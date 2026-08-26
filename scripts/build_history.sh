#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
#
# Build the teaching commit history from the current working tree.
#
# The history of this repository is a designed artefact, not a by-product: every
# commit is one step of model development, and the diffs between them are the
# lesson. Building it with a script rather than by hand means a mistake is fixed
# by editing this file and running it again -- no interactive rebase, no tags
# left pointing at orphaned commits.
#
#   ./scripts/build_history.sh                    # build into ../nfdi4sd-history
#   ./scripts/build_history.sh -o /tmp/try --force
#
# The three .mdl files are successive versions of ONE file. They are committed
# as models/kaibab_ecosystem_model.mdl so that each step produces a diff
# against the previous one -- which is the entire point of commits 2 to 4.

set -euo pipefail

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS="$(cd "$SOURCE/.." && pwd)/model"
TARGET="$(cd "$SOURCE/.." && pwd)/nfdi4sd-history"
FORCE=0
MODEL_NAME="models/kaibab_ecosystem_model.mdl"

while [ $# -gt 0 ]; do
    case "$1" in
        -o|--output)  TARGET="$2"; shift 2 ;;
        -m|--models)  MODELS="$2"; shift 2 ;;
        --force)      FORCE=1; shift ;;
        -h|--help)    sed -n '7,22p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *)            echo "unknown option: $1" >&2; exit 2 ;;
    esac
done

STOCK_FLOW="$MODELS/kaibab_ecosystem_model_stock-and-flow.mdl"
PARAMETER="$MODELS/kaibab_ecosystem_model_parameter.mdl"
EXTERNAL="$MODELS/kaibab_ecosystem_model_parameter_external.mdl"

for f in "$STOCK_FLOW" "$PARAMETER" "$EXTERNAL"; do
    [ -f "$f" ] || { echo "error: model not found: $f" >&2; exit 1; }
done

# Each stage commits the runs that its own model version produced, so every
# stage needs its own export. Missing ones are named rather than skipped: a
# history whose results silently belong to a different model version is worse
# than one that refuses to build.
missing=""
for f in vensim_run_configuration_parameter vensim_run_configuration_external \
         doc_parameter doc_external; do
    [ -e "$MODELS/$f" ] || missing="$missing  $MODELS/$f
"
done
for f in runners/vensim/vensim_savelist_export_results.lst \
         runners/vensim/vensim_convert_historical_deer_botg_csv_to_dataset.frm \
         results/runs/case1_parameter.csv results/runs/case2_parameter.csv \
         results/runs/case1_external.csv results/runs/case2_external.csv; do
    [ -f "$SOURCE/$f" ] || missing="$missing  $f
"
done
if [ -n "$missing" ]; then
    echo "error: these inputs are missing from $SOURCE:" >&2
    printf '%s' "$missing" >&2
    echo "" >&2
    echo "The run configurations and the pysdmdoc output live next to the" >&2
    echo "models, in $MODELS." >&2
    echo "" >&2
    echo "Export each case from the model version it belongs to:" >&2
    echo "  *_parameter.csv from the parameterised model (commit 3)" >&2
    echo "  *_external.csv  from the externalised model  (commit 4)" >&2
    exit 1
fi

if [ -e "$TARGET" ]; then
    [ "$FORCE" -eq 1 ] || {
        echo "error: $TARGET exists. Pass --force to rebuild it from scratch." >&2
        exit 1
    }
    rm -rf "$TARGET"
fi

mkdir -p "$TARGET"
git -C "$TARGET" init -q -b main

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

# stage <path>...  -- copy from the working tree into the history and add it
stage() {
    for path in "$@"; do
        [ -e "$SOURCE/$path" ] || { echo "error: missing in source: $path" >&2; exit 1; }
        mkdir -p "$TARGET/$(dirname "$path")"
        if [ -d "$SOURCE/$path" ]; then
            cp -R "$SOURCE/$path/." "$TARGET/$path/"
        else
            cp "$SOURCE/$path" "$TARGET/$path"
        fi
        # No -f: .gitignore decides what belongs in the history. A forced add
        # would quietly commit exactly the files the ignore rules exist to keep
        # out. What gets skipped is reported rather than swallowed.
        git -C "$TARGET" add -- "$path"
        skipped=$(git -C "$TARGET" ls-files --others --ignored --exclude-standard -- "$path" 2>/dev/null)
        if [ -n "$skipped" ]; then
            echo "  note: excluded by .gitignore, not committed:" >&2
            echo "$skipped" | sed 's/^/    /' >&2
        fi
    done
}

# stage_from <source> <target-path>  -- for inputs that live outside the
# repository working tree, such as the run configurations and the generated
# documentation next to the models. A directory replaces its target wholesale,
# so files from the previous stage do not linger.
stage_from() {
    local src="$1" dst="$2"
    [ -e "$src" ] || { echo "error: not found: $src" >&2; exit 1; }
    mkdir -p "$TARGET/$(dirname "$dst")"
    if [ -d "$src" ]; then
        rm -rf "${TARGET:?}/$dst"
        mkdir -p "$TARGET/$dst"
        cp -R "$src/." "$TARGET/$dst/"
    else
        cp "$src" "$TARGET/$dst"
    fi
    git -C "$TARGET" add -A -- "$dst"
}

# stage_model <file>  -- the model, always under the same name
stage_model() {
    mkdir -p "$TARGET/$(dirname "$MODEL_NAME")"
    cp "$1" "$TARGET/$MODEL_NAME"
    git -C "$TARGET" add -- "$MODEL_NAME"
}

# drop_keep <dir>...  -- a directory with real content no longer needs .gitkeep
drop_keep() {
    for dir in "$@"; do
        if git -C "$TARGET" ls-files --error-unmatch "$dir/.gitkeep" >/dev/null 2>&1; then
            git -C "$TARGET" rm -q --cached "$dir/.gitkeep"
            rm -f "$TARGET/$dir/.gitkeep"
        fi
    done
}

commit() {  # commit <tag> <subject> [body]
    local tag="$1" subject="$2" body="${3:-}"
    if [ -n "$body" ]; then
        git -C "$TARGET" commit -q -m "$subject" -m "$body"
    else
        git -C "$TARGET" commit -q -m "$subject"
    fi
    [ -n "$tag" ] && git -C "$TARGET" tag -f "$tag" >/dev/null
    printf '  %-22s %s\n' "$tag" "$subject"
}

echo "Building history in $TARGET"
echo

# ---------------------------------------------------------------------------
# 1 -- scaffold
# ---------------------------------------------------------------------------
stage README.md LICENSE LICENSES REUSE.toml CITATION.cff \
      .gitignore .gitattributes copier.yml template \
      scripts/check_template.sh \
      docs/git_workflow.md docs/kaibab_example.md \
      models/export/.gitkeep \
      models/config/lookups/.gitkeep models/config/parameters/.gitkeep \
      models/config/scenarios/.gitkeep models/config/timeseries/.gitkeep \
      runners/pysd/.gitkeep runners/stella/.gitkeep runners/vensim/.gitkeep \
      scripts/.gitkeep tests/.gitkeep \
      results/runs/.gitkeep results/figures/.gitkeep \
      docs/kaibab_ecosystem_report/views/.gitkeep \
      .github/workflows/reuse.yml
commit v0.1-scaffold "chore: repository scaffold, licensing and project template" \
"Directory layout, REUSE licensing, citation metadata and the Copier template.

.gitignore and .gitattributes belong in the first commit: introduced later,
'* text=auto' rewrites every file at once."

# ---------------------------------------------------------------------------
# 2 -- structure only
# ---------------------------------------------------------------------------
stage_model "$STOCK_FLOW"
stage docs/kaibab_variable_description.xlsx
commit v0.2-structure "feat: Kaibab stock-and-flow structure" \
"Three stocks and their flows, no parameter values yet.

This state is deliberately not runnable -- structure without parameters
computes nothing. The history documents model development, not a green main."

# ---------------------------------------------------------------------------
# 3 -- parameterised
# ---------------------------------------------------------------------------
stage_model "$PARAMETER"
stage runners/vensim/vensim_savelist_export_results.lst \
      results/runs/case1_parameter.csv results/runs/case2_parameter.csv
stage_from "$MODELS/vensim_run_configuration_parameter" \
           runners/vensim/vensim_run_configuration_parameter
stage_from "$MODELS/doc_parameter" docs/kaibab_ecosystem_report
drop_keep runners/vensim results/runs docs/kaibab_ecosystem_report/views
commit v0.3-parameterized "feat: parameterise the model, pin the simulation settings" \
"Values in place, 1900-1950, DT = 1/20 year, RK2. The model runs now, so this is
also the first commit with results: the .lst is the Vensim save list deciding
which variables get exported, and results/runs/*_parameter.csv is what came out.

    git diff --stat v0.2-structure v0.3-parameterized -- models/kaibab_ecosystem_model.mdl

About a third of that diff is the sketch section -- the coordinates of boxes on
the diagram. That unreadable diff is what the next commit exists to fix."

# ---------------------------------------------------------------------------
# 4 -- externalised, with the runner that reads it
# ---------------------------------------------------------------------------
stage_model "$EXTERNAL"
stage models/config/parameters \
      models/config/lookups models/config/timeseries \
      runners/pysd/run.py runners/pysd/rk_integrator.py runners/pysd/cin_loader.py \
      runners/vensim/vensim_convert_historical_deer_botg_csv_to_dataset.frm \
      results/runs/case1_external.csv results/runs/case2_external.csv \
      scripts/csv_to_cin.py scripts/vensim_csv.py scripts/compare_tools.sh \
      .github/workflows/simulate.yml \
      tests/test_rk_integrator.py tests/fixtures \
      docs/pysd_integration.md
stage_from "$MODELS/vensim_run_configuration_external" \
           runners/vensim/vensim_run_configuration_external
stage_from "$MODELS/doc_external" docs/kaibab_ecosystem_report
drop_keep models/config/parameters models/config/lookups models/config/timeseries runners/pysd tests
commit v0.4-config-external "refactor: move parameters, lookups and data out of the model" \
"Constants become ':NA:' and are supplied by models/config/parameters, the lookups
become stubs filled from models/config/lookups, and the historical series is read
from models/config/timeseries.

Shipped with the consumer, not without it: runners/pysd/run.py reads all three
forms. Moving values into files changes nothing until something reads them."

# ---------------------------------------------------------------------------
# 5 -- a scenario (this is the payoff)
# ---------------------------------------------------------------------------
stage models/config/scenarios/case2.cin
drop_keep models/config/scenarios
commit v0.5-scenario "feat: predator-removal scenario" \
"Four parameters in one file. The point is not that the diff is small -- editing
a value inside the .mdl would be small too -- but that the model file is
untouched:

    git diff v0.4-config-external v0.5-scenario -- models/kaibab_ecosystem_model.mdl

comes back empty. Every scenario provably runs the same structure.

Deliberately not on a branch. Nothing here needed isolating, reviewing or
running in parallel, and a merge commit would be noise around the one thing
this commit is meant to show. See docs/git_workflow.md for where branching
does earn its place."

# ---------------------------------------------------------------------------
# 6 -- the verification layer
# ---------------------------------------------------------------------------
stage results/reference \
      results/figures/results.pdf results/figures/results.png \
      tests/test_reference.py scripts/plot_results.py scripts/build_history.sh
drop_keep results/runs results/figures scripts
commit v0.6-verification "test: reference results and cross-tool comparison" \
"A committed baseline at annual resolution, and the test that replays each
scenario through PySD and checks it. Vensim is commercial: without this,
anyone without a licence can verify nothing."

# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
echo
echo "History:"
git -C "$TARGET" log --graph --oneline --decorate --all | sed 's/^/  /'
echo
echo "The teaching diff, commit 3 vs commit 4:"
printf '  model file, v0.2 -> v0.3: %s changed lines\n' \
    "$(git -C "$TARGET" diff --numstat v0.2-structure v0.3-parameterized -- "$MODEL_NAME" | awk '{print $1+$2}')"
printf '  scenario,   v0.4 -> v0.5: %s changed lines\n' \
    "$(git -C "$TARGET" diff --numstat v0.4-config-external v0.5-scenario | awk '{s+=$1+$2} END {print s}')"
echo
echo "Done. Review it, then move it into place or push it."
