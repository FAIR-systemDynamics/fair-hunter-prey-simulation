# FAIR4RS evidence and limits

| Principle | Evidence | Status / limit |
|---|---|---|
| F1, F1.1, F1.2 | Repository revisions, preserved teaching tags, separate model implementations and cases | Published [concept DOI](https://doi.org/10.5281/zenodo.23267768) and [version DOI](https://doi.org/10.5281/zenodo.23267769); see publication.json for the archived commit |
| F2, F3 | CITATION.cff, CodeMeta, source URLs, model metadata | Identifiers refer to actual repository objects |
| F4 | Public GitHub metadata; discovery exercise in Betty | External indexing must be observed, not assumed |
| A1, A1.1 | HTTPS sources, downloadable wheel/source, git installation | Native vendor workflows retain their access requirements |
| A1.2 | Authentication for contributions and hosted Jupyter | Public source inspection needs no repository account |
| A2 | Zenodo and Software Heritage preparation instructions | No deposit or archive ingestion claimed |
| I1 | MDL, XMILE, CSV readers, shared quantities and output interpretation | Identical file extensions do not imply identical schemas |
| I2 | Literature, ORCID, controlled vocabulary, semantic bindings | Local vocabulary and proposed relations remain a review draft |
| R1 | README, workflows, sources, runnable notebooks | Inspection and execution are separate activities |
| R1.1 | LICENSES and REUSE mappings | Vendor licenses are separate; model-derived content retains NC-SA |
| R1.2 | Git history, changelog, source manifests, execution records | Reconstructed native provenance is not newly observed execution |
| R2 | PySD and dependency versions, environment constraints | Separate tested locks cover Python 3.12 and 3.13; ranges alone would not lock transitive dependencies |
| R3 | Packaging, tests, reference comparisons, CFF/CodeMeta, RO-Crate | FAIR is an evidence-based assessment, not a certification badge |

The native simulation applications remain proprietary. Open artifacts and metadata improve reuse without claiming to change vendor licensing. An RO-Crate records what it contains; it does not guarantee future executability or recreate a missing vendor runtime.
