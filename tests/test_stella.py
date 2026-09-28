# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Run Stella models with PySD, and check them against Stella itself.

Two layers:

* ``fixtures/stella_minimal.stmx`` is small enough to reason about by hand and
  carries one of each thing the runner has to get right: Stella's ``//``, a
  graphical function, a ``STEP``, a uniflow and ``method="RK2"``. These tests
  run on every branch.
* The Kaibab model is checked against Stella's own export,
  ``results/kaibab_ecosystem_results_stella_scenario{1,2}.csv``, driven by the
  parameter files Stella imported. Those files live on the ``stella`` branch,
  so elsewhere these tests are skipped. Agreement to 1e-9 means the PySD run
  *is* the Stella run. Stella is commercial, and without this nobody without
  a licence can check the Stella results.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners" / "pysd"))
sys.path.insert(0, str(ROOT / "scripts"))

pysd = pytest.importorskip("pysd")
pytest.importorskip("lxml")

import run  # noqa: E402
import stella_csv  # noqa: E402
import xmile_support  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "stella_minimal.stmx"

KAIBAB = ROOT / "models" / "kaibab_ecosystem_model.stmx"
PARAMETERS = ROOT / "models" / "config" / "parameters"
RESULTS = ROOT / "results"
STOCKS = ("Deer Population", "Forage Biomass", "Predator Population")

needs_kaibab = pytest.mark.skipif(
    not (KAIBAB.exists()
         and (RESULTS / "kaibab_ecosystem_results_stella_scenario1.csv").exists()),
    reason="the Stella model and its export live on the stella branch",
)

#: Stella's export carries 12 significant digits, so this is its rounding
#: floor with room to spare, and far below any integrator difference.
TOLERANCE = 1e-9


def _run(tmp_path, model, *extra, name="run.csv"):
    target = tmp_path / name
    assert run.main([str(model), *extra, "--layout", "stella",
                     "-o", str(target)]) == 0
    times, series, _ = stella_csv.read_results(target)
    return times, series


# ---------------------------------------------------------------------------
# The mechanics, on the fixture

def test_declared_method_and_step_variables():
    facts = xmile_support.ModelFacts(FIXTURE)
    assert facts.method == "RK2"
    assert facts.integration_method() == "rk2-heun"
    assert facts.step_variables == ["Harvest"]
    assert facts.stocks == {"biomass"}
    assert facts.graphical == {"growth fraction"}


@pytest.mark.parametrize(
    "method,vendor,expected",
    [("RK2", "isee systems, inc.", "rk2-heun"),
     ("RK2", "Ventana Systems", "rk2-midpoint"),
     ("Euler", "", "euler"),
     ("gear, rk4", "", "rk4"),
     ("", "", None)],
)
def test_integration_method(method, vendor, expected):
    facts = xmile_support.ModelFacts(FIXTURE)
    facts.method, facts.vendor = method, vendor
    assert facts.integration_method() == expected


def test_runs_with_the_declared_method(tmp_path):
    times, series = _run(tmp_path, FIXTURE)
    assert times[:3] == [0.0, 0.5, 1.0]
    assert series["Biomass"][0] == 100


def test_step_is_held_for_the_whole_step(tmp_path):
    """Without holding, Heun's last stage of the step ending at the STEP time
    already sees it switched on and removes 0.5 * dt * 1 = 0.25 too early."""
    folder = tmp_path / "copy"
    folder.mkdir()
    compiled, _, _ = run.prepare_xmile(FIXTURE, folder)
    plain = run.attach(pysd.load(str(compiled)), "rk2-heun").run()
    model = pysd.load(str(compiled))
    held = run.attach(model, "rk2-heun",
                      hold=run.held_components(model, ["Harvest"])).run()
    difference = held.loc[1.0, "Biomass"] - plain.loc[1.0, "Biomass"]
    assert difference == pytest.approx(0.25)


def test_holding_changes_nothing_under_euler(tmp_path):
    folder = tmp_path / "copy"
    folder.mkdir()
    compiled, _, _ = run.prepare_xmile(FIXTURE, folder)
    plain = run.attach(pysd.load(str(compiled)), "euler").run()
    model = pysd.load(str(compiled))
    held = run.attach(model, "euler",
                      hold=run.held_components(model, ["Harvest"])).run()
    assert (plain["Biomass"] == held["Biomass"]).all()


def test_a_stock_value_sets_its_initial_value(tmp_path):
    """As Stella's import does, rather than freezing the stock."""
    parameters = tmp_path / "p.csv"
    parameters.write_text("Biomass;200\n", encoding="utf-8")
    _, series = _run(tmp_path, FIXTURE, "-d", str(parameters))
    assert series["Biomass"][0] == 200
    assert series["Biomass"][-1] != 200


def test_a_table_replaces_the_graphical_function(tmp_path):
    """A table in the input is the table the run uses, not a time series."""
    parameters = tmp_path / "p.csv"
    parameters.write_text(
        '="Growth Fraction:x";0;2\n="Growth Fraction:y";0;0\n',
        encoding="utf-8",
    )
    _, series = _run(tmp_path, FIXTURE, "-d", str(parameters))
    # No growth and a harvest from t = 1: the stock can only fall.
    biomass = series["Biomass"]
    assert all(b <= a + 1e-12 for a, b in zip(biomass, biomass[1:]))
    assert biomass[-1] < biomass[0]


def test_the_model_file_is_never_touched(tmp_path):
    before = FIXTURE.read_bytes()
    _run(tmp_path, FIXTURE)
    assert FIXTURE.read_bytes() == before


@pytest.mark.parametrize(
    "equation,expected",
    [
        ("a//b", "SAFEDIV(a, b)"),
        ("a*b//c", "SAFEDIV(a * b, c)"),
        ("a//b*c", "SAFEDIV(a, b) * c"),
        ("a MOD b", "a mod b"),
        ("IF a THEN b ELSE IF c THEN d ELSE e",
         "(IF a THEN b ELSE (IF c THEN d ELSE e))"),
        ("x + IF a THEN IF b THEN 1 ELSE 2 ELSE 3",
         "x + (IF a THEN (IF b THEN 1 ELSE 2) ELSE 3)"),
        ("a*b {note}", "a*b"),
        ("a + b", "a + b"),
    ],
)
def test_equation_rewrites(equation, expected):
    assert xmile_support.rewrite_equation(equation) == expected


class TestStellaTables:
    def test_parameters_with_decimal_commas_and_tables(self, tmp_path):
        path = tmp_path / "p.csv"
        path.write_text(
            "Baseline Biomass Growth Fraction;0,1\n"
            "Initial Deer Population;4000\n"
            '="Table:x";0;0,5;1\n'
            '="Table:y";1;2,5;3\n',
            encoding="utf-8",
        )
        values = stella_csv.read_parameters(path)
        assert values["Baseline Biomass Growth Fraction"] == 0.1
        assert values["Initial Deer Population"] == 4000
        assert list(values["Table"].index) == [0, 0.5, 1]
        assert list(values["Table"].values) == [1, 2.5, 3]

    def test_results_round_trip(self, tmp_path):
        import pandas as pd

        frame = pd.DataFrame({"Stock": [1.5, 2.25]}, index=[1900.0, 1900.05])
        target = tmp_path / "r.csv"
        stella_csv.write_results(frame, target, "Years", decimal_comma=True)
        assert target.read_text().splitlines()[0] == "Years;1900;1900,05"
        times, series, unit = stella_csv.read_results(target)
        assert (times, series["Stock"], unit) == ([1900.0, 1900.05], [1.5, 2.25], "Years")

    def test_a_table_without_its_x_row_is_refused(self, tmp_path):
        path = tmp_path / "p.csv"
        path.write_text('="Table:y";1;2\nA;1\n', encoding="utf-8")
        with pytest.raises(stella_csv.NotAStellaTable):
            stella_csv.read_parameters(path)


# ---------------------------------------------------------------------------
# The Kaibab model against Stella's own export

@needs_kaibab
@pytest.mark.parametrize("scenario", [1, 2])
def test_reproduces_stella(tmp_path, scenario):
    parameters = PARAMETERS / f"kaibab_ecosystem_parameters_stella_scenario{scenario}.csv"
    times, ours = _run(tmp_path, KAIBAB, "-d", str(parameters))
    ref_times, reference, _ = stella_csv.read_results(
        RESULTS / f"kaibab_ecosystem_results_stella_scenario{scenario}.csv"
    )
    assert times == pytest.approx(ref_times)
    for name in STOCKS:
        worst = max(
            abs(a - b) / max(abs(a), 1e-12)
            for a, b in zip(reference[name], ours[name], strict=True)
        )
        assert worst < TOLERANCE, name


@needs_kaibab
def test_without_holding_step_the_scenario_misses(tmp_path):
    """The reason STEP is held: re-evaluated per stage, the predator-removal
    scenario ends far from Stella's run."""
    folder = tmp_path / "copy"
    folder.mkdir()
    compiled, _, _ = run.prepare_xmile(KAIBAB, folder)
    frame = run.attach(pysd.load(str(compiled)), "rk2-heun").run(params={
        "Baseline Annual Kills Per Predator": 20,
        "Deer Carrying Capacity in Years": 4,
        "Desired Consumption per Deer": 0.5,
        "Fraction Predators Killed per Year": 0.2,
    })
    _, reference, _ = stella_csv.read_results(
        RESULTS / "kaibab_ecosystem_results_stella_scenario2.csv"
    )
    final = frame["Deer Population"].iloc[-1]
    assert abs(final - reference["Deer Population"][-1]) / final > 0.1


@needs_kaibab
def test_the_committed_parameter_file_reads():
    values = stella_csv.read_parameters(
        PARAMETERS / "kaibab_ecosystem_parameters_stella_scenario2.csv"
    )
    assert values["Fraction Predators Killed per Year"] == 0.2
    assert len(values["Historical Deer Behavior Over Time"]) == 21
