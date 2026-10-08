# Kaibab semantic atlas — review draft

Open `index.html` in a browser. It is a static, offline-capable explorer: no account, external scripts, remote fonts, or build server are required. The source links need access to the private GitHub repository. Notebook and figure source artifacts are available on the `codex/semantic-workflow-sources` repository branch. The explorer has not been deployed as a website.

The model combines concise literature interpretations with all 47 Vensim declarations and 50 main-branch files from commit `f156dcf37597c0587958f463985986f0ea91accf`. The revised Overview also includes the Stella declaration at commit `194a8b92e963920e95393accc7d5699348864d85`. This is a focused addition; a complete mapping of all Stella declarations is still pending. The diagram shows documented runs, not new simulations. Search can open review-note entities for known ambiguities and evidence gaps.

## Diagram interactions

The two tabs are **Semantic Model** (formerly Overview) and **Workflows**. Workflows is a scrolling document: a linked table of contents followed by both examples in order. Section links are bookmarkable, and “Explore diagram” opens a full pan-and-zoom view with a return link to the same section. Inline diagrams scroll horizontally on smaller screens.

Hover or keyboard-focus a node for its definition. Click scientific quantities, formulas and groups to explore their connections; file and variable nodes link directly to the pinned GitHub revision. Use search to explore a node’s connections. In the full canvas, drag the background to pan and use the wheel or +/− buttons to zoom. Neighborhood views show up to 28 neighbors and disclose omitted connections. The RDF exports retain all relationships.

## First workflow: set predator removal, simulate, and visualize

The worked sequence is `kaibab_ecosystem_model.mdl` → `case2.cin` → documented Case 2 simulation → `case2_external.csv` → a locally generated three-panel SVG. Numbered stages give the reading order; labelled arrows express actual semantic relationships, including supporting inputs and processing steps.

1. The model declares **Fraction Predators Killed per Year** in `1/Year` at line 143. Its declaration is `:NA:`: a value must be supplied externally.
2. `models/config/scenarios/case2.cin`, line 4, assigns **0.2/year**, overriding the baseline value 0. Case 2 also changes annual kills per predator (40 → 20), carrying-capacity horizon (2 → 4 years), and desired consumption (0.75 → 0.5). This is not a single-factor experiment.
3. The Vensim run instructions load the baseline parameters and lookup tables, then Case 2 overrides. Initial stocks come from the workbook. Simulation settings are 1900–1950, time step 0.05 year, RK2 midpoint.
4. The committed `results/runs/case2_external.csv` is the documented output. Original execution timestamps and exact Vensim version remain unknown. No new simulation was executed for this example.
5. `tools/build_workflow_figure.py` actually runs the pinned `scripts/plot_results.py` and `scripts/vensim_csv.py` against that pinned CSV, selecting deer, predators and forage. The figure node opens the commit-pinned source of `data/case2-workflow.svg` in GitHub. `data/workflow-figure.json` records the command, source revision, source hashes and output hash.

The workflow sequence is also an `rdf:Seq` in the RDF. Sequence membership itself makes no provenance claim. `sd:inputTo` is an explicitly declared local inverse of the existing `obo:RO_0002233` input relation. The original simulation retains `sd:documentedOutput`; the executed plotting activity uses `prov:used` and `prov:generated`. This separates a scientific task, its documented execution, and a new visualization of existing data.

## Second workflow: inspect results with Python / Jupyter

The repository already supplies a Python data reader (`scripts/vensim_csv.py`) and a PySD simulation runner (`runners/pysd/run.py`). No Jupyter notebook existed in the inspected source revision. The new [executed notebook](notebooks/inspect_results.ipynb) demonstrates the supported inspection path:

**Saved result CSVs → Python inspection → repository reader and notebook → five linked notebook cells → tables and comparison figure.**

The notebook verifies the reader and input hashes, inventories variables and units, preserves each time axis, builds a 2,002-row state table, computes sampled peaks and final values, and plots both cases. Each simulated state has 1,001 samples; the historical reference has 21. The reference stays separate and is never interpolated into the state table. Case 2 changes four parameters, so the comparison does not establish an isolated predator-removal effect.

Open the notebook through its repository link on the Workflows page, or open `docs/semantic/notebooks/inspect_results.ipynb` in a Python Jupyter environment with pandas and matplotlib. Start within the repository; the notebook locates the repository root. Saved tables and the inline figure are already included. The example is tied to the reviewed revision and checks inputs before execution. It writes its exported tables, report and SVG only under `docs/semantic/data/`.

The final notebook section shows an optional upstream PySD command for creating a new result. It uses the repository runner with the baseline parameters, lookup tables, reference time series and scenario overrides. That command was not executed for this inspection. The runner writes tidy CSV by default; the same reader can load it, but tidy exports lack unit metadata, which must be supplied from the model documentation.

### Notebook sections and source links

Both workflows use five numbered stages and descriptive action-sentence titles. The Python diagram puts only `vensim_csv.py` and `inspect_results.ipynb` immediately after the inspection activity. Five notebook sections follow, then the tables and SVG specified by cells 3–5.

| Code cell | Section | Result |
|---|---|---|
| 1 | Locate and check the source artifacts | Verified input hashes and setup |
| 2 | Read units and time axes | Variable inventory and separate time axes |
| 3 | Build the state table | pandas table exported as CSV |
| 4 | Inspect peaks and final values | Summary CSV and inspection report |
| 5 | Compare trajectories | Three-panel SVG and inline notebook figure |

Each cell node links to its heading in [one complete rendered notebook](notebooks/inspect_results.html). The view contains all five executed cells, saved tables and the inline figure, with a linked contents list and a return link to the workflow. The sole executable notebook is `notebooks/inspect_results.ipynb`; sections are parts of that artifact, not separate notebooks.

`tools/notebook_view.py` renders the saved notebook with nbconvert without executing it. The HTML uses the atlas stylesheet, works locally and offline, and needs no Jupyter account. The reader’s Git source link follows the workflow branch; explicit repository actions retain commit-pinned sources. The optional `notebooks/inspect_results.py` source view remains available. Validation compares rendered code, table contents and image bytes against the canonical notebook.

NFDI4Ing is a potential interactive execution environment, but no upload or authenticated launch has been tested. The read-only view does not claim to execute cells or provide a working service launch link.

The notebook and its sections are `prov:Plan` / `schema:CreativeWork` entities connected with `dcterms:hasPart`. The local `sd:specifiesOutput` relation describes what a code section writes; `prov:generated` records the observed generation on the executed activity separately. This keeps the diagram readable without attributing an execution event to a source file.

Notebook reading links open the rendered view; source links and the other artifact actions open repository sources. No download controls are offered. Generated-artifact links use `ARTIFACT_REVISION` in `tools/workflow_sources.py`; original model/input links retain their earlier reviewed revisions.

## Overview proposal

The overview uses MathModDB’s verified mathematical-model class (`Q68663`), formula (`Q96183`), quantity (`Q6534237`) and computational-task (`Q6534247`) identifiers. Local relationships remain explicitly declared `sd:` proposals; there is no assertion that they are MathModDB predicates. The three state-balance formulas are transcriptions of the declarations. A simulation task, setup plan, alternative tools and requested outputs are distinct from actual executions and generated datasets. Vensim and Stella source links preserve their separate revisions.

## Model architecture

- m4i 1.4.0 supplies `NumericalVariable`, `Method`, `Tool`, `Configuration`, `ProcessingStep` and their relationships.
- m4i reuses **PIMS-II `Assignment` and `Value`**, so these are correctly identified in the PIMS namespace, not invented as m4i classes. Assignments use `m4i:hasVariable` and `m4i:hasAssignedValue`; numerical literals are attached to values with `rdf:value`.
- SKOS vocabulary concepts are separate from implementation variables. Proposed preferred labels preserve original symbols as alternatives when they differ.
- The explicit local `sd:` extension covers stocks, flows, file selectors, model dependencies, and review notes. `vocabulary.ttl` declares it. No local ecological term is minted in the m4i namespace.
- Configuration assignments preserve both baseline and effective case-2 values. All four overrides are represented. Simulation-time controls are distinct from wall-clock execution timestamps.
- Documented run entities are reconstructions, not observed execution events. They use `sd:documentedOutput`, with evidence metadata, rather than asserting fully verified generation provenance.
- Model-native unit expressions preserve species counts and the thousand-acre scale. They are local QUDT-unit instances; alignment to standardized units and quantity kinds remains a review task.
- `sd:dependsOn` means a syntactic dependency, not causal polarity. Feedback-loop identities, signed causal assertions, and formal equation trees are future refinements.

## Files

| Artifact | Purpose |
|---|---|
| `model.ttl` / `model.jsonld` | Full RDF graph in equivalent serializations |
| `controlled-vocabulary.ttl` | 59 scientific and variable concepts, with definitions and sources |
| `vocabulary.ttl` | Local ontology extension |
| `shapes.ttl` | SHACL requirements for variables, files, bindings, assignments, values, and documented runs |
| `data/model.json` / `data/model.js` | Browser projection generated alongside RDF |
| `data/case2-workflow.svg` / `data/workflow-figure.json` | Generated figure and its input, software and output hashes |
| `notebooks/inspect_results.ipynb` / `inspect_results.py` | Executed notebook and matching Python source with linkable cell boundaries |
| `notebooks/inspect_results.html` | One complete read-only notebook view with links to its headings |
| `data/python-*` | Inspected state table, descriptive summary, comparison figure, report and source/output hashes |
| `validation.json` | Results of the local graph and source-integrity checks |

## Regenerate and validate

Install Graphviz (`dot` on PATH) to regenerate the precomputed diagrams. Use Python 3.11+ with the packages in `requirements.txt` installed:

```sh
python docs/semantic/tools/build_model.py
python docs/semantic/tools/build_tokens.py
python docs/semantic/tools/build_graphs.py
python docs/semantic/tools/validate_model.py
```

Before rebuilding the semantic model, generate its workflow figure once with `python docs/semantic/tools/build_workflow_figure.py` (requires the plotting dependencies in `requirements.txt`). The model builder checks the saved figure manifest against the pinned inputs and actual SVG. Regenerate the figure whenever its source revision or plotting selection changes. The semantic builder itself does not execute plotting or simulation.

Regenerate just the reading view with `python docs/semantic/tools/notebook_view.py`; this preserves all saved cells and outputs and updates the manifest without running a kernel.

Generate and execute the Python inspection example with `python docs/semantic/tools/build_inspection_notebook.py`. This runs five cells in a temporary Python kernel against a temporary copy of the pinned reader and CSVs, then saves the executed notebook and outputs. It does not alter the user's Jupyter configuration or execute a simulation. Commit regenerated artifacts, then update `ARTIFACT_REVISION` in `tools/workflow_sources.py` before rebuilding the semantic model and diagrams. The builder verifies that linked repository bytes match local artifacts. The validator checks notebook execution, source/output hashes, both RDF sequences, and independently recomputes statistics from the committed CSVs.

The builder reads the pinned commit with `git show`, not uncommitted source edits. Change `REV` deliberately when updating the source model. All file links, line anchors, hashes, and spreadsheet cells refer to that revision. Read `DESIGN.md` for visual and interaction contracts.

For an additional term-existence check, download the published m4i 1.4.0 Turtle serialization and pass its path as `--ontology`. The validation does not claim full OWL consistency checking. SHACL is an application profile, not a formal certification of scientific correctness.

## Identifiers and publication

Proposed namespace: `https://fair-systemdynamics.github.io/fair-hunter-prey-simulation/semantic/#`.

These are draft identifiers, not already registered or resolving. The fragment router selects entities now in the local preview. If GitHub Pages later serves the repository's `docs/` directory, this layout places the explorer at `/semantic/`. Hosting approval, repository visibility, identifier policy, and review of derived content precede deployment. No deployment workflow was added.

## Attribution

Deaton, Mike & MacDonald, Rod (2025), *System Dynamics Learning Guide*, James Madison University Libraries, Chapter 4 (current online §4.12, Figure 4.19). <https://pressbooks.lib.jmu.edu/sdlearningguide/>. CC BY-NC-SA 4.0. Model comments and definitions are derived from the repository's credited Kaibab reimplementation. The semantic datasets and generated browser data retain CC BY-NC-SA 4.0 for this review draft; viewer and tooling code are MIT. The ontology follows Metadata4Ing 1.4.0: <https://w3id.org/nfdi4ing/metadata4ing/>.
