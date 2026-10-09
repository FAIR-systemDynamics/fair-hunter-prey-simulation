# Release preparation and Pages rollout

This PR does not create a release, enable a webhook, publish a DOI, or change the live Pages environment.

## Review and Pages

1. Review the preserved semantic-site commits and the additive FAIR changes in the PR to `main`.
2. Inspect the `pages-preview` workflow artifact and verification results. The preview includes the current semantic root plus `/slides/`.
3. At rollout, restrict the `github-pages` environment's allowed deployment branch to `main`. This prevents the older semantic branch from publishing its root-only artifact.
4. Merge only after review. The main-only workflow deploys the combined artifact. Verify old root, hash routes, notebook links and `/slides/`.
5. For rollback, restore the prior complete Pages artifact or revert the integration commit. Do not publish a slides-only artifact over the semantic root.

## First software release

1. Confirm author information and the package API. Keep unknown ORCIDs absent.
2. Choose a release version, update package/CFF/CodeMeta consistently, and move the relevant Unreleased notes into a dated changelog section. Preserve historical teaching tags.
3. Validate licenses, metadata, clean wheel installation, notebooks, reference comparisons and the site.
4. Review `.zenodo.json`. It describes the bundled research object with CC BY-NC-SA 4.0 and explicitly preserves the separate code/documentation licenses in REUSE.toml. Do not label the whole model MIT.
5. Connect the repository in Zenodo's GitHub settings and confirm the release webhook. This is a maintainer action and is **not performed by this PR**.
6. Publish the approved GitHub release. Confirm that Zenodo actually ingests it before recording its concept DOI and version DOI. A tag alone is not a deposit.
7. Update citation metadata, badges and teaching links using the verified record. Cite the version used for a computation. Do not fabricate identifiers or silently mutate an archived snapshot.
8. Check Software Heritage ingestion separately and record a verified SWHID only when available.

Official instructions: https://help.zenodo.org/docs/github/enable-repository/

## Sustainability

Review roles are the repository's existing maintainers; this document does not assign duties or service-level promises to collaborators. Review the Python support matrix and lock files with each release. Record deprecations in the changelog, retain prior artifacts, and use an RDMO Software Management Plan to agree maintenance, archival and end-of-support responsibilities.
