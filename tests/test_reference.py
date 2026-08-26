# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Check PySD runs against the committed reference results.

This is what makes `results/reference/` important: if the model, the parameters or
the runner change in a way that changes the numbers, this fails and names the
variable and the year.

Each scenario is simulated from its own `.cin` in `models/config/scenarios/`, so the
test exercises the same scenario definition Vensim uses.

The model is loaded through `runners/pysd/run.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "results" / "reference"
SCENARIOS = ROOT / "models" / "config" / "scenarios"
sys.path.insert(0, str(ROOT / "runners" / "pysd"))
sys.path.insert(0, str(ROOT / "scripts"))

pysd = pytest.importorskip("pysd")
pd = pytest.importorskip("pandas")
from rk_integrator import attach  # noqa: E402
from run import collect, expand, match_to_model, prepare  # noqa: E402
from vensim_csv import read_dataset, time_bases  # noqa: E402

TOLERANCES = json.loads((REFERENCE / "tolerances.json").read_text())
FLOOR = TOLERANCES["absolute_floor"]

# Vensim's "RK2" is the midpoint rule, not Heun
METHOD = "rk2-midpoint"
TIME_STEP = 1 / 20

# case1 is the baseline: no overrides. case2 is defined by a changes file.
CASES = {"case1": None, "case2": "case2.cin"}


def find_model() -> Path | None:
    candidates = sorted((ROOT / "models").glob("*.mdl"))
    return candidates[0] if candidates else None


# Everything the externalised model needs
BASE_INPUTS = [
    ROOT / "models" / "config" / "parameters",
    ROOT / "models" / "config" / "lookups",
    ROOT / "models" / "config" / "timeseries",
]


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    """Model and base inputs, loaded exactly the way the runner loads them."""
    model = find_model()
    if model is None:
        pytest.skip(
            "no .mdl in models/: the model is not committed yet, so there "
            "is nothing to compare against the reference"
        )
    workdir = tmp_path_factory.mktemp("reference")
    inputs = [path for path in BASE_INPUTS if path.exists()]
    params, workbooks, _ = collect(expand(inputs))
    compiled, _, stubs = prepare(model, workbooks, workdir)

    unsupplied = [name for name in stubs if name not in params]
    assert not unsupplied, (
        f"the model has placeholder lookups that nothing supplies: "
        f"{', '.join(unsupplied)}. The run would silently produce wrong numbers."
    )
    return compiled, params


def load_reference(case: str) -> dict:
    """Reference results as ``{variable: Series}``, each on its own time base.

    A Vensim export that contains a data variable, e.g, a reference mode, imported
    data, carries more than one time axis.
    """
    series, _ = read_dataset(REFERENCE / f"{case}.csv")
    return series


def test_reference_files_are_consistent():
    """Both cases hold the same variables on the same time bases."""
    case1, case2 = load_reference("case1"), load_reference("case2")
    assert sorted(case1) == sorted(case2), "the two cases record different variables"
    for name in case1:
        assert list(case1[name].index) == list(case2[name].index), (
            f"{name}: the two cases put it on different time bases"
        )
    spans = {name: (float(s.index.min()), float(s.index.max()))
             for name, s in case1.items()}
    assert len(set(spans.values())) == 1, (
        f"variables do not cover the same period: {spans}"
    )


def test_historical_series_is_scenario_independent():
    """The reference mode must not differ between scenarios."""
    case1, case2 = load_reference("case1"), load_reference("case2")
    column = "Historical Deer BOT"
    if column not in case1:
        pytest.skip(f"{column} is not in the reference export")
    assert case1[column].equals(case2[column])


def test_data_variable_keeps_its_own_time_base():
    """Guard against the multi-axis export being read onto a single axis.

    Vensim writes a fresh 'Time' header for every time base in a run. Read
    naively, the coarse series lands on the fine grid: a 1910 value would be
    reported at 1900.2. If that ever happens again, this fails.
    """
    reference = load_reference("case1")
    column = "Historical Deer BOT"
    if column not in reference:
        pytest.skip(f"{column} is not in the reference export")
    series = reference[column]
    assert float(series.index.max()) > 1940, (
        f"{column} ends at {series.index.max()}: it has been written to the "
        f"wrong time axis: it should span the whole simulated period"
    )


def test_every_case_has_a_tolerance():
    """A reference file without a stated tolerance cannot be checked."""
    for case in CASES:
        assert case in TOLERANCES, f"no tolerance recorded for {case}"
        assert "rationale" in TOLERANCES[case], (
            f"{case}: a tolerance without a rationale is a guess"
        )


def test_scenario_files_exist():
    """Every scenario that is not the baseline must be recorded as a .cin."""
    missing = [
        name for case, name in CASES.items()
        if name is not None and not (SCENARIOS / name).exists()
    ]
    assert not missing, (
        f"scenario definition(s) missing from models/config/scenarios/: "
        f"{', '.join(missing)}. Without them the run is not reproducible."
    )


@pytest.mark.parametrize("case", sorted(CASES))
def test_matches_reference(prepared, case):
    """A PySD replay of the scenario must reproduce the committed results."""
    compiled, base_params = prepared
    reference = load_reference(case)
    columns = [c for c in reference if c != "Historical Deer BOT"]
    tolerance = TOLERANCES[case]["relative_tolerance"]

    params = dict(base_params)
    scenario_names: set[str] = set()
    scenario = CASES[case]
    if scenario:
        overrides, _, _ = collect(expand([SCENARIOS / scenario]))
        scenario_names = set(overrides)
        params.update(overrides)

    model = attach(pysd.load(str(compiled)), METHOD)
    # The same config serves several model versions, so a base parameter may
    # legitimately have no variable to bind to. A *scenario* parameter that does
    # not bind is a different matter: the scenario would not be applied at all.
    params, unknown = match_to_model(model, params)
    unapplied = sorted(set(unknown) & set(scenario_names))
    assert not unapplied, (
        f"{case}: scenario parameter(s) not present in the model: "
        f"{', '.join(unapplied)}. The run would not be the scenario."
    )
    result = model.run(params=params, return_columns=columns,
                       time_step=TIME_STEP, saveper=1.0)

    failures = []
    for column in columns:
        if column not in reference:
            continue
        expected = reference[column]
        # compare where both actually have a value, the reference may be on a
        # finer grid than the run was asked to save
        shared = [t for t in expected.index if t in result.index]
        assert shared, f"{column}: no common time points with the reference"
        deviation = ((result.loc[shared, column] - expected.loc[shared]).abs()
                     / expected.loc[shared].abs().clip(lower=FLOOR))
        worst = deviation.max()
        if worst > tolerance:
            year = deviation.idxmax()
            failures.append(
                f"{column}: {worst:.4%} at {year:g} "
                f"(reference {expected[year]:.6g}, PySD {result.loc[year, column]:.6g})"
            )

    assert not failures, (
        f"{case}: PySD deviates from results/reference/{case}.csv beyond "
        f"{tolerance:.1%}:\n  " + "\n  ".join(failures)
    )
