# Release and preservation

Version **0.7.0** was published on **2026-10-09**, from commit `e2e72ea61a251fead67a24fe624f47cc3e12d854`.

- [GitHub release v0.7.0](https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation/releases/tag/v0.7.0)
- [Zenodo record](https://zenodo.org/records/23267769)
- [Version DOI: 10.5281/zenodo.23267769](https://doi.org/10.5281/zenodo.23267769), identifying this immutable source snapshot
- [Concept DOI: 10.5281/zenodo.23267768](https://doi.org/10.5281/zenodo.23267768), identifying the project across archived versions

The official Zenodo application has organization access. Its active repository webhook listens for release events; Zenodo accepted the publication event with HTTP 202 and completed the deposit. The record lists Raphael Ginster, Matthias Papesch and Vasiliy Seibert, in that order. See [publication.json](publication.json) for the release commit, webhook and archive checksum.

The source archive retains the slides as they existed at release time. The live slides and handout received the DOI links in a subsequent documentation update. That update does not change the release tag or retroactively change the archived software. The presentation revision is recorded separately in [the slide source manifest](../slides/sources.json).

## Authors and organization membership

Both collaborators are already credited in CFF, CodeMeta, package and Zenodo metadata. Raphael Ginster's verified ORCID is [0000-0003-2394-7064](https://orcid.org/0000-0003-2394-7064). Matthias Papesch's ORCID remains blank at the repository owner's request because the same-name registry record could not be independently disambiguated. [authors.json](authors.json) records the research sources.

Matthias (`mpapesch`) has accepted his organization-owner invitation and is an active owner. Raphael (`rginster`) has an outstanding owner invitation, sent on 2026-10-09; he must accept it to become active. Authorship credit does not depend on invitation acceptance.

## Licensing and preservation

MIT applies to original code, CC BY 4.0 to original documentation, and CC BY-NC-SA 4.0 to model-derived artifacts, as mapped in `REUSE.toml`. The Zenodo description explains these separate terms and attributes the original *System Dynamics Learning Guide* to Mike Deaton and Rod MacDonald (2025).

Six GitHub checks passed on the released commit: Python 3.12 and 3.13 verification, simulation, REUSE, Pages build and deployment. Preserved models, configurations, reference tolerances and semantic-site files are unchanged.

Software Heritage ingestion must be checked separately; this release record makes no unverified SWHID claim.

## Future releases

1. Keep authors, versions, licenses and source attribution consistent across CFF, CodeMeta, package and `.zenodo.json` metadata. Zenodo uses `.zenodo.json` when both it and CFF are present.
2. Review the exact source commit and run the scientific, installed-package, notebook, metadata, preservation and site checks.
3. Create an explicitly targeted new release tag. Never move a published tag.
4. Verify webhook delivery, the completed Zenodo record, creators, licensing, archive checksum and DOI resolution.
5. Record the new version DOI and release commit in `publication.json`; update citation metadata, README, slides and handout after verifying publication. Preserve the project concept DOI.
6. Keep the presentation revision distinct from the archived software revision. Deploy the combined semantic root and slides through the main-only Pages workflow.

Official guidance: [enable repository](https://help.zenodo.org/docs/github/enable-repository/), [metadata precedence](https://help.zenodo.org/docs/github/describe-software/), [archive a GitHub release](https://help.zenodo.org/docs/github/archive-software/github-upload/).

## Sustainability

Agree scientific review, release management and support responsibilities with the collaborators. Organization ownership does not itself assign an issue-response commitment. Review supported Python versions, locks and deprecations with each release, preserving earlier artifacts and attribution.
