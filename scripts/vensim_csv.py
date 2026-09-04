# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Read a simulation result table from Vensim, whatever shape the tool wrote it in.

Three layouts are supported:

**Vensim "Export Dataset", one time axis.** Metadata columns first, then the
time points in the header row, one row per variable::

    "Time","Year",1900,1900.05,1900.1,…
    "Deer Population","Deer",4000,3996.27,3992.64,…

**Vensim export, several time axes.** As soon as the run includes a variable
that carries its own time base, e.g., a reference mode, an imported
time series, Vensim starts a new block with a fresh ``"Time"`` header::

    "Time","Year",1900,1900.05,1900.1,…        <- 1001 points, the DT grid
    "Deer Population","Deer",4000,3996.27,…
    "Time","Year",1900,1902.5,1905,…           <- 21 points, the data's own grid
    "Historical Deer BOT","Deer",4000,4000,…

**Tidy.** Time in the first column, one row per time step, one column per
variable. What PySD writes and what this module writes back.
"""

from __future__ import annotations

import csv
from pathlib import Path

TIME_NAMES = {"time", "year", "t"}


class NotATimeSeries(Exception):
    """The file is a table, but not one of time series."""


def is_number(text) -> bool:
    try:
        float(text)
    except (TypeError, ValueError):
        return False
    return True


def _rows(path: Path) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return [[cell.strip() for cell in row] for row in csv.reader(handle) if row]


def read_dataset(path) -> tuple[dict, dict[str, str]]:
    """Return ``({variable: Series}, {variable: unit})``.

    Each series carries its own time index, so variables recorded on different
    time bases stay on them.
    """
    import pandas as pd

    path = Path(path)
    rows = _rows(path)
    if len(rows) < 2:
        raise NotATimeSeries(f"{path}: fewer than two rows")

    header = rows[0]
    first_number = next((i for i, cell in enumerate(header) if is_number(cell)), None)

    # Tidy: time in the first column, variable names across the header.
    if first_number is None:
        if header[0].strip().lower() not in TIME_NAMES:
            raise NotATimeSeries(
                f"{path}: no time axis found. Expected time in the first column "
                f"or numeric time points in the header row."
            )
        index, columns = [], {name: [] for name in header[1:]}
        for row in rows[1:]:
            if not is_number(row[0]):
                continue
            index.append(float(row[0]))
            for name, cell in zip(header[1:], row[1:]):
                columns[name].append(float(cell) if is_number(cell) else float("nan"))
        series = {name: pd.Series(values, index=index, name=name)
                  for name, values in columns.items()}
        return series, {}

    # Vensim: one or more blocks, each opened by its own header row.
    if first_number == 0:
        raise NotATimeSeries(f"{path}: the header row starts with a number")

    series: dict = {}
    units: dict[str, str] = {}
    axis: list[float] = []

    for row in rows:
        if row[0].strip().lower() in TIME_NAMES and is_number(row[first_number] if len(row) > first_number else ""):
            axis = [float(cell) for cell in row[first_number:] if is_number(cell)]
            continue
        if not axis:
            continue
        name = row[0].strip()
        if not name:
            continue
        unit = row[1].strip() if first_number >= 2 and len(row) > 1 else ""
        values = [float(cell) if is_number(cell) else float("nan")
                  for cell in row[first_number:first_number + len(axis)]]
        if len(values) < len(axis):                    # short row: pad
            values += [float("nan")] * (len(axis) - len(values))
        series[name] = pd.Series(values, index=list(axis), name=name)
        if unit and unit.lower() != "nan":
            units[name] = unit

    if not series:
        raise NotATimeSeries(f"{path}: no variable rows found")
    return series, units


def time_bases(series: dict) -> dict[tuple, list[str]]:
    """Group variable names by the time axis they were recorded on."""
    bases: dict[tuple, list[str]] = {}
    for name, values in series.items():
        bases.setdefault(tuple(values.index), []).append(name)
    return bases
