#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Publication-ready figures from exported simulation results.

Reads one CSV per scenario and draws a stacked multi-panel figure. **Panels are
grouped by unit**, not by variable name: every variable sharing a unit lands in
the same panel, on the same axis, where the curves are directly comparable.

Output is black and white by default. Scenarios are distinguished by *marker
shape*. Markers are placed at even intervals along each curve rather than on
every data point, which would bury the curve. ``--linestyles`` switches to dash
patterns instead, ``--color`` adds a validated colour palette for slides.

A variable whose values are identical in every input file does not depend on the
scenario, like a reference mode, a historical series, an exogenous input. Drawing it
once per scenario would imply a difference that is not there, so it is drawn once
and labelled as a reference. ``--repeat-identical`` disables that.

Input formats (detected automatically)
--------------------------------------
* PySD (``result.to_csv()``): time in the first column, one column per variable.
* Vensim "Export Dataset": one row per variable, time in the header row, with
  the variable name and its unit as leading columns::

      "Time","Year",1900,1900.05,…
      "Deer Population","Deer",4000,3996.27,…

Examples
--------
::

    python scripts/plot_results.py results/runs/case1.csv results/runs/case2.csv
    python scripts/plot_results.py results/runs/case*.csv --format png --color
    python scripts/plot_results.py run.csv --width 90 --serif   # single column
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vensim_csv import NotATimeSeries, read_dataset  # noqa: E402

MM_PER_INCH = 25.4

# Scenario encoding: marker shapes, filled. The hairline white edge is not
# decoration -- it keeps two markers separable where curves cross and the
# symbols would otherwise merge into one blob.
MARKERS = ["o", "s", "^", "D", "v", "P"]
MARKER_SPACING = 0.09   # fraction of the curve length between markers

# Fallback encoding for --linestyles: dash patterns, most legible first.
LINE_STYLES = [
    (0, ()),                # solid
    (0, (5.5, 2.2)),        # dashed
    (0, (1.1, 1.6)),        # dotted
    (0, (5.5, 2, 1, 2)),    # dash-dot
    (0, (8, 2, 1, 2, 1, 2)),
]
# Variables within one panel: grey values, dark first.
GREY_LEVELS = ["#000000", "#6b6b6b", "#a3a3a3"]
REFERENCE_GREY = "#8a8a8a"

# Validated categorical palette for --color (light surface #fcfcfb):
# worst-pair CVD dE 24.7, normal-vision dE 33.6, contrast >= 3:1.
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]

INK = "#000000"
GRID = "#d9d9d9"


class PlotError(Exception):
    """Raised for input the caller has to fix; reported without a traceback."""


def is_number(text) -> bool:
    try:
        float(text)
    except (TypeError, ValueError):
        return False
    return True


def load_results(path: Path):
    """Read one results file. Returns ``({variable: Series}, {variable: unit})``.

    Delegates to :mod:`vensim_csv`, which keeps every variable on the time axis
    it was actually recorded on. A Vensim export that contains lookup data or a
    reference mode carries more than one.
    """
    try:
        return read_dataset(path)
    except FileNotFoundError:
        raise PlotError(f"input file not found: {path}") from None
    except NotATimeSeries as error:
        raise PlotError(str(error)) from None
    except Exception as error:
        raise PlotError(f"could not read {path}: {error}") from None


def group_by_unit(columns, units) -> list[tuple[str, list[str]]]:
    """Group variables into panels by shared unit, keeping input order."""
    panels: list[tuple[str, list[str]]] = []
    index: dict[str, int] = {}
    for column in columns:
        unit = units.get(column, "")
        key = unit or f"__{column}"  # no unit: variable gets its own panel
        if key not in index:
            index[key] = len(panels)
            panels.append((unit, []))
        panels[index[key]][1].append(column)
    return panels


def find_invariant(frames, columns) -> set[str]:
    """Variables whose values *and* time base are identical across every scenario."""
    if len(frames) < 2:
        return set()
    invariant = set()
    reference = next(iter(frames.values()))
    for column in columns:
        present = [f[column] for f in frames.values() if column in f]
        if len(present) != len(frames) or column not in reference:
            continue
        if all(series.equals(reference[column]) for series in present):
            invariant.add(column)
    return invariant


def thousands(value, _pos) -> str:
    """Axis tick labels with a thin space as thousands separator."""
    if value == int(value):
        return f"{int(value):,}".replace(",", " ")
    return f"{value:,.2f}".replace(",", " ")


def apply_style(serif: bool, base_size: float) -> None:
    import matplotlib as mpl

    mpl.rcParams.update({
        "font.family": "serif" if serif else "sans-serif",
        "font.size": base_size,
        "axes.labelsize": base_size,
        "axes.titlesize": base_size,
        "xtick.labelsize": base_size - 1,
        "ytick.labelsize": base_size - 1,
        "legend.fontsize": base_size - 1,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "lines.linewidth": 1.2,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,   # embed as TrueType, not Type 3: journals require it
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def draw(frames, panels, invariant, width_mm, panel_height_mm, use_color,
         use_linestyles, title):
    """Draw the figure: one panel per unit, scenarios by line style."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    count = len(panels)
    figure, axes = plt.subplots(
        count, 1, sharex=True,
        figsize=(width_mm / MM_PER_INCH, count * panel_height_mm / MM_PER_INCH),
    )
    if count == 1:
        axes = [axes]

    for position, (ax, (unit, columns)) in enumerate(zip(axes, panels)):
        scenario_columns = [c for c in columns if c not in invariant]

        for variable_slot, column in enumerate(scenario_columns):
            for scenario_slot, (name, frame) in enumerate(frames.items()):
                if column not in frame:
                    continue
                label = name if len(scenario_columns) == 1 else f"{column} — {name}"
                color = (SERIES_COLORS[scenario_slot % len(SERIES_COLORS)]
                         if use_color
                         else GREY_LEVELS[variable_slot % len(GREY_LEVELS)])
                # stagger the marker positions so scenarios do not stack up
                offset = scenario_slot * MARKER_SPACING / max(len(frames), 1)
                series = frame[column]
                ax.plot(
                    series.index, series.values,
                    linestyle=(LINE_STYLES[scenario_slot % len(LINE_STYLES)]
                               if use_linestyles else "-"),
                    marker=None if use_linestyles else MARKERS[scenario_slot % len(MARKERS)],
                    markevery=(offset, MARKER_SPACING),
                    markersize=4.0, markerfacecolor=color, markeredgewidth=0.5,
                    markeredgecolor="white",
                    color=color, linewidth=1.0, label=label,
                    solid_capstyle="round", dash_capstyle="round", zorder=3,
                )

        # scenario-independent series: drawn once, visibly subordinate
        for column in (c for c in columns if c in invariant):
            series = next(f[column] for f in frames.values() if column in f)
            ax.plot(
                series.index, series.values,
                linestyle=(0, (2.5, 1.8)), color=REFERENCE_GREY, linewidth=1.0,
                label=f"{column} (reference)", zorder=2,
            )

        # The variable name goes in the panel title, the unit on the axis:
        # "Predator Population [Predators]" as a y-label is longer than the
        # panel is tall and collides with its neighbours.
        ax.set_ylabel(unit if unit else "", color=INK)
        ax.yaxis.set_major_formatter(FuncFormatter(thousands))
        ax.grid(True, axis="y", color=GRID, linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)
        # A closed frame on every panel: with three stacked panels an open
        # L-shape leaves the plotting areas visually unbounded on the right,
        # where the curves run out.
        for side in ("top", "right", "bottom", "left"):
            ax.spines[side].set_visible(True)
            ax.spines[side].set_color(INK)
        ax.tick_params(colors=INK)
        for label in (*ax.get_xticklabels(), *ax.get_yticklabels()):
            label.set_color(INK)

        heading = ", ".join(scenario_columns) or ", ".join(columns)
        if count > 1:
            heading = f"({chr(ord('a') + position)}) {heading}"
        ax.set_title(heading, loc="left", pad=8, color=INK, fontweight="bold")

        # Anchor the axis at zero, and put both limits exactly on a tick, so
        # the topmost label sits on the frame instead of floating below it.
        values = [f[c] for f in frames.values() for c in columns if c in f]
        data_low = min((float(v.min()) for v in values), default=0.0)
        data_high = max((float(v.max()) for v in values), default=1.0)
        if data_high <= data_low:
            data_high = data_low + 1.0

        bottom = 0.0 if data_low >= 0 else data_low
        ticks = [t for t in
                 MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10]).tick_values(
                     bottom, data_high)
                 if t >= bottom]
        if not ticks or ticks[-1] < data_high:
            ticks = list(ticks) + [data_high]
        ax.set_yticks(ticks)
        ax.set_ylim(ticks[0], ticks[-1])

    # Clip the time axis to the simulated period. Matplotlib's default margin
    # otherwise pads a couple of years onto both ends, which reads as data that
    # was not simulated.
    every = [series for frame in frames.values() for series in frame.values()]
    x_low = min(float(series.index.min()) for series in every)
    x_high = max(float(series.index.max()) for series in every)
    for ax in axes:
        ax.set_xlim(x_low, x_high)

    axes[-1].set_xlabel("Year", color=INK)

    # One legend for the whole figure. Per-panel legends repeat the same two
    # entries three times and eat the space the data should have.
    handles, labels = [], []
    for ax in axes:
        for handle, label in zip(*ax.get_legend_handles_labels()):
            if label not in labels:
                handles.append(handle)
                labels.append(label)

    figure.align_ylabels(axes)

    height_inches = count * panel_height_mm / MM_PER_INCH
    reserved = (2.4 * plt.rcParams["font.size"] / 72) / height_inches
    figure.tight_layout(h_pad=1.1, rect=(0, reserved, 1, 0.97 if title else 1))
    figure.legend(
        handles, labels, loc="lower center", ncol=min(len(labels), 4),
        frameon=False, handlelength=2.6, columnspacing=2.0,
        bbox_to_anchor=(0.5, 0.0),
    )
    if title:
        figure.suptitle(title, x=0.0, ha="left", color=INK,
                        fontweight="bold", fontsize=plt.rcParams["font.size"] + 1)

    return figure


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Publication-ready figures from exported simulation results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("csv_files", nargs="+", type=Path,
                        help="one results CSV per scenario")
    parser.add_argument("-o", "--outdir", type=Path, default=Path("results/figures"),
                        help="output directory (default: results/figures)")
    parser.add_argument("-n", "--name", default="results",
                        help="output file stem (default: results)")
    parser.add_argument("--columns", nargs="+", metavar="NAME",
                        help="variables to plot (default: all, grouped by unit)")
    parser.add_argument("--format", default="pdf", choices=("pdf", "png", "svg", "eps"),
                        help="output format (default: pdf -- vector, for print)")
    parser.add_argument("--width", type=float, default=180.0, metavar="MM",
                        help="figure width in mm (default: 180, a double column; "
                             "use 90 for a single column)")
    parser.add_argument("--panel-height", type=float, default=48.0, metavar="MM",
                        help="height per panel in mm (default: 48)")
    parser.add_argument("--font-size", type=float, default=9.0,
                        help="base font size in pt (default: 9)")
    parser.add_argument("--serif", action="store_true",
                        help="use a serif face, to match a serif manuscript")
    parser.add_argument("--linestyles", action="store_true",
                        help="distinguish scenarios by dash pattern instead of "
                             "marker shape")
    parser.add_argument("--color", action="store_true",
                        help="use colour instead of black and white (for slides)")
    parser.add_argument("--repeat-identical", action="store_true",
                        help="draw scenario-independent series once per scenario "
                             "instead of once")
    parser.add_argument("--dpi", type=int, default=600,
                        help="raster resolution for --format png (default: 600)")
    parser.add_argument("--title", help="figure title (omit for a manuscript: "
                                        "the caption carries the title)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        import matplotlib
        matplotlib.use("Agg")
    except ImportError:
        print("error: matplotlib is required (pip install matplotlib)", file=sys.stderr)
        return 1

    import matplotlib.pyplot as plt

    try:
        loaded = {path.stem: load_results(path) for path in args.csv_files}
        frames = {name: frame for name, (frame, _) in loaded.items()}
        units: dict[str, str] = {}
        for _, found in loaded.values():
            units.update(found)

        available = list(next(iter(frames.values())))
        columns = args.columns or available
        missing = [c for c in columns if c not in available]
        if missing:
            raise PlotError(
                f"column(s) not in the data: {', '.join(missing)}. "
                f"Available: {', '.join(available)}"
            )

        panels = group_by_unit(columns, units)
        invariant = set() if args.repeat_identical else find_invariant(frames, columns)
    except PlotError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if invariant:
        print(
            f"note: identical in every scenario, drawn once as a reference: "
            f"{', '.join(sorted(invariant))}",
            file=sys.stderr,
        )
    if not units:
        print(
            "note: no units in the input, so each variable gets its own panel. "
            "Export from Vensim with units to group them.",
            file=sys.stderr,
        )

    apply_style(args.serif, args.font_size)
    figure = draw(frames, panels, invariant, args.width, args.panel_height,
                  args.color, args.linestyles, args.title)

    args.outdir.mkdir(parents=True, exist_ok=True)
    target = args.outdir / f"{args.name}.{args.format}"
    figure.savefig(target, dpi=args.dpi)
    plt.close(figure)

    print(f"wrote {target}  ({len(panels)} panels, {len(frames)} scenarios)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
