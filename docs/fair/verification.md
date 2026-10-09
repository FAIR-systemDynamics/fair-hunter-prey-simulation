# Implementation verification

Verified on 2026-10-09. This records the added teaching workflows and their preservation checks; it is not a claim of new Vensim or Stella native execution.

| Check | Result |
|---|---|
| Original scientific/site/test files | All 90 SHA-256 values match the semantic branch baseline `9bb1658a44223358ad2d4403bb307ba50292c002` |
| Stella import | All 19 files match revision `194a8b92e963920e95393accc7d5699348864d85` byte for byte; internal paths retained in `examples/stella-source/` |
| Existing native model tests | Existing Stella test file passes all 32 tests in the isolated source tree, including the previously conditional model checks |
| Python environments | Python 3.12 and 3.13 each pass 56 tests; the four expected path-conditional Stella skips are covered by the isolated 32-test Stella run. The PR matrix repeats the checks on Ubuntu |
| Installed package | The 0.7.0 wheel, installed outside the checkout on both Python versions, passes all nine installed-package execution, CSV and RO-Crate checks (four combinations per interpreter) |
| CSV interpretation | Existing readers retained; native headers/locale conventions covered by existing tests; 1,001-point Vensim states and 21-point historical observations remain separate; Stella Case 2 remains final-only |
| Numerical agreement | Existing Vensim annual comparison grid and 0.1%/5% case tolerances retained; Stella own-reference relative tolerance 1e-9 retained; no cross-tool equality requirement |
| RO-Crates | Each implementation/case can be packaged; hashes checked; portable rerun produces byte-identical PySD output; changed output is rejected |
| Jupyter | Both new notebooks execute on Python 3.12 and 3.13 with an explicitly selected kernel; source notebooks are not overwritten |
| Citation and metadata | CFF 1.2 schema valid; CodeMeta identity/version/authors consistent with the package; Zenodo publication verified with all three creators; DOI identifiers recorded in publication.json |
| Semantic graph | Preserved Turtle and JSON-LD are isomorphic and conform to the existing SHACL shapes |
| Licensing | Clean committed snapshot passes REUSE 3.3, including font and vendor runtime attributions |
| Lecture | All 52 original slides retained in order from e354ef2, plus five labelled case-study slides and six appendix slides; all 63 have notes and a compact workflow. Exact substitutions and 104 paired screenshots are in the comparison gallery |
| Browser | All 63 desktop (1280 × 800) and narrow-screen (390 px) layouts checked; M/Escape focus restoration, O overview and arrow navigation checked; 63 Reveal print pages without overflow |
| Semantic routes | All 399 generated graph views, 26 reachable navigation routes, both workflow diagrams and the saved notebook render in the combined preview |
| Publishing boundary | The reviewed source was merged and deployed, then archived as v0.7.0; the follow-up documentation update adds the verified DOI links |

The four root-suite Stella skips reflect the unchanged original test path checks. `tools/fair/check_stella.py` supplies the preserved snapshot in a temporary tree and runs those tests with no skips. The new package tests independently execute all four combinations. The legacy simulation workflow now installs the teaching package before running its full suite; its scientific commands and comparisons are unchanged.

`browser-verification.json` records the layout and route measurements. Screenshots were visually inspected, and full-resolution image links support reading dense diagrams. All 63 notes are embedded and the notes plugin loads; the separate S-key presenter popup could not be visually verified in the in-app browser. Print mode was checked in-browser; no native vendor application or physical printer was used. The design audit reported no findings.

Local `reuse lint` also sees the unrelated, untracked `docs/semantic/app 2.js`, which has no license header. It is untouched, excluded from the PR and excluded from the Pages artifact. License compliance was checked against the clean committed snapshot. Imported Stella whitespace and line endings are intentionally preserved rather than normalized.

External links were requested on the verification date. The automated HTTP client received 403 responses from the canonical FAIR4RS DOI and original textbook; these are access restrictions, not evidence that their identifiers are invalid. The ing.grid link was corrected to `https://www.inggrid.org/`; the retired RDA working-group link now targets its official outputs page. The 108-link check found the textbook HTTP client restriction (403); the unpublished slides link was changed to the current preview. Betty's anonymous exact-name search returned no repositories and offered GitHub sign-in for wider results; authenticated enrichment was not tested. See the discovery exercise for direct reference links and the scope of that observed gap.

PR checks provide the current results and executed-notebook artifacts. See the [review PR](https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation/pull/1), [coverage map](../slides/coverage.md), [source manifests](stella-sources.json) and [rollout/release checklist](release.md). The reviewed source is merged and live. Matthias is an active organization owner; Raphael’s owner invitation remains pending. Zenodo organization access was explicitly approved and the release webhook archived v0.7.0. See publication.json for the observed state and exact archived commit.

## Reference fidelity review

The pinned reference HTML and both original theme stylesheets are preserved. Checks compare the original order, all layout classes and all principle quotations, and require exact substitution reasons. The motivation, repository overview, six image4 dividers, two image3 title compositions, changelog, metadata examples, OpenAPI illustration, packaging steps and printable checklist are retained. The gallery shows every original/adapted pair; a title/topic match alone is not accepted as coverage.

The 63-page [visual review PDF](../slides/handout.pdf) was rendered back to images and inspected. Its image-based pages retain the presentation composition and clickable links; the HTML deck provides selectable text, notes and native browser printing. The refreshed notebook screenshot comes from the successful Python 3.13 branch CI run at `ca6c7c85df3335e7197b1ef1bfd75af2ea41a33a`, with actual PySD execution provenance.

## Published archive and DOI update

On 2026-10-09, Zenodo published version DOI `10.5281/zenodo.23267769` and concept DOI `10.5281/zenodo.23267768`. Both resolve successfully. The downloaded ZIP matches its published MD5 checksum, and all 345 file contents match release commit `e2e72ea61a251fead67a24fe624f47cc3e12d854`. The public record contains all three authors in the required order, Raphael’s verified ORCID, and the mixed-license explanation. Matthias’s ORCID remains unset as requested.

Thirteen slides changed in the DOI documentation update; all were rendered at the original 1280 × 800 size and inspected. The comparison captures and 63-page handout were refreshed, with clickable concept and version DOI annotations. The immutable software archive retains the original pre-DOI slide snapshot.
