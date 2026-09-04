# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Runge-Kutta integration for PySD models.

PySD integrates with fixed-step Euler only: :meth:`Model._integrate_step` calls
:meth:`Model._euler_step`, and there is no switch for anything else. Vensim and
Stella offer RK2 and RK4, and a model simulated under RK2 is not the same model
under Euler. This module supplies the missing methods.

It works by replacing ``_integrate_step`` on a model *instance*. The rest of
PySD is untouched::

    import pysd
    from rk_integrator import attach

    model = pysd.read_vensim("model.mdl")
    attach(model, "rk4")
    result = model.run()

``rk2-midpoint``, ``rk2-heun``, ``rk4``, and ``euler`` are provided.

Which RK2?
----------
"RK2" is not one method. The midpoint rule and Heun's method are both
second-order and give different numbers. Vensim and Stella do not use the same
formulation, and neither states which one in the user interface. If
comparing runs across tools, verify which variant each tool implements before
concluding that a discrepancy is a modelling error.
:func:`compare_methods` is there for exactly that check.
"""

from __future__ import annotations

import warnings
from types import MethodType

# Butcher tableaux: (c, A, b)
#   c -- the time offset of each stage, as a fraction of dt
#   A -- how each stage's trial state is built from earlier stages
#   b -- the weights combining the stages into the final increment
TABLEAUX: dict[str, tuple[tuple[float, ...], tuple[tuple[float, ...], ...], tuple[float, ...]]] = {
    "euler": (
        (0.0,),
        ((),),
        (1.0,),
    ),
    "rk2-midpoint": (
        (0.0, 0.5),
        ((), (0.5,)),
        (0.0, 1.0),
    ),
    "rk2-heun": (
        (0.0, 1.0),
        ((), (1.0,)),
        (0.5, 0.5),
    ),
    "rk4": (
        (0.0, 0.5, 0.5, 1.0),
        ((), (0.5,), (0.0, 0.5), (0.0, 0.0, 1.0)),
        (1 / 6, 1 / 3, 1 / 3, 1 / 6),
    ),
}

# Accepted spellings, so "RK2" and "rk4 " do not fail on formatting.
ALIASES = {
    "rk2": "rk2-midpoint",
    "midpoint": "rk2-midpoint",
    "heun": "rk2-heun",
    "rk2_heun": "rk2-heun",
    "rk2_midpoint": "rk2-midpoint",
}


def _resolve(method: str) -> str:
    key = method.strip().lower().replace(" ", "-")
    key = ALIASES.get(key.replace("-", "_"), ALIASES.get(key, key))
    if key not in TABLEAUX:
        raise ValueError(
            f"unknown integration method {method!r}; "
            f"available: {', '.join(sorted(TABLEAUX))}"
        )
    return key


def _make_step(tableau):
    """Build an ``_integrate_step`` replacement for the given Butcher tableau."""
    c, a_rows, b = tableau

    def _integrate_step(self):
        dt = self.time.time_step()
        t0 = self.time()
        y0 = self.state

        stages = []
        for stage, (c_i, a_row) in enumerate(zip(c, a_rows)):
            if stage:
                trial = y0
                for coeff, k in zip(a_row, stages):
                    if coeff:
                        trial = trial + (dt * coeff) * k
                self.state = trial
                self.time.update(t0 + c_i * dt)
                # the model may read Time directly, and cached values are stale
                # once state or time changed
                self.clean_caches()
            stages.append(self.ddt())

        increment = None
        for weight, k in zip(b, stages):
            if not weight:
                continue
            term = (dt * weight) * k
            increment = term if increment is None else increment + term

        self.state = y0 if increment is None else y0 + increment
        self.time.update(t0 + dt)
        self.clean_caches()

    return _integrate_step


def attach(model, method: str = "rk4"):
    """Give ``model`` a Runge-Kutta integrator. Returns the model.

    Parameters
    ----------
    model
        A model from :func:`pysd.read_vensim`, :func:`pysd.read_xmile` or
        :func:`pysd.load`.
    method
        ``euler``, ``rk2-midpoint`` (alias ``rk2``), ``rk2-heun`` or ``rk4``.
    """
    key = _resolve(method)

    elements = getattr(model, "_dynamicstateful_elements", None)
    if not elements:
        raise ValueError(
            "the model has no dynamic stateful elements -- nothing to integrate"
        )
    unknown = [
        type(e).__name__
        for e in elements
        if type(e).__name__ not in ("Integ", "Delay", "DelayFixed", "Smooth",
                                    "Trend", "DelayN", "SmoothN")
    ]
    if unknown:
        warnings.warn(
            f"model contains stateful elements that may not be differential: "
            f"{', '.join(sorted(set(unknown)))}. Runge-Kutta evaluates the "
            f"model at fractional time steps, which is not meaningful for "
            f"discrete constructs. Check the result against Euler.",
            stacklevel=2,
        )

    model._integrate_step = MethodType(_make_step(TABLEAUX[key]), model)
    model._integration_method = key
    return model


def compare_methods(model_file, methods=("euler", "rk2-midpoint", "rk2-heun", "rk4"),
                    reference_dt=None, **run_kwargs):
    """Run one model under several integrators and report the spread.

    ``reference_dt`` runs an extra Euler pass at a much smaller step to serve as
    a stand-in for the exact solution. Returns a :class:`pandas.DataFrame`
    indexed by time with one column per method and variable.

    This is a diagnostic, not a test: it tells how much the integrator
    choice moves the trajectory of *this* model, which is what decides whether
    a cross-tool difference is worth investigating.
    """
    import pandas as pd
    import pysd
    from pathlib import Path

    # Translate once; re-translating per method dominates the runtime.
    pysd.read_vensim(str(model_file))
    compiled = Path(model_file).with_suffix(".py")

    frames = {}
    for method in methods:
        model = attach(pysd.load(str(compiled)), method)
        frames[method] = model.run(**run_kwargs)

    if reference_dt is not None:
        model = attach(pysd.load(str(compiled)), "rk4")
        kwargs = dict(run_kwargs)
        kwargs["time_step"] = reference_dt
        kwargs.setdefault("saveper", model.time.time_step())
        frames["reference"] = model.run(**kwargs)

    return pd.concat(frames, axis=1)
