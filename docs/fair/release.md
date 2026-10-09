# Reviewed-branch release and Pages rollout

Version **0.7.0** is prepared for review. The first GitHub/Zenodo release will archive an explicitly approved commit on `codex/fair4rs-hunter-prey`. It does not require merging main or deploying Pages. [publication.json](publication.json) records observed integration, invitation and publication states; unset DOI fields mean no DOI has been issued.

## Before the release review

1. Finish the 63-slide lecture, original-to-adapted comparison, runnable practicals and checks. Retain all 52 original lessons, with five added case-study slides and six optional walkthroughs.
2. Keep authors in this order: Raphael Ginster, Matthias Papesch, Vasiliy Seibert. Retain verified ORCIDs and the Deaton/MacDonald source attribution. CFF, CodeMeta, package metadata and `.zenodo.json` must agree.
3. Preserve the inherited licensing. MIT applies to code, CC BY 4.0 to original documentation, and CC BY-NC-SA 4.0 to model-derived artifacts as recorded in REUSE.toml. The aggregate Zenodo record must explain these separate terms.
4. Verify protected-file hashes, byte-identical Stella imports, scientific tests without changed tolerances, Python 3.12/3.13 clean-package runs, notebooks, crates, slides and semantic routes.
5. Use the existing official Zenodo account and GitHub integration. Grant the app access to FAIR-systemDynamics when authorized, synchronize the repository list, enable this repository, and verify its active release webhook. Do not enable unrelated repositories.
6. Present the PR, preview and full source commit for review. **Wait for approval of that exact commit before creating a tag or release.** Approval of the implementation plan is not approval of an unseen release commit.

## Publish only the approved commit

1. Confirm that the approved SHA still identifies the reviewed source, all required checks passed, and `v0.7.0` does not already identify a different release.
2. Create the `v0.7.0` tag at the approved SHA and a GitHub release explicitly targeting it. Never accept an implicit main-branch target. Do not move the tag afterward.
3. Confirm delivery of the release event to Zenodo and successful ingestion. Inspect the archive, title, version, all three creators, references and licensing. A green webhook or a Git tag alone is not a DOI deposit.
4. Record the verified concept DOI and version DOI in `publication.json`, together with the released SHA, record URL, tag and verification date. If ingestion fails, record the actual error and repair it without inventing an identifier or silently repointing the tag.
5. In a follow-up commit on the same PR, add actual DOI badges and links to the README and lecture. Show the concept DOI for the project and the version DOI for the archived computation. Switch teaching installation examples to the verified release tag.
6. Record the presentation revision separately from the archived software revision. The follow-up documentation does not retroactively become part of the immutable archived source.
7. Verify badge rendering, DOI resolution, archived file checksums and a clean installation of the released version. Check Software Heritage ingestion separately and record an SWHID only when observed.

Zenodo uses `.zenodo.json` when both it and `CITATION.cff` are present. Keep the two consistent. Official guides: [enable repository](https://help.zenodo.org/docs/github/enable-repository/), [metadata precedence](https://help.zenodo.org/docs/github/describe-software/), [archive a GitHub release](https://help.zenodo.org/docs/github/archive-software/github-upload/).

## Collaborators

Organization-owner invitations were sent on 2026-10-09 to `rginster` (Raphael Ginster) and `mpapesch` (Matthias Papesch). Invitations remain pending until the recipients accept. Authorship credit does not depend on invitation acceptance.

## Later Pages rollout — outside this revision

1. Review the combined artifact: original semantic content at the root, lecture under `/slides/`.
2. Before a future merge, restrict the `github-pages` environment to deployments from **main**. This prevents the older semantic branch from replacing the combined site with a root-only artifact.
3. Merge only when separately authorized. The main-only publishing job then deploys the complete artifact. PR and release-branch checks create previews without deployment.
4. Verify the semantic root, existing hash routes, notebook links and slide route. For rollback, restore the prior complete artifact or revert the integration commit; never publish a slides-only artifact over the semantic root.

## Sustainability

Agree scientific review, release management and support responsibilities with the collaborators. Organization ownership does not itself assign an issue-response commitment. Review supported Python versions, locks and deprecations with each release; preserve earlier artifacts and attribution. Use an RDMO Software Management Plan to document agreed maintenance and end-of-support responsibilities.
