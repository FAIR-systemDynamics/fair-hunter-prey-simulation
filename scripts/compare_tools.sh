#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
#
# Run the model under PySD and plot the result against the committed Vensim
# runs, so the difference between the two tools is visible in one figure rather
# than buried in a table of deviations.
#
#   ./scripts/compare_tools.sh
#
# Writes results/runs/case{1,2}_pysd.csv and results/figures/results_pysd.{pdf,png}.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL="${1:-models/kaibab_ecosystem_model.mdl}"
[ -f "$MODEL" ] || { echo "error: model not found: $MODEL" >&2; exit 1; }

STOCKS=("Deer Population" "Forage Biomass" "Predator Population")

# Compare against whichever Vensim export matches the model in the tree: the
# externalised model produces *_external.csv, the parameterised one *_parameter.csv.
if [ -f results/runs/case1_external.csv ] && grep -q ':NA:' "$MODEL"; then
    SUFFIX=external
elif [ -f results/runs/case1_parameter.csv ]; then
    SUFFIX=parameter
elif [ -f results/runs/case1_external.csv ]; then
    SUFFIX=external
else
    echo "error: no Vensim run in results/runs/ to compare against" >&2
    exit 1
fi
echo "comparing against the ${SUFFIX} runs"

inputs=()
for candidate in models/config/parameters/basic_parameters.cin \
                 models/config/lookups models/config/timeseries; do
    [ -e "$candidate" ] && inputs+=(-d "$candidate")
done

run_case() {                       # run_case <name> [extra -d …]
    local name="$1"; shift
    python runners/pysd/run.py "$MODEL" "${inputs[@]}" "$@" \
        --columns "${STOCKS[@]}" --saveper 1 \
        -o "results/runs/${name}_pysd.csv"
}

run_case case1
if [ -f models/config/scenarios/case2.cin ]; then
    run_case case2 -d models/config/scenarios/case2.cin
else
    echo "note: no case2 scenario recorded, plotting case1 only" >&2
fi

figures=()
for case in case1 case2; do
    [ -f "results/runs/${case}_${SUFFIX}.csv" ] && figures+=("results/runs/${case}_${SUFFIX}.csv")
    [ -f "results/runs/${case}_pysd.csv" ] && figures+=("results/runs/${case}_pysd.csv")
done

for format in pdf png; do
    python scripts/plot_results.py "${figures[@]}" \
        --columns "${STOCKS[@]}" -n results_pysd --format "$format"
done

echo
echo "Vensim vs PySD, worst relative deviation:"
python - "$SUFFIX" <<'PY'
import sys
sys.path.insert(0, "scripts")
from pathlib import Path
from vensim_csv import read_dataset

suffix = sys.argv[1]
for case in ("case1", "case2"):
    vensim, pysd = Path(f"results/runs/{case}_{suffix}.csv"), Path(f"results/runs/{case}_pysd.csv")
    if not (vensim.exists() and pysd.exists()):
        continue
    left, _ = read_dataset(vensim)
    right, _ = read_dataset(pysd)
    worst = 0.0
    for name in right:
        if name not in left:
            continue
        shared = [t for t in right[name].index if t in left[name].index]
        if not shared:
            continue
        a, b = left[name].loc[shared], right[name].loc[shared]
        worst = max(worst, float(((a - b).abs() / a.abs().clip(lower=1e-9)).max()))
    print(f"  {case}: {worst:.4%}")
PY
