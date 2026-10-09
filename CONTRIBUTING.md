# Contributing

Open an issue describing the use case, or a focused pull request with its evidence and tests. Credit the original model and preserve REUSE licensing.

The scientific sources, configurations, readers, numerical adapters, references and semantic site are protected by `tests/fair-preservation.json`. This teaching addition does not authorize changing them. A future scientific change needs its own review, rationale and regenerated evidence; never relax reference tolerances to hide a regression.

Use conventional commit prefixes such as `feat:`, `fix:`, `docs:` and `test:`. Add a concise Unreleased changelog entry. Future versions follow Semantic Versioning for the public package API. Changes to scientific behavior also require an explicit model/provenance note, regardless of API compatibility.

Run `python -m pytest tests -q`, `python tools/fair/check_stella.py`, and `python tools/fair/check_materials.py`. Run REUSE and citation checks as described in `docs/fair/README.md`. Keep generated runs outside source directories.
