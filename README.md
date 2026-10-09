# fair-hunter-prey-simulation

[![FAIR teaching checks](https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation/actions/workflows/fair.yml/badge.svg?branch=codex%2Ffair4rs-hunter-prey)](https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation/actions/workflows/fair.yml)
[![Zenodo: awaiting first release](docs/slides/assets/img/zenodo-status.svg)](docs/fair/release.md)
[![Python 3.12 / 3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue)](pyproject.toml)
[![Licensing: REUSE](https://img.shields.io/badge/licensing-REUSE-green)](REUSE.toml)

**Authors:** [Raphael Ginster](https://github.com/rginster), [Matthias Papesch](https://github.com/mpapesch), [Vasiliy Seibert](https://github.com/VasiliySeibert).

A shared Kaibab scientific model, implemented in **Vensim** and **Stella Architect**, with **Case 1 and Case 2**. Open CSV inspection and independent **PySD** execution make the artifacts inspectable and reusable alongside the proprietary native workflows. Original model: [Deaton and MacDonald, *System Dynamics Learning Guide* (2025)](https://pressbooks.lib.jmu.edu/sdlearningguide/).

[Semantic model and vocabulary](https://fair-systemdynamics.github.io/fair-hunter-prey-simulation/) · [FAIR4RS teaching material](docs/fair/README.md) · [Review PR and Pages preview](https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation/pull/1) · [52-slide adaptation register](docs/slides/coverage.md)

The semantic site is live and unchanged. The revised slides are under review; `/slides/` will be published only after a future merge. The first Zenodo release requires review of its exact commit; no DOI is claimed before publication.

### Quick start

Use Python 3.12 or 3.13. This command installs the **moving review branch**; for an exact rerun, use the full commit shown in the PR or the commit-pinned installation command in its slide preview.

```sh
python -m pip install "fair-hunter-prey[teaching] @ git+https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation@codex/fair4rs-hunter-prey"
fair-hunter-prey inspect --output-dir out/inspection
fair-hunter-prey run --implementation stella --case case2 --output-dir out/stella-case2
fair-hunter-prey crate --run-dir out/stella-case2 --output-dir out/research-object
```

Inspection reads saved exports; `run` uses PySD and records the selected implementation and case. See the [four-combination example and locked environments](docs/fair/README.md). Native Stella Case 2 evidence contains final values only; the PySD trajectory is a separate computation.

Licensing is per file: MIT code, CC BY 4.0 documentation, and CC BY-NC-SA 4.0 model-derived material. See [REUSE.toml](REUSE.toml).

## Original nfdi4sd example and repository conventions

The collaborators’ original explanation follows. Its layout diagram is a **template illustration**, not an inventory of committed exports. This teaching edition preserves the Stella snapshot under `examples/stella-source/`; `.vpmx` and `.stmz` distributions remain options rather than completed exports.

> A reference repository layout, a git workflow, and a set of data-handling conventions for
> publishing system dynamics models in the NFDI context, so that others can actually re-run them.

System dynamics models are usually shared as a single file, e.g., an `.mdl` or `.stmx` file or a screenshot of
a stock-and-flow diagram in a paper. That file mixes model structure, parameter values, and
run settings into one artefact, which makes it hard to review, to version,
and to reproduce with a different tool. This repository is an answer to three questions:

1. **How should a system dynamics repository be structured?** → separate structure from numbers and
   from results: see [Repository layout](#repository-layout).
2. **How do you use git with a system dynamics model?** → what a diff actually looks like,
   which commits to make, and what belongs in `.gitignore`: see [`docs/git_workflow.md`](docs/git_workflow.md).
3. **How should the data be handled?** → parameters, lookups, scenarios, and reference time series
   as external, citable files: see [Data handling](#data-handling).

All three answers serve one goal: that the model is **F**indable, **A**ccessible,
**I**nteroperable, and **R**eusable in the sense the NFDI means under [FAIR](#fair).

The **Kaibab Plateau ecosystem model** serves as the worked example throughout. Here, we use it as an example,
but any system dynamics model should fit this structure. Details of the example model
are in [`docs/kaibab_example.md`](docs/kaibab_example.md).

## Repository layout

```
nfdi4sd/
├── README.md
├── LICENSE                                # licensing overview (multi-license)
├── copier.yml                             # template questions
├── template/                              # the Copier template
├── LICENSES/                              # full license texts (REUSE)
│   ├── CC-BY-4.0.txt
│   ├── CC-BY-NC-SA-4.0.txt
│   └── MIT.txt
├── REUSE.toml                             # which license applies to which path
├── CITATION.cff                           # authors, ORCIDs, version, DOI
├── codemeta.json                          # software metadata for Zenodo
├── CHANGELOG.md
├── Snakefile                              # snakemake workflow
│
├── models/
│   ├── kaibab_ecosystem.mdl               # Vensim model file
│   ├── kaibab_ecosystem.stmx              # Stella (?) model file
│   ├── export/                            # exported / published models
│   │   ├── kaibab_ecosystem.py            # exported PySD file
│   │   ├── kaibab_ecosystem.vpmx          # published Vensim binary file
│   │   └── kaibab_ecosystem.???           # published Stella (?) binary file
│   └── config/
│       ├── lookups/
│       │   ├── effect_deer_density_on_predator_births.cin
│       │   ├── effect_deer_density_on_predator_hunting_efficiency.cin
│       │   └── effect_forage_availability_on_consumption.cin
│       ├── parameters/
│       │   └── basic_parameters.csv       # basic parameter configuration
│       ├── scenarios/
│       │   └── case2.cin                  # scenario specific configuration
│       └── timeseries/
│           └── historical_deer_botg.csv   # behavior over time graph
│
├── runners/
│   ├── pysd/                              # run.py, rk_integrator.py, cin_loader.py,
│   │                                      #   xmile_support.py (Stella models)
│   ├── stella/                            
│   └── vensim/                            
│
├── scripts/
│   ├── compare_runs.py
│   ├── csv_to_cin.py                      # parameter CSV -> Vensim .cin
│   ├── plot_results.py                    
│   └── vensim_csv.py                      # helper for reading Vensim CSV exports
│
├── tests/                                 # tests to run
│
├── results/                               # versioned, except binary tool output
│   ├── reference/                         # committed baseline the tests check
│   ├── runs/                              # run output
│   └── figures/                           # plots
│
├── docs/
│   ├── git_workflow.md                    # commit plan / git with SD models
│   ├── kaibab_example.md                  # the worked example model
│   ├── kaibab_ecosystem_report/           # pysdmdoc documentation
│   │   ├── kaibab_ecosystem.html
│   │   └── views/                         # svg of every Vensim view
│   └── kaibab_variable_description.xlsx   # description of every model variable
│
├── .github/workflows/run_???.yml
├── .gitattributes                         # LF, binary markers
└── .gitignore
```

## Data handling

The layout encodes one rule: **`models/` holds structure, `models/config/` holds numbers, `results/`
holds what those two produce.**

| Folder | What goes there? |
|---|---|
| `models/` | Stocks, flows, equations, causal structure | 
| `models/export/` | Model exports generated from `models/` | 
| `models/config/` | Parameter values, lookups, scenarios, timeseries data | 
| `results/reference/` | A committed baseline the tests check against | 
| `results/` | Run output and plots | 

## FAIR

The NFDI's purpose is that research data are provided according to the FAIR
principles: **F**indable, **A**ccessible, **I**nteroperable, and **R**eusable.

### Findable

Machine-readable metadata in [`CITATION.cff`](CITATION.cff) (title, authors,
ORCIDs, keywords) which GitHub renders as a "Cite this repository" button and
Zenodo can read on release; where `.zenodo.json` is present, that file supplies the deposit metadata. Every scenario is a named file rather than a variant
buried in a model, so a result can be traced back to the inputs that produced
it.

### Accessible

Model source, metadata and many inputs are openly readable in this public git repository; workbooks, images and document exports retain their existing formats. The one part that would be inaccessible is
the *results*, since these are generated by commercial system dynamics software.
Therefore, [`results/reference/`](results/reference/) holds a committed baseline,
which can be read and compared against. The tools' binary run files (e.g., `*.vdfx`) 
are deliberately excluded: they are unreadable without the licence and would only pretend to be accessible.

### Interoperable

The model is kept as plain-text (e.g., `.mdl`), not as a binary. Everything the model
needs is in formats other tools can read: parameters and lookups as `.cin`,
time series and parameter sets as CSV. **The scientific configuration is shared, while each implementation retains its own input representation.** For example, [`runners/pysd/`](runners/pysd/) runs the Vensim model under PySD from exactly the files Vensim reads.

### Reusable

Licensing is per-file and machine-checkable via [REUSE](https://reuse.software/):
`reuse lint` either passes or names the file it cannot classify. Moreover, a run 
is named by which model and which configuration, and the
origin of the example model is credited in
[`docs/kaibab_example.md`](docs/kaibab_example.md). The numerics that a result
depends on are accessable without the commercial tools and
[`tests/test_reference.py`](tests/test_reference.py) checks that the committed
results still reproduce.

## Starting a new project from this template

This repository is the *worked example*. To start a new model repository with
the same structure but none of the example's content, use the
[Copier](https://copier.readthedocs.io/) template in [`template/`](template/):

```bash
pipx run copier copy gh:<org>/nfdi4sd my-new-model
```

It asks for the project name, authors and ORCIDs, which simulation tools you
use, and how your model is licensed, then generates the directory layout,
`CITATION.cff`, `REUSE.toml`, `LICENSE` and the git documentation.

## Working with git

The commit history of this repository is itself teaching material: it walks from an empty
structure to a fully externalised, scenario-driven model, one reviewable step at a time.
The workflow plan is documented in **[`docs/git_workflow.md`](docs/git_workflow.md)**.

Note that not every commit is a runnable state (see the note on the structure-only commit in that
document). This is deliberate and it is the one place where this repository departs from ordinary
software practice.

## Quick start

```bash
# A model that carries its own parameters needs nothing but itself
python runners/pysd/run.py models/kaibab_ecosystem.mdl -o results/runs/case1.csv

# A model whose data lives outside it takes the sources, in any order.
# Later inputs override earlier ones, as a stack of Vensim changes files does.
python runners/pysd/run.py models/kaibab_ecosystem.mdl \
    -d models/config/parameters/basic_parameters.cin \
    -d models/config/lookups/ \
    -d models/config/timeseries/historical_deer_botg.csv \
    -d models/config/scenarios/case2.cin \
    -o results/runs/case2.csv

# Plot whatever came out
python scripts/plot_results.py results/runs/case*.csv
```

The workbook the model reads itself (`GET XLS CONSTANTS`) needs no `-d`: the
model names it relative to its own location, and the runner reproduces that path.
That is the reason `models/config/` sits under `models/`: Vensim resolves file
references relative to the `.mdl`, so the data has to be reachable from there.

The runner dispatches each `-d` by what it is: `.cin` files give constants and
lookups, a `.csv` gives constants or a time series depending on its shape, an
`.xlsx` is placed where the model's own `GET XLS CONSTANTS` can find it, and a
directory expands to everything supported inside it.

The runner is tool-independent: a Stella model (`.stmx`) runs the same way,
from the parameter file Stella imports, and reproduces Stella's own export
(see [`docs/pysd_integration.md`](docs/pysd_integration.md#the-stella-model)).
The Stella model and its files live on the `stella` branch:

```bash
python runners/pysd/run.py models/kaibab_ecosystem_model.stmx \
    -d models/config/parameters/kaibab_ecosystem_parameters_stella_scenario2.csv \
    -d models/config/lookups/kaibab_ecosystem_lookups_stella.csv \
    -d models/config/timeseries/kaibab_ecosystem_historic_BOT_stella.csv \
    --layout stella \
    -o results/runs/stella_scenario2_pysd.csv
```

*Planned — Snakemake workflow:*


## Citing this software

Machine-readable citation metadata is located in [`CITATION.cff`](CITATION.cff). GitHub renders a "Cite this repository" button from it. Please cite the version you actually ran.

The example model is not ours: if you use it, **cite the original source** as given in
[`docs/kaibab_example.md`](docs/kaibab_example.md).

## License

This repository is **multi-licensed**, managed with [REUSE](https://reuse.software/).
Full texts in [`LICENSES/`](LICENSES/), machine-readable mapping in [`REUSE.toml`](REUSE.toml), and overview in [`LICENSE`](LICENSE). Verify with `reuse lint`.

| What | License |
|------|---------|
| Code — `runners/`, `scripts/`, `tests/`, `Snakefile`, `.github/` | **MIT** |
| Documentation — `README.md`, `docs/*.md` | **CC BY 4.0** |
| Kaibab example model and derivatives — `models/`, `models/config/`, `docs/kaibab_example.md` | **CC BY-NC-SA 4.0** |

The third row is inherited, not chosen: the example model reproduces text from a
CC BY-NC-SA 4.0 source, and ShareAlike carries the license over. **However, the structure and the
workflow are MIT and free of that restriction.**

## Acknowledgements

- Example model: Mike Deaton and Rod MacDonald, *System Dynamics Learning Guide*,
  James Madison University Libraries, 2025. <https://pressbooks.lib.jmu.edu/sdlearningguide/>
  Licensed CC BY-NC-SA 4.0.

## FAIR4RS lecture and open workflows

The [teaching guide](docs/fair/README.md) adds installable examples for both preserved implementations, saved-result inspection, and RO-Crate packaging. [Presentation source](docs/slides/) is prepared for `/slides/`; the existing semantic site keeps its current address. See the [evidence and limitations](docs/fair/evidence.md) and [release checklist](docs/fair/release.md). No Zenodo release has been published by this addition.
