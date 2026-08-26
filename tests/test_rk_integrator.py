# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Verify the Runge-Kutta wrapper against a model with a known exact solution.

`fixtures/expgrowth.mdl` is `Stock = INTEG(r*Stock, 1)` with `r = 0.5`, whose
solution is `exp(r*t)`. Halving the time step must reduce the error by roughly
2 for a first-order method, 4 for second order and 16 for fourth order.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runners" / "pysd"))

pysd = pytest.importorskip("pysd")
from rk_integrator import TABLEAUX, attach  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "expgrowth.mdl"
R, T_END = 0.5, 10.0
EXACT = math.exp(R * T_END)

# method -> expected error reduction when the step size is halved
EXPECTED_ORDER = {"euler": 2, "rk2-midpoint": 4, "rk2-heun": 4, "rk4": 16}


@pytest.fixture(scope="module")
def compiled(tmp_path_factory):
    """Translate the fixture once into a temporary directory."""
    workdir = tmp_path_factory.mktemp("rk")
    mdl = workdir / FIXTURE.name
    mdl.write_text(FIXTURE.read_text())
    pysd.read_vensim(str(mdl))
    return mdl.with_suffix(".py")


def final_error(compiled, method: str, dt: float) -> float:
    model = attach(pysd.load(str(compiled)), method)
    value = model.run(time_step=dt, saveper=T_END)["Stock"].iloc[-1]
    return abs(value - EXACT) / EXACT


@pytest.mark.parametrize("method", sorted(EXPECTED_ORDER))
def test_convergence_order(compiled, method):
    """Halving dt must reduce the error by the method's order factor."""
    expected = EXPECTED_ORDER[method]
    coarse = final_error(compiled, method, 0.25)
    fine = final_error(compiled, method, 0.125)
    ratio = coarse / fine
    # generous band: the asymptotic rate is only approached, not hit exactly
    assert 0.7 * expected < ratio < 1.4 * expected, (
        f"{method}: error ratio {ratio:.2f}, expected about {expected}"
    )


def test_rk4_beats_euler_by_orders_of_magnitude(compiled):
    assert final_error(compiled, "rk4", 0.25) < final_error(compiled, "euler", 0.25) / 1000


def test_unknown_method_is_rejected(compiled):
    with pytest.raises(ValueError, match="unknown integration method"):
        attach(pysd.load(str(compiled)), "rk3-not-a-thing")


def test_aliases_resolve(compiled):
    model = attach(pysd.load(str(compiled)), "RK2")
    assert model._integration_method == "rk2-midpoint"


def test_every_tableau_is_consistent():
    """Sum of the b weights must be 1, and each row of A must match its c."""
    for name, (c, a_rows, b) in TABLEAUX.items():
        assert math.isclose(sum(b), 1.0), f"{name}: weights do not sum to 1"
        for c_i, row in zip(c, a_rows):
            assert math.isclose(sum(row), c_i, abs_tol=1e-12), (
                f"{name}: stage offset {c_i} does not match its coefficients"
            )
