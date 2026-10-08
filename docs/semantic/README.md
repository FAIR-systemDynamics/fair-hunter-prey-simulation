# Kaibab semantic atlas — review draft

Open `index.html` in a browser. It is a static, offline-capable explorer: no account, external scripts, remote fonts, or build server are required. The source links need access to the private GitHub repository. Nothing has been published.

The model combines concise literature interpretations with all 47 Vensim declarations and 50 main-branch files from commit `f156dcf37597c0587958f463985986f0ea91accf`. The revised Overview also includes the Stella declaration at commit `194a8b92e963920e95393accc7d5699348864d85`. This is a focused addition; a complete mapping of all Stella declarations is still pending. The diagram shows documented runs, not new simulations. Search can open review-note entities for known ambiguities and evidence gaps.

## Diagram interactions

Hover or keyboard-focus a node for its definition. Click scientific quantities, formulas and groups to explore their connections; file and variable nodes link directly to the pinned GitHub revision. Use search to explore a node’s connections, drag the background to pan, and use the wheel or +/− buttons to zoom. The four curated views show subsets of the same graph; neighborhood views show up to 28 neighbors and disclose omitted connections. The RDF exports retain all relationships.

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
| `validation.json` | Results of the local graph and source-integrity checks |

## Regenerate and validate

Install Graphviz (`dot` on PATH) to regenerate the precomputed diagrams. Use Python 3.10+ with `rdflib`, `openpyxl`, and `pyshacl` installed:

```sh
python docs/semantic/tools/build_model.py
python docs/semantic/tools/build_tokens.py
python docs/semantic/tools/build_graphs.py
python docs/semantic/tools/validate_model.py
```

The builder reads the pinned commit with `git show`, not uncommitted source edits. Change `REV` deliberately when updating the source model. All file links, line anchors, hashes, and spreadsheet cells refer to that revision. Read `DESIGN.md` for visual and interaction contracts.

For an additional term-existence check, download the published m4i 1.4.0 Turtle serialization and pass its path as `--ontology`. The validation does not claim full OWL consistency checking. SHACL is an application profile, not a formal certification of scientific correctness.

## Identifiers and publication

Proposed namespace: `https://fair-systemdynamics.github.io/fair-hunter-prey-simulation/semantic/#`.

These are draft identifiers, not already registered or resolving. The fragment router selects entities now in the local preview. If GitHub Pages later serves the repository's `docs/` directory, this layout places the explorer at `/semantic/`. Hosting approval, repository visibility, identifier policy, and review of derived content precede deployment. No deployment workflow was added.

## Attribution

Deaton, Mike & MacDonald, Rod (2025), *System Dynamics Learning Guide*, James Madison University Libraries, Chapter 4 (current online §4.12, Figure 4.19). <https://pressbooks.lib.jmu.edu/sdlearningguide/>. CC BY-NC-SA 4.0. Model comments and definitions are derived from the repository's credited Kaibab reimplementation. The semantic datasets and generated browser data retain CC BY-NC-SA 4.0 for this review draft; viewer and tooling code are MIT. The ontology follows Metadata4Ing 1.4.0: <https://w3id.org/nfdi4ing/metadata4ing/>.
