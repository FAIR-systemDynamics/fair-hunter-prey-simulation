# FAIR4RS teaching example

The scientific specification and use cases are shared. Vensim and Stella Architect implement them differently. FAIR practices expose model sources, configurations, evidence and outputs while the native applications remain proprietary.

## Install and run

Use Python 3.12 or 3.13. From this repository:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -c environments/teaching-py312.txt -e '.[teaching,dev]'
fair-hunter-prey inspect --output-dir out/inspection
fair-hunter-prey run --implementation vensim --case case1 --output-dir out/vensim-case1
fair-hunter-prey run --implementation vensim --case case2 --output-dir out/vensim-case2
fair-hunter-prey run --implementation stella --case case1 --output-dir out/stella-case1
fair-hunter-prey run --implementation stella --case case2 --output-dir out/stella-case2
fair-hunter-prey crate --run-dir out/stella-case2 --output-dir out/stella-case2-crate
```

On Python 3.13 use `environments/teaching-py313.txt`. Constraints pin the teaching environment; `pyproject.toml` declares the public dependency contract. The build includes model resources, so an installed wheel works outside the source checkout. The slides' installation command pins the source revision embedded when the site is assembled. No PyPI publication is claimed.

```python
from fair_hunter_prey import run_example, inspect_results, create_crate
inspection = inspect_results('out/saved')
run = run_example('stella', 'case2', 'out/replay')
crate = create_crate('out/replay', 'out/crate')
```

The two required selectors identify a source implementation and a scientific case. All `run` commands use **PySD**, not a remote or local vendor application. Nonempty output folders are refused. Use a new folder for each execution.

## The two open workflows

1. Inspect committed CSVs using the existing Vensim/Stella readers, pandas and Matplotlib. This does not execute a simulation. Historical observations retain their time axis. Missing Stella variable units remain unspecified in the exported tables; consult the model documentation.
2. Translate and run a model copy using the existing PySD runner and numerical adapters. Vensim RK2 uses midpoint; Stella RK2 uses Heun and the established STEP handling. Compare each with its own reference, not with an assumed identical cross-tool trajectory.

Stella Case 2 is committed as final values only. The inspection never fabricates a trajectory. A newly computed trajectory is labeled as a PySD result, not a Stella export. Case 2 changes four parameters, so it is not a single-parameter experiment.

## Stella snapshot

`examples/stella-source/` preserves the internal relative paths and bytes of selected artifacts from the existing `stella` branch. `stella-sources.json` records the immutable revision and checksums. The bundle prevents Stella CSVs from being swept up by the original Vensim runner's directory expansion. No scientific file is rewritten.

## Validate

```sh
python -m pytest tests -q
python tools/fair/check_stella.py
python tools/fair/check_materials.py
cffconvert --validate
reuse lint
python -m build
python tools/fair/build_site.py --output-dir /tmp/fair-hunter-prey-site
```

The Stella test command stages a temporary tree containing the original test file and Stella snapshot, then runs the existing tests unchanged. It leaves the repository untouched. Use a fresh environment to install the built wheel and run all four combinations from a different directory.

See [FAIR evidence](evidence.md), [release preparation](release.md), [slide coverage](../slides/coverage.json), and the [existing semantic site](https://fair-systemdynamics.github.io/fair-hunter-prey-simulation/).

## Three practicals

1. **Discovery (12 minutes):** open [Betty Research Engine](https://software.nfdi4ing.de/), search the repository name, and inspect any returned metadata. Record an indexing gap if no exact result appears; then use the [repository](https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation), [citation record](../../CITATION.cff), [CodeMeta](../../codemeta.json), [scientific reference](https://pressbooks.lib.jmu.edu/sdlearningguide/) and [semantic model](https://fair-systemdynamics.github.io/fair-hunter-prey-simulation/). The exercise does not assume or claim an indexed result.
2. **Interoperability (14 minutes):** run [02_interoperability.ipynb](../../examples/fair/02_interoperability.ipynb) in the installed teaching environment. Inspect all four saved exports first, then execute both implementations and both cases through PySD.
3. **Reuse (14 minutes):** run [03_ro_crate.ipynb](../../examples/fair/03_ro_crate.ipynb). Inspect hashes and provenance, then use the crate's `reproduce.py` in a compatible environment. Select either implementation and case before executing the notebook.

For automated notebook verification, run `python tools/fair/execute_notebooks.py --output-dir out/executed-notebooks`. It explicitly selects the current Python interpreter as the kernel and writes executed notebooks to the new output folder. The source notebooks and scientific artifacts stay unchanged.

### Observed discovery status (2026-10-09)

The anonymous Betty / Research Software Finder search for `fair-hunter-prey-simulation` returned “No repositories found for your search” and offered GitHub sign-in for broader results. This is an observed gap in that anonymous search, not proof of absence from GitHub or every search source. Authenticated GitHub enrichment was not tested. The direct repository and metadata links above remain available. The [official service description](https://nfdi4ing.de/brse/) explains its federated sources and access requirements.

## Presentation review

The revised lecture retains all 52 reference slides in their original order, adds five case-study slides before the first FAIR block, and ends with six optional walkthroughs (63 total). The [content-level register](../slides/coverage.md) and [side-by-side comparison](../slides/comparison.html) record exact substitutions and reasons. The first v0.7.0 release will archive the reviewed branch commit without merging or deploying Pages.
