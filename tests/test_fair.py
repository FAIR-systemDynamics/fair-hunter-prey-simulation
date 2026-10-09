# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_original_artifacts_are_unchanged():
    manifest = json.loads((ROOT / "tests/fair-preservation.json").read_text())
    for name, digest in manifest["sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name


def test_stella_snapshot_is_unchanged():
    manifest = json.loads((ROOT / "docs/fair/stella-sources.json").read_text())
    for name, digest in manifest["sha256"].items():
        assert hashlib.sha256((ROOT / manifest["bundle"] / name).read_bytes()).hexdigest() == digest, name


def test_run_requires_explicit_valid_choices(tmp_path):
    from fair_hunter_prey import run_example
    with pytest.raises(ValueError):
        run_example("automatic", "case1", tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_output_cannot_replace_existing_data(tmp_path):
    from fair_hunter_prey import run_example
    protected = tmp_path / "keep.csv"
    protected.write_text("existing data")
    with pytest.raises(FileExistsError):
        run_example("vensim", "case1", tmp_path)
    assert protected.read_text() == "existing data"


def test_inspection_preserves_export_shapes(tmp_path):
    from fair_hunter_prey import inspect_results
    import pandas as pd
    result = inspect_results(tmp_path / "inspection")
    trajectories = pd.read_csv(result["trajectories"])
    assert len(trajectories.query("implementation == 'vensim' and case == 'case1' and variable == 'Deer Population'")) == 1001
    assert len(trajectories.query("implementation == 'vensim' and case == 'case1' and variable == 'Historical Deer BOT'")) == 21
    assert trajectories.query("implementation == 'stella' and case == 'case2'").empty
    final = pd.read_csv(result["final_values"])
    assert set(final.case) == {"case2"}
    assert final.unit.isna().all()
    assert not json.loads(result["provenance"].read_text())["simulation_executed"]


@pytest.mark.parametrize("implementation", ["vensim", "stella"])
@pytest.mark.parametrize("case", ["case1", "case2"])
def test_packaged_execution_matches_reference(implementation, case, tmp_path):
    from fair_hunter_prey import run_example
    from fair_hunter_prey.workflows import _reader, _root, STOCKS
    result = run_example(implementation, case, tmp_path / "run")
    manifest = json.loads(result["provenance"].read_text())
    assert manifest["engine"] == "PySD"
    assert manifest["outputs"]["simulation.csv"] == hashlib.sha256(result["csv"].read_bytes()).hexdigest()
    if implementation == "vensim":
        reader = _reader("vensim_csv")
        actual, _ = reader.read_dataset(result["csv"])
        reference, _ = reader.read_dataset(_root() / f"results/reference/{case}.csv")
        assert len(actual[STOCKS[0]]) == 51
        tolerance = json.loads((_root() / "results/reference/tolerances.json").read_text())[case]["relative_tolerance"]
        for stock in STOCKS:
            times = actual[stock].index.intersection(reference[stock].index)
            deviation = (actual[stock].loc[times] - reference[stock].loc[times]).abs() / reference[stock].loc[times].abs().clip(lower=1e-6)
            assert deviation.max() <= tolerance
    else:
        reader = _reader("stella_csv")
        times, actual, _ = reader.read_results(result["csv"])
        ref_times, reference, _ = reader.read_results(_root() / f"examples/stella-source/results/kaibab_ecosystem_results_stella_scenario{case[-1]}.csv")
        if ref_times:
            assert times == pytest.approx(ref_times)
        for stock in STOCKS:
            pairs = zip(actual[stock], reference[stock], strict=True) if ref_times else [(actual[stock][-1], reference[stock][0])]
            assert max(abs(a-b) / max(abs(b), 1e-12) for a,b in pairs) < 1e-9


@pytest.mark.parametrize("implementation", ["vensim", "stella"])
@pytest.mark.parametrize("case", ["case1", "case2"])
def test_crate_records_and_reproduces_an_actual_run(implementation, case, tmp_path):
    from fair_hunter_prey import run_example, create_crate
    import subprocess
    import sys
    run = run_example(implementation, case, tmp_path / 'run')
    crate = create_crate(tmp_path / 'run', tmp_path / 'crate')
    metadata = json.loads((crate / 'ro-crate-metadata.json').read_text())
    entities = metadata['@graph']
    action = next(e for e in entities if e['@id'] == '#execution')
    assert action['@type'] == 'CreateAction'
    assert action['result']['@id'] == 'execution/simulation.csv'
    hashes = [e for e in entities if 'sha256' in e]
    assert len(hashes) > 15
    for entity in hashes:
        assert hashlib.sha256((crate / entity['@id']).read_bytes()).hexdigest() == entity['sha256']
    subprocess.run([sys.executable, str(crate / 'reproduce.py')], cwd=tmp_path, check=True, capture_output=True)
    assert (crate / 'reproduced/simulation.csv').read_bytes() == run['csv'].read_bytes()
    run['csv'].write_text('changed after execution')
    with pytest.raises(ValueError, match='Run output changed'):
        create_crate(tmp_path / 'run', tmp_path / 'invalid-crate')
    assert not (tmp_path / 'invalid-crate').exists()
