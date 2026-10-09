# Implementation verification

Verified on 2026-10-09. This records the added teaching workflows and their preservation checks; it is not a claim of new Vensim or Stella native execution.

| Check | Result |
|---|---|
| Original scientific/site/test files | All 90 SHA-256 values match the semantic branch baseline `9bb1658a44223358ad2d4403bb307ba50292c002` |
| Stella import | All 19 files match revision `194a8b92e963920e95393accc7d5699348864d85` byte for byte; internal paths retained in `examples/stella-source/` |
| Existing native model tests | Existing Stella test file passes all 32 tests in the isolated source tree, including the previously conditional model checks |
| Python environments | Python 3.12 and 3.13 exercised locally; locked environments also checked on Ubuntu by the PR matrix |
| Installed package | Clean wheel installations outside the checkout run all four implementation/case combinations and compare each against its own reference |
| CSV interpretation | Existing readers retained; native headers/locale conventions covered by existing tests; 1,001-point Vensim states and 21-point historical observations remain separate; Stella Case 2 remains final-only |
| Numerical agreement | Existing Vensim annual comparison grid and 0.1%/5% case tolerances retained; Stella own-reference relative tolerance 1e-9 retained; no cross-tool equality requirement |
| RO-Crates | Each implementation/case can be packaged; hashes checked; portable rerun produces byte-identical PySD output; changed output is rejected |
| Jupyter | Both new notebooks execute on Python 3.12 and 3.13 with an explicitly selected kernel; source notebooks are not overwritten |
| Citation and metadata | CFF 1.2 schema valid; CodeMeta identity/version/authors consistent with the package; prepared Zenodo metadata contains no invented DOI |
| Semantic graph | Preserved Turtle and JSON-LD are isomorphic and conform to the existing SHACL shapes |
| Licensing | Clean committed snapshot passes REUSE 3.3, including font and vendor runtime attributions |
| Lecture | All 52 original topics mapped to 56 core slides plus six optional appendix slides; all 62 have notes and a workflow strip |
| Browser | All 62 desktop and narrow-screen layouts checked; arrows, M/Escape focus restoration and O overview work; 62 print pages without body/workflow overlap |
| Semantic routes | Root, workflows, NFDI4Ing use cases, model/concept/assignment neighborhoods, both workflow diagrams and saved notebook open in the combined preview |
| Publishing boundary | PR preview uploaded, deployment job skipped; live deployment still uses the original semantic commit |

The four root-suite Stella skips reflect the unchanged original test path checks. `tools/fair/check_stella.py` supplies the preserved snapshot in a temporary tree and runs those tests with no skips. The new package tests independently execute all four combinations. The legacy simulation workflow now installs the teaching package before running its full suite; its scientific commands and comparisons are unchanged.

`browser-verification.json` records the layout and route measurements. Screenshots were visually inspected, and full-resolution image links support reading dense diagrams. Print mode was checked in-browser; no native vendor application or physical printer was used. The design audit reported no findings.

Local `reuse lint` also sees the unrelated, untracked `docs/semantic/app 2.js`, which has no license header. It is untouched, excluded from the PR and excluded from the Pages artifact. License compliance was checked against the clean committed snapshot. Imported Stella whitespace and line endings are intentionally preserved rather than normalized.

External links were requested on the verification date. The automated HTTP client received 403 responses from the canonical FAIR4RS DOI and original textbook; these are access restrictions, not evidence that their identifiers are invalid. The ing.grid link was corrected to `https://www.inggrid.org/`. Betty's anonymous exact-name search returned no repositories and offered GitHub sign-in for wider results; authenticated enrichment was not tested. See the discovery exercise for direct reference links and the scope of that observed gap.

PR checks provide the current results and executed-notebook artifacts. See the [review PR](https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation/pull/1), [coverage map](../slides/coverage.md), [source manifests](stella-sources.json) and [rollout/release checklist](release.md). No merge, live deployment, release, webhook activation or DOI publication is performed during implementation.
