#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Run a Vensim or Stella model with PySD, with or without externalised data.

One script for both stages of the model. A model that carries its own numbers
needs no arguments beyond itself::

    python runners/pysd/run.py models/kaibab_ecosystem.mdl -o results/runs/case1.csv

A model whose parameters, lookups and time series live outside it takes them as
inputs, in any number and any order::

    python runners/pysd/run.py models/kaibab_ecosystem.mdl \\
        -d models/config/parameters/basic_parameters.cin \\
        -d models/config/lookups/ \\
        -d models/config/timeseries/historical_deer_botg.csv \\
        -d models/config/scenarios/case2.cin \\
        -o results/runs/case2.csv

A workbook the model reads itself needs no ``-d``: the model names it relative
to its own location, and the runner reproduces that path inside its work
directory. Pass a workbook only when it lives somewhere the model cannot name.

Each ``-d`` is dispatched by what it is, not by a separate flag:

===========  ====================================================================
``.cin``     constants as floats, lookups as x-indexed series
``.csv``     ``variable,value`` rows become constants, a table with time in the
             header row or the first column becomes a time series
``.xlsx``    not read here, since the *model* reads it via ``GET XLS CONSTANTS``. The
             file is placed next to the model copy so the reference resolves.
directory    every supported file inside it
===========  ====================================================================

Inputs are applied in the order given, so a scenario listed after the base
parameters overrides them. That is the same precedence Vensim gives a stack of
changes files.

Adapting the model
------------------
PySD rejects two constructs that Vensim accepts. Rather than requiring the model
to avoid them, this runner patches a **copy** in a temporary directory and says
so on stderr. The file in ``models/`` is never touched, and both tools keep
reading the same source:

* an equation with no right-hand side (a ``:SUPPLEMENTARY`` data variable) --
  given ``= 0``, then overridden by whatever time series you pass in;
* Vensim's indirect file reference ``'?book.xlsx'`` the ``?`` is dropped.

Stella models
-------------
A ``.stmx`` runs the same way, and is run as Stella runs it::

    python runners/pysd/run.py models/kaibab_ecosystem_model.stmx \\
        -d models/config/parameters/kaibab_ecosystem_parameters_stella_scenario2.csv \\
        -d models/config/lookups/kaibab_ecosystem_lookups_stella.csv \\
        -d models/config/timeseries/kaibab_ecosystem_historic_BOT_stella.csv \\
        --layout stella -o results/runs/stella_scenario2_pysd.csv

* the integration method is the one the file declares, and Stella's RK2 is
  Heun's method, not the midpoint rule Vensim uses;
* ``STEP`` is evaluated once per time step and held through its stages;
* Stella's tables are read as Stella writes them: no header row, ``,`` and
  ``.`` or, from a German Stella, ``;`` and decimal commas, graphical
  functions as ``="Name:x"`` and ``="Name:y"`` rows. A value given for a
  stock sets its initial value, as Stella's import does;
* equations Stella writes and PySD rejects (``a // b``, nested ``IF``,
  ``MOD``, ``{comments}``) are rewritten in the copy.

See :mod:`xmile_support` for the measurements behind each of these.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from cin_loader import CinError, read_cin  # noqa: E402
from vensim_csv import NotATimeSeries, read_dataset  # noqa: E402
from rk_integrator import TABLEAUX, attach  # noqa: E402
import stella_csv  # noqa: E402
import xmile_support  # noqa: E402

DATA_SUFFIXES = {".cin", ".csv", ".xlsx", ".xls"}
TIME_COLUMN_NAMES = {"time", "year", "t"}


class RunError(Exception):
    """Raised for input the caller has to fix; reported without a traceback."""


def is_number(text) -> bool:
    try:
        float(text)
    except (TypeError, ValueError):
        return False
    return True


def expand(paths) -> list[Path]:
    """Turn the -d arguments into a flat, ordered list of files."""
    files: list[Path] = []
    for entry in paths:
        path = Path(entry)
        if path.is_dir():
            found = sorted(
                child for child in path.iterdir()
                if child.suffix.lower() in DATA_SUFFIXES
            )
            if not found:
                raise RunError(f"{path} holds no .cin, .csv or .xlsx file")
            files.extend(found)
        elif path.is_file():
            if path.suffix.lower() not in DATA_SUFFIXES:
                raise RunError(
                    f"{path}: cannot tell what to do with a {path.suffix} file. "
                    f"Supported: {', '.join(sorted(DATA_SUFFIXES))}"
                )
            files.append(path)
        else:
            raise RunError(f"input not found: {path}")
    return files


def load_csv(path: Path) -> dict:
    """Read a CSV as either constants or time series, whichever it is.

    Time series go through :mod:`vensim_csv`, so a Vensim export keeps every
    variable on the time base it was recorded on -- a run containing lookup data
    or a reference mode has more than one.
    """
    import pandas as pd

    if stella_csv.is_stella_table(path):
        return _load_stella_table(path)

    try:
        series, _ = read_dataset(path)
        return series
    except NotATimeSeries:
        pass                      # fall through: probably variable/value rows
    except FileNotFoundError:
        raise RunError(f"input not found: {path}") from None

    raw = pd.read_csv(path)
    if raw.shape[1] < 2:
        raise RunError(f"{path}: needs at least two columns")

    headers = list(raw.columns)
    values: dict = {}
    for _, row in raw.iterrows():
        name = str(row[headers[0]]).strip()
        cell = row[headers[1]]
        if not name or str(cell).strip() == "":
            continue
        try:
            values[name] = float(cell)
        except (TypeError, ValueError):
            raise RunError(
                f"{path}: {name!r} has the non-numeric value {cell!r}. If this "
                f"file is a time series, its first column should be named "
                f"'time' or 'year'."
            ) from None
    if not values:
        raise RunError(f"{path}: no usable rows")
    return values


def _load_stella_table(path: Path) -> dict:
    """A Stella parameter file, or a Stella export as time series."""
    import pandas as pd

    try:
        return stella_csv.read_parameters(path)
    except stella_csv.NotAStellaTable as parameters_error:
        try:
            times, series, _ = stella_csv.read_results(path)
        except (stella_csv.NotAStellaTable, ValueError):
            raise RunError(str(parameters_error)) from None
        if not times:
            raise RunError(
                f"{path}: an export of final values only, which is a result "
                f"to compare with, not an input to a run"
            )
        return {
            name: pd.Series(values, index=times[: len(values)])
            for name, values in series.items()
        }


def collect(files: list[Path]) -> tuple[dict, list[Path], list[str]]:
    """Read every input. Returns (params, workbooks, a log of what was read)."""
    params: dict = {}
    workbooks: list[Path] = []
    log: list[str] = []

    for path in files:
        suffix = path.suffix.lower()
        if suffix in (".xlsx", ".xls"):
            workbooks.append(path)
            log.append(f"{path.name}: workbook, made available to the model")
            continue

        try:
            found = read_cin(path) if suffix == ".cin" else load_csv(path)
        except CinError as error:
            raise RunError(str(error)) from None

        overridden = sorted(set(found) & set(params))
        params.update(found)
        note = f", overriding {', '.join(overridden)}" if overridden else ""
        log.append(f"{path.name}: {len(found)} variable(s){note}")

    return params, workbooks, log


# Files the model reads itself, e.g. GET XLS CONSTANTS('config/parameters/x.xlsx', …)
_FILE_REF = re.compile(r"GET\s+(?:XLS|DIRECT)\s+[A-Z]+\s*\(\s*'([^']+)'", re.I)

# A lookup written with two points or fewer is a placeholder, not a table.
_LOOKUP_DEF = re.compile(
    r"^(?P<name>[A-Za-z\"][^=~|(\n]*?)\s*\(\s*\[[^\]]*\]\s*,(?P<points>[^)]*(?:\)[^)]*)*?)\)\s*$",
    re.M | re.S,
)


def find_stub_lookups(text: str) -> list[str]:
    """Names of lookups defined with two points or fewer, i.e. placeholders."""
    stubs = []
    for match in _LOOKUP_DEF.finditer(text):
        pairs = re.findall(r"\(\s*-?[\d.eE+-]+\s*,\s*-?[\d.eE+-]+\s*\)", match["points"])
        if 0 < len(pairs) <= 2:
            stubs.append(match["name"].strip().strip('"'))
    return stubs


def prepare_xmile(model: Path, workdir: Path, tables: dict | None = None,
                  ) -> tuple[Path, list[str], list[str]]:
    """Copy a Stella model into workdir, rewrite what PySD rejects, translate.

    ``tables`` are graphical functions supplied by an input, as
    ``{name: (xs, ys)}``; they are written into the copy.
    """
    import pysd

    text, notes = xmile_support.prepare_text(model, tables)
    suffix = (model.suffix.lower()
              if model.suffix.lower() in xmile_support.PYSD_SUFFIXES else ".xmile")
    copy = workdir / (model.stem + suffix)
    copy.write_text(text, encoding="utf-8")
    patches = [f"rewrote {note}" for note in notes]
    try:
        pysd.read_xmile(str(copy))
    except Exception as error:
        raise RunError(
            f"PySD could not translate {model.name}: {type(error).__name__}: "
            f"{str(error)[:300]}"
        ) from None
    return copy.with_suffix(".py"), patches, []


def split_tables(params: dict, graphical: set) -> tuple[dict, dict]:
    """Take the tables given for Stella graphical functions out of ``params``.

    They are written into the model copy instead, see :func:`prepare_xmile`.
    """
    rest, tables = {}, {}
    for name, value in params.items():
        if xmile_support.canonical(name) in graphical and hasattr(value, "index"):
            tables[name] = (list(value.index), list(value.values))
        else:
            rest[name] = value
    return rest, tables


def prepare(model: Path, workbooks: list[Path], workdir: Path,
            tables: dict | None = None) -> tuple[Path, list[str], list[str]]:
    """Copy the model into workdir, adapt it for PySD, translate it."""
    import pysd

    if not model.exists():
        raise RunError(f"model not found: {model}")
    if xmile_support.is_xmile(model):
        return prepare_xmile(model, workdir, tables)

    text = model.read_text()
    patches: list[str] = []

    # A declared variable with no right-hand side (Vensim :SUPPLEMENTARY data).
    empty_rhs = re.compile(r"^([A-Za-z\"][^=~|\n]*?)[ \t]*\n(?=\t~)", re.M)
    names = [m.group(1).strip() for m in empty_rhs.finditer(text)]
    if names:
        text = empty_rhs.sub(lambda m: f"{m.group(1).strip()} = 0\n", text)
        patches.append(
            f"gave '= 0' to {len(names)} variable(s) declared without an "
            f"equation: {', '.join(names)}"
        )

    # Vensim's indirect file reference.
    indirect = re.findall(r"'\?([^']+)'", text)
    if indirect:
        text = re.sub(r"'\?([^']+)'", r"'\1'", text)
        patches.append(
            f"dropped the '?' from {len(indirect)} file reference(s): "
            f"{', '.join(sorted(set(indirect)))}"
        )

    copy = workdir / model.name
    copy.write_text(text)

    # Vensim resolves a file reference relative to the model, so the reference
    # has to be reproduced verbatim inside the work directory. Hence, copying the
    # workbook in flat would leave 'config/parameters/x.xlsx' unresolvable.
    by_name = {book.name: book for book in workbooks}
    missing: list[str] = []
    for reference in sorted(set(_FILE_REF.findall(text))):
        candidates = [model.parent / reference]
        named = by_name.get(Path(reference).name)
        if named is not None:
            candidates.append(named)
        source = next((c for c in candidates if Path(c).is_file()), None)
        if source is None:
            missing.append(reference)
            continue
        destination = workdir / reference
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, destination)
        patches.append(f"placed {reference} (from {source})")

    if missing:
        raise RunError(
            "the model reads files that were not found:\n  "
            + "\n  ".join(missing)
            + "\n  Looked next to the model and among the -d inputs. Pass the "
            "file with -d, or check the path written in the model."
        )

    # bare-name references still resolve if the workbook sits beside the model
    for book in workbooks:
        target = workdir / book.name
        if not target.exists():
            shutil.copy(book, target)

    try:
        pysd.read_vensim(str(copy))
    except Exception as error:
        raise RunError(
            f"PySD could not translate {model.name}: {type(error).__name__}: "
            f"{str(error)[:300]}"
        ) from None
    return copy.with_suffix(".py"), patches, find_stub_lookups(text)


def canonical(name: str) -> str:
    """Fold a variable name the way Vensim compares them.

    Vensim is case-insensitive, treats spaces and underscores as the same
    character and collapses runs of them. PySD's namespace is none of those
    things, so a changes file that Vensim accepts, e.g., "Baseline Annual Kills per
    Predator" against a model declaring "... Kills Per Predator", would
    otherwise look like an unknown variable.
    """
    return " ".join(name.replace("_", " ").split()).lower()


def match_to_model(model, params: dict) -> tuple[dict, list[str]]:
    """Map parameter names onto the model's spelling. Returns (params, unknown).

    Names that fold onto a model variable are renamed to the model's own
    spelling. Names with no match are dropped and returned: the same ``models/config/``
    often has to serve several versions of a model, and a value that was
    hard-coded in an earlier version has no variable to bind to. A typo looks
    the same, which is why the names are reported.
    """
    namespace = getattr(model, "_namespace", {})
    if not namespace:
        return params, []

    by_fold = {canonical(name): name for name in namespace}
    matched: dict = {}
    unknown: list[str] = []

    for name, value in params.items():
        base, _, subscript = name.partition("[")
        target = by_fold.get(canonical(base))
        if target is None:
            unknown.append(name)
            continue
        matched[target + ("[" + subscript if subscript else "")] = value

    return matched, sorted(unknown)


def split_initial_values(params: dict, stocks: set) -> tuple[dict, dict]:
    """Take the values given for stocks out of ``params``.

    Stella's import sets a stock's *initial* value.  Handed to PySD as a
    parameter, the same number would replace the stock by a constant and the
    stock would never move.  They go to ``initial_condition`` instead.
    """
    rest, initial = {}, {}
    for name, value in params.items():
        target = initial if xmile_support.canonical(name) in stocks else rest
        target[name] = value
    return rest, initial


def held_components(model, names) -> list[str]:
    """PySD's Python names for the given model names."""
    wanted = {xmile_support.canonical(n) for n in names}
    namespace = getattr(model, "_namespace", {})
    return [py for real, py in namespace.items()
            if xmile_support.canonical(real) in wanted]


def write_output(result, model, target: Path, layout: str,
                 decimal_comma: bool = False) -> None:
    """Write the run tidy, in the Vensim export layout, or in Stella's."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if layout == "tidy":
        result.to_csv(target, index_label="time")
        return
    if layout == "stella":
        unit = "Time"
        try:
            doc = model.doc
            row = doc[doc["Py Name"] == "final_time"]
            if not row.empty and str(row.iloc[0]["Units"]).strip():
                unit = str(row.iloc[0]["Units"]).strip()
        except Exception:
            pass
        stella_csv.write_results(result, target, unit, decimal_comma)
        return

    units = {}
    try:
        doc = model.doc
        units = dict(zip(doc["Real Name"], doc["Units"]))
    except Exception:      # older PySD, or a model without documented units
        pass

    frame = result.T
    frame.insert(0, "Units", [units.get(name, "") for name in frame.index])
    frame.index.name = "Time"
    frame.to_csv(target)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run a Vensim or Stella model with PySD, with or without "
                    "externalised data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Inputs are applied in the order given: a scenario listed after "
               "the base parameters overrides them.",
    )
    parser.add_argument("model", type=Path,
                        help="the .mdl or .stmx file to run")
    parser.add_argument(
        "-d", "--data", action="append", default=[], metavar="PATH",
        help=".cin, .csv or .xlsx file, or a directory of them: repeatable",
    )
    parser.add_argument("-o", "--output", type=Path,
                        help="where to write the run (default: stdout)")
    parser.add_argument(
        "--method", default=None, choices=sorted(TABLEAUX) + ["rk2"],
        help="integration method (default: for a .stmx the one the file "
             "declares, Stella's RK2 being rk2-heun; for a .mdl rk2-midpoint, "
             "which is what Vensim's RK2 turned out to be)",
    )
    parser.add_argument("--time-step", type=float,
                        help="DT (default: the model's own setting)")
    parser.add_argument("--saveper", type=float,
                        help="output interval (default: the model's own setting)")
    parser.add_argument("--initial-time", type=float)
    parser.add_argument("--final-time", type=float)
    parser.add_argument("--columns", nargs="+", metavar="NAME",
                        help="variables to return (default: all)")
    parser.add_argument("--layout", default="tidy",
                        choices=("tidy", "vensim", "stella"),
                        help="tidy: time in the first column. vensim: one row "
                             "per variable with a units column, matching a "
                             "Vensim 'Export Dataset'. stella: one row per "
                             "variable, time unit first, matching Stella's "
                             "horizontal export (default: tidy)")
    parser.add_argument("--decimal-comma", action="store_true",
                        help="with --layout stella, write ';' and decimal "
                             "commas as a German Stella does")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        import pysd  # noqa: F401
    except ImportError:
        print("error: pysd is required (pip install pysd)", file=sys.stderr)
        return 1

    import pysd

    with tempfile.TemporaryDirectory(prefix="pysd-run-") as tmp:
        workdir = Path(tmp)
        try:
            files = expand(args.data)
            params, workbooks, log = collect(files)
            facts = (xmile_support.ModelFacts(args.model)
                     if xmile_support.is_xmile(args.model)
                     and args.model.exists() else None)
            tables = {}
            if facts is not None:
                params, tables = split_tables(params, facts.graphical)
            compiled, patches, stubs = prepare(args.model, workbooks, workdir,
                                               tables)
        except RunError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1

        for line in log:
            print(f"read  {line}", file=sys.stderr)
        for patch in patches:
            print(f"patch {patch}", file=sys.stderr)

        # A stubbed lookup that nobody supplied does not fail -- it quietly
        # produces a wrong run. Say so loudly.
        unsupplied = [name for name in stubs if name not in params]
        if unsupplied:
            print(
                "WARNING: the model defines these lookups as placeholders and "
                "no input supplied them:\n  " + "\n  ".join(unsupplied)
                + "\n  The run will complete and the numbers will be wrong. "
                "Pass the .cin files that define them (e.g., -d models/config/lookups/).",
                file=sys.stderr,
            )

        method = args.method
        if method is None:
            declared = facts.integration_method() if facts else None
            method = declared or "rk2-midpoint"
            if facts is not None:
                source = (f"declared {facts.method!r} in the model file"
                          if declared else "the model declares none")
                print(f"method {method} ({source})", file=sys.stderr)

        model = pysd.load(str(compiled))
        hold = held_components(model, facts.step_variables) if facts else []
        model = attach(model, method, hold=hold)
        if hold and method != "euler":
            print("hold  STEP once per time step, as Stella does: "
                  + ", ".join(hold), file=sys.stderr)

        params, unknown = match_to_model(model, params)
        initial = {}
        if facts is not None:
            params, initial = split_initial_values(params, facts.stocks)
            for name in initial:
                print(f"init  {name}: initial value, as Stella's import sets it",
                      file=sys.stderr)
        if unknown:
            print(
                "note: not in this model, so not applied:\n  "
                + "\n  ".join(unknown)
                + "\n  Expected when the same config serves several model "
                "versions and a typo would look the same, so check the spelling.",
                file=sys.stderr,
            )

        settings = {
            "time_step": args.time_step,
            "saveper": args.saveper,
            "initial_time": args.initial_time,
            "final_time": args.final_time,
        }
        settings = {k: v for k, v in settings.items() if v is not None}
        if initial:
            start = (args.initial_time if args.initial_time is not None
                     else model.components.initial_time())
            settings["initial_condition"] = (start, initial)

        try:
            result = model.run(params=params or None,
                               return_columns=args.columns, **settings)
        except Exception as error:
            print(f"error: the run failed: {type(error).__name__}: {error}",
                  file=sys.stderr)
            return 1

        if args.output:
            write_output(result, model, args.output, args.layout,
                         args.decimal_comma)
            print(f"wrote {args.output}  ({len(result)} time points, "
                  f"{len(result.columns)} variables, method {method})",
                  file=sys.stderr)
        else:
            result.to_csv(sys.stdout, index_label="time")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
