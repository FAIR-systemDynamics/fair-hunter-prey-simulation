#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Translate a parameter CSV into a Vensim changes file (``.cin``).

A ``.cin`` file assigns values to constants, lookups and string variables. It
looks like model equations but without the tilde/bar terminators::

    Initial Deer Population = 4000
    Kaibab Forage Carrying Capacity = 350000
    Growth Rate[Region1] = 0.03

Examples
--------
Defaults are enough for a two-column file:

    python scripts/csv_to_cin.py models/config/parameters/basic_parameters.csv \
        -o models/config/parameters/basic_parameters.cin

Explicit columns, subscripts, and a comment column:

    python scripts/csv_to_cin.py params.csv -o params.cin \
        --variable-col name --value-col value \
        --subscript-col region --subscript-col product \
        --comment-col note

Semicolon-separated export with German decimal commas:

    python scripts/csv_to_cin.py params.csv --delimiter ';' --decimal ','
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# Column names tried when --variable-col / --value-col / --comment-col are omitted.
VARIABLE_COL_GUESSES = ("variable_name", "variable", "name", "parameter", "constant")
VALUE_COL_GUESSES = ("value", "val")
COMMENT_COL_GUESSES = ("comment", "note", "description")

# Vensim needs quotes around names that are not plain words. Leading digits and
# anything outside letters/digits/space/underscore force quoting.
PLAIN_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9 _]*$")


class ConversionError(Exception):
    """Raised for input the caller has to fix, reported without a traceback."""


def normalise(text: str) -> str:
    """Fold a header into a comparable form: lowercase, no surrounding space."""
    return text.strip().lower().replace(" ", "_")


def resolve_column(
    spec: str | None,
    header: list[str],
    guesses: tuple[str, ...],
    role: str,
    required: bool = True,
) -> int | None:
    """Turn a column spec into an index into ``header``.

    ``spec`` is a column name (case- and space-insensitive) or a 0-based index.
    When ``spec`` is None the ``guesses`` are tried in order.
    """
    folded = [normalise(h) for h in header]

    if spec is not None:
        if spec.lstrip("-").isdigit():
            index = int(spec)
            if not 0 <= index < len(header):
                raise ConversionError(
                    f"--{role}-col {index} is out of range; the file has "
                    f"{len(header)} column(s): {', '.join(header)}"
                )
            return index
        if normalise(spec) in folded:
            return folded.index(normalise(spec))
        raise ConversionError(
            f"no column named {spec!r} for --{role}-col; "
            f"available columns: {', '.join(header)}"
        )

    for guess in guesses:
        if guess in folded:
            return folded.index(guess)

    if not required:
        return None
    raise ConversionError(
        f"could not guess the {role} column (tried: {', '.join(guesses)}). "
        f"Pass --{role}-col explicitly; available columns: {', '.join(header)}"
    )


def quote_name(name: str) -> str:
    """Wrap a variable name in double quotes if Vensim would need them."""
    return name if PLAIN_NAME.match(name) else '"' + name.replace('"', r"\"") + '"'


def clean_value(raw: str, decimal: str, allow_raw: bool, variable: str) -> str:
    """Validate and normalise a value cell, preserving its literal formatting.

    The text is passed through unchanged (so ``0.10`` stays ``0.10`` rather than
    collapsing to ``0.1``), only the decimal separator is converted when needed.
    """
    value = raw.strip()
    if not value:
        raise ConversionError(f"{variable!r} has an empty value")

    if decimal != ".":
        value = value.replace(decimal, ".")

    try:
        float(value)
    except ValueError:
        if allow_raw:
            return value
        raise ConversionError(
            f"{variable!r} has a non-numeric value {raw.strip()!r}. A .cin file "
            f"only assigns constants, lookups and string variables -- pass "
            f"--raw-values to write it through unchanged (e.g., for a lookup)."
        ) from None
    return value


def format_comment(text: str, style: str) -> str:
    """Render a trailing comment in the requested Vensim comment syntax."""
    collapsed = " ".join(text.split())
    if style == "tilde":
        return f" ~ {collapsed}"
    if style == "brace":
        return f" {{{collapsed}}}"
    raise AssertionError(f"unhandled comment style {style!r}")


def build_lines(
    rows: list[dict[str, str]],
    header: list[str],
    variable_idx: int,
    value_idx: int,
    subscript_idx: list[int],
    comment_idx: int | None,
    decimal: str,
    allow_raw: bool,
    comment_style: str,
) -> list[str]:
    """Turn parsed CSV rows into .cin assignment lines."""
    lines: list[str] = []
    seen: dict[str, int] = {}

    for number, row in enumerate(rows, start=2):  # start=2: row 1 is the header
        cells = [row.get(name, "") or "" for name in header]
        variable = cells[variable_idx].strip()

        if not variable and not any(cell.strip() for cell in cells):
            continue  # blank line in the CSV
        if not variable:
            raise ConversionError(f"row {number}: no variable name")

        elements = [cells[i].strip() for i in subscript_idx]
        elements = [e for e in elements if e]
        target = quote_name(variable)
        if elements:
            target += "[" + ",".join(elements) + "]"

        key = normalise(target)
        if key in seen:
            raise ConversionError(
                f"row {number}: {target} was already assigned in row {seen[key]}. "
                f"Vensim silently keeps the last assignment, so this is almost "
                f"certainly a mistake -- remove the duplicate."
            )
        seen[key] = number

        value = clean_value(cells[value_idx], decimal, allow_raw, variable)
        line = f"{target} = {value}"

        if comment_idx is not None:
            comment = cells[comment_idx].strip()
            if comment:
                if comment_style == "line":
                    lines.append(f":C {' '.join(comment.split())}")
                else:
                    line += format_comment(comment, comment_style)

        lines.append(line)

    if not lines:
        raise ConversionError("no parameters found -- the file has no data rows")
    return lines


def read_csv(path: Path, delimiter: str | None) -> tuple[list[str], list[dict[str, str]]]:
    """Read the CSV and return its header and rows, with whitespace stripped."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise ConversionError(f"input file not found: {path}") from None
    except UnicodeDecodeError:
        raise ConversionError(
            f"{path} is not valid UTF-8. Re-export it as UTF-8 (Excel: "
            f'"CSV UTF-8") or convert it with iconv.'
        ) from None

    if delimiter is None:
        try:
            delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;\t").delimiter
        except csv.Error:
            delimiter = ","

    reader = csv.reader(text.splitlines(), delimiter=delimiter)
    try:
        header = [column.strip() for column in next(reader)]
    except StopIteration:
        raise ConversionError(f"{path} is empty") from None

    rows = [dict(zip(header, [cell.strip() for cell in cells])) for cells in reader]
    return header, rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Translate a parameter CSV into a Vensim changes file (.cin).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Columns are given by name (case- and space-insensitive) or by "
        "0-based index. Omitted column options are guessed from the header.",
    )
    parser.add_argument("csv_file", type=Path, help="input CSV file")
    parser.add_argument(
        "-o", "--output", type=Path,
        help="output .cin file (default: write to stdout)",
    )
    parser.add_argument("--variable-col", help="column holding the variable names")
    parser.add_argument("--value-col", help="column holding the values")
    parser.add_argument(
        "--subscript-col", action="append", default=[], metavar="COL",
        help="column holding a subscript element; repeat once per subscript "
             "dimension, in the order Vensim expects them",
    )
    parser.add_argument(
        "--comment-col",
        help="column whose text is appended as a comment to each line",
    )
    parser.add_argument(
        "--comment-style", choices=("tilde", "brace", "line"), default="tilde",
        help="how to write comments: 'x ~ text' (default), 'x {text}', "
             "or ':C text' on its own line above",
    )
    parser.add_argument(
        "--delimiter", help="CSV delimiter (default: detected from the file)",
    )
    parser.add_argument(
        "--decimal", default=".", choices=(".", ","),
        help="decimal separator used in the CSV (default: '.')",
    )
    parser.add_argument(
        "--raw-values", action="store_true",
        help="pass non-numeric values through unchanged instead of failing",
    )
    parser.add_argument(
        "--header", action="append", default=[], metavar="TEXT",
        help="prepend a ':C TEXT' provenance comment; repeatable",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        header, rows = read_csv(args.csv_file, args.delimiter)

        variable_idx = resolve_column(
            args.variable_col, header, VARIABLE_COL_GUESSES, "variable")
        value_idx = resolve_column(
            args.value_col, header, VALUE_COL_GUESSES, "value")
        subscript_idx = [
            resolve_column(spec, header, (), "subscript")
            for spec in args.subscript_col
        ]
        comment_idx = resolve_column(
            args.comment_col, header, COMMENT_COL_GUESSES, "comment",
            required=args.comment_col is not None,
        )

        lines = build_lines(
            rows, header, variable_idx, value_idx, subscript_idx, comment_idx,
            args.decimal, args.raw_values, args.comment_style,
        )
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    preamble = [f":C {text}" for text in args.header]
    preamble.append(f":C generated from {args.csv_file.name} by csv_to_cin.py")
    output = "\n".join(preamble + [""] + lines) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8", newline="\n")
        print(
            f"wrote {len(lines)} assignment(s) to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
