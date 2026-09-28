# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Read and write the tables Stella imports and exports.

Stella writes its tables in the locale it runs under. On a German system that
is a semicolon between cells and a decimal comma, which a plain CSV reader
takes for text. Both are detected per file rather than assumed.

**Parameters** (what *File > Import Data* reads), one variable per row::

    Baseline Annual Kills Per Predator;40
    Baseline Biomass Growth Fraction;0,1
    ="Effect of Deer Density on Predator Births:x";0;0,2;0,4;…
    ="Effect of Deer Density on Predator Births:y";-1;-0,95;-0,9;…

A graphical function takes two rows, its ``:x`` and its ``:y`` points. The
``="…"`` is how Stella keeps a spreadsheet from reading the name as a
formula.

**Results** (what *File > Export Data* writes, horizontal orientation), the
first row holding time with the time unit as its label::

    Years;1900;1900,05;1900,1;…
    Deer Population;4000;3996,26540712;…
"""

from __future__ import annotations

import csv
from pathlib import Path


class NotAStellaTable(Exception):
    """The file is not in either of Stella's layouts."""


def _dialect(sample: str) -> tuple[str, bool]:
    """The cell separator, and whether numbers use a decimal comma."""
    separator = ";" if sample.count(";") > sample.count(",") else ","
    decimal_comma = separator == ";" and any(
        cell.strip().replace(",", "", 1).replace("-", "", 1).isdigit()
        and "," in cell
        for line in sample.splitlines()
        for cell in line.split(";")[1:]
    )
    return separator, decimal_comma


def _number(text: str, decimal_comma: bool) -> float:
    text = text.strip()
    if decimal_comma:
        text = text.replace(".", "").replace(",", ".") if text.count(",") == 1 \
            else text
    return float(text)


def _rows(path: Path) -> tuple[list[list[str]], bool]:
    raw = Path(path).read_text(encoding="utf-8-sig")
    separator, decimal_comma = _dialect(raw[:20000])
    rows = [
        [cell.strip() for cell in row]
        for row in csv.reader(raw.splitlines(), delimiter=separator)
        if row and any(cell.strip() for cell in row)
    ]
    return rows, decimal_comma


def _name(cell: str) -> str:
    """``="Name:x"`` or ``"Name"`` or ``Name`` to ``Name``."""
    cell = cell.strip()
    if cell.startswith("="):
        cell = cell[1:]
    return cell.strip().strip('"').strip()


def is_stella_table(path) -> bool:
    """Semicolon-separated, or carrying a ``:x``/``:y`` graphical function."""
    try:
        head = Path(path).read_text(encoding="utf-8-sig")[:20000]
    except (OSError, UnicodeDecodeError):
        return False
    return ";" in head.splitlines()[0] if head.strip() else False


def read_parameters(path) -> dict:
    """``{name: float}`` for constants, ``{name: pandas.Series}`` for tables.

    A graphical function becomes a Series indexed by its x points, which is
    the form PySD's ``run(params=...)`` takes for a lookup.
    """
    import pandas as pd

    rows, decimal_comma = _rows(path)
    values: dict = {}
    tables: dict = {}
    for row in rows:
        if len(row) < 2:
            continue
        name = _name(row[0])
        numbers = []
        for cell in row[1:]:
            if not cell:
                continue
            try:
                numbers.append(_number(cell, decimal_comma))
            except ValueError:
                raise NotAStellaTable(
                    f"{path}: {cell!r} in the row for {name!r} is not a number"
                ) from None
        if name.endswith((":x", ":y")):
            tables.setdefault(name[:-2], {})[name[-1]] = numbers
        elif len(numbers) == 1:
            values[name] = numbers[0]
        else:
            raise NotAStellaTable(
                f"{path}: {name!r} has {len(numbers)} values; a parameter row "
                f"holds one, a table is written as two rows ending ':x' and ':y'"
            )

    for name, axes in tables.items():
        if set(axes) != {"x", "y"} or len(axes["x"]) != len(axes["y"]):
            raise NotAStellaTable(
                f"{path}: the table {name!r} needs an ':x' and a ':y' row of "
                f"equal length"
            )
        values[name] = pd.Series(axes["y"], index=axes["x"])
    return values


def read_results(path) -> tuple[list[float], dict[str, list[float]], str]:
    """``(times, {variable: values}, time unit)`` from a Stella export."""
    rows, decimal_comma = _rows(path)
    if not rows:
        raise NotAStellaTable(f"{path}: empty")
    header = rows[0]
    try:
        times = [_number(cell, decimal_comma) for cell in header[1:] if cell]
    except ValueError:
        raise NotAStellaTable(f"{path}: the first row is not a time axis") from None
    series = {}
    for row in rows[1:]:
        values = [_number(cell, decimal_comma) for cell in row[1:] if cell]
        series[_name(row[0])] = values
    return times, series, header[0]


def write_results(frame, target, time_unit: str = "Time",
                  decimal_comma: bool = False) -> None:
    """Write a run in Stella's horizontal export layout.

    ``frame`` is indexed by time with one column per variable, as PySD
    returns it.  ``decimal_comma`` writes ``;`` and ``,`` as a German Stella
    does, so the two files can be compared cell by cell.
    """
    separator = ";" if decimal_comma else ","

    def show(value) -> str:
        text = repr(float(value))
        if text.endswith(".0"):
            text = text[:-2]
        return text.replace(".", ",") if decimal_comma else text

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=separator)
        writer.writerow([time_unit] + [show(t) for t in frame.index])
        for column in frame.columns:
            writer.writerow([column] + [show(v) for v in frame[column]])
