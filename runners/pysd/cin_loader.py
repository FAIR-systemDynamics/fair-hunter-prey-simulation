# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Read a Vensim constant input file (``.cin``) into parameters for PySD.

A ``.cin`` assigns constants and lookups, while PySD takes the same information as a
dict passed to ``Model.run(params=...)``.

Supported (see https://www.vensim.com/documentation/cin_files.html):

* ``NAME = value`` and subscripted ``NAME[element] = value``
* quoted names, ``"Odd Name (2)" = 7``
* comments: ``:C`` line prefix, ``~`` to end of line, ``{braces}`` inline
* continuation of a statement across lines until the next ``=``

Lookup assignments ``NAME((x1,y1),(x2,y2),…)`` or ``NAME(x1,y1,x2,y2,…)``
come back as a :class:`pandas.Series` indexed by x, which is the shape
``Model.run(params=...)`` expects for a table function.
"""

from __future__ import annotations

import re
from pathlib import Path

_BRACE_COMMENT = re.compile(r"\{[^}]*\}")
_LOOKUP = re.compile(r"^\s*(?P<name>\"[^\"]+\"|[^(]+?)\s*\(\s*(?P<points>.*)\)\s*$")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
_ASSIGNMENT = re.compile(r"^\s*(?P<name>\"[^\"]+\"|[^=\[]+?)\s*"
                         r"(?:\[(?P<subscript>[^\]]*)\])?\s*=\s*(?P<value>.+)$")


class CinError(Exception):
    """Raised for a .cin the caller has to fix."""


def _strip_comments(line: str) -> str:
    line = _BRACE_COMMENT.sub(" ", line)
    if "~" in line:
        line = line.split("~", 1)[0]
    return line.strip()


def read_cin(path: str | Path) -> dict[str, float | str]:
    """Return ``{variable: value}`` from a .cin file.

    Numeric values come back as floats and anything else (a lookup, a string
    variable) comes back as the raw text after the ``=``.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise CinError(f"changes file not found: {path}") from None

    params: dict[str, float | str] = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(":"):   # :C comment, :NOMSG, :MSG
            continue
        line = _strip_comments(line)
        if not line:
            continue

        if "=" not in line:
            lookup = _LOOKUP.match(line)
            if lookup:
                name = lookup["name"].strip().strip('"')
                numbers = [float(n) for n in _NUMBER.findall(lookup["points"])]
                if not numbers or len(numbers) % 2:
                    raise CinError(
                        f"{path}:{number}: {name} has {len(numbers)} numbers; "
                        f"a lookup needs an even count (x,y pairs)"
                    )
                if name in params:
                    raise CinError(f"{path}:{number}: {name} is assigned twice.")
                import pandas as pd  # only needed for lookups
                params[name] = pd.Series(index=numbers[0::2], data=numbers[1::2])
                continue

        match = _ASSIGNMENT.match(line)
        if not match:
            raise CinError(
                f"{path}:{number}: cannot read this as an assignment: {raw.strip()!r}"
            )

        name = match["name"].strip().strip('"')
        if match["subscript"]:
            name = f"{name}[{match['subscript'].strip()}]"
        value = match["value"].strip().rstrip(",")

        if name in params:
            raise CinError(
                f"{path}:{number}: {name} is assigned twice. Vensim silently "
                f"keeps the last one, so this is almost certainly a mistake."
            )

        try:
            params[name] = float(value)
        except ValueError:
            params[name] = value

    if not params:
        raise CinError(f"{path}: no assignments found")
    return params
