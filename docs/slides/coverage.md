# Reference lecture coverage

All 52 reference topics map to 56 core slides plus six optional screenshot walkthroughs.

| Original | Original topic | Adapted slide |
|---|---|---|
| 1 | Research Software that others can find, trust and run. | 1: [FAIR research with proprietary simulation tools](index.html#/title) |
| 2 | Four lectures, one story | 2: [Research data and research software](index.html#/recap) |
| 3 | Agenda · 3 × theory ↔ 3 × practical | 3: [Today’s route through the example](index.html#/agenda) |
| 4 | Why make research software FAIR? | 4: [What a future collaborator needs](index.html#/why-fair) |
| 5 | One repo, running through every slide | 5: [The scientific specification comes first](index.html#/shared-specification) |
| 6 | Findable & Accessible research software | 10: [Findable & Accessible](index.html#/findable-accessible) |
| 7 | F1 · Globally unique and persistent identifier F1 F1.1 F1.2 | 11: [F1: identify the research object](index.html#/f1) |
| 8 | F1 · A DOI is a promise , not a URL F1 | 12: [A release can trigger a Zenodo deposit](index.html#/zenodo-webhook) |
| 9 | One project, many versions — each citable F1.1 F1.2 | 13: [Project identity and version identity](index.html#/version-identifiers) |
| 10 | F2 · F3 · F4 · rich, linked, harvestable metadata F2 F3 F4 | 14: [F2–F4: metadata that points to evidence](index.html#/metadata-principles) |
| 11 | Machines can only find what they can read F2 F3 F4 | 15: [Citation metadata and software metadata](index.html#/citation-codemeta) |
| 12 | A1 · A1.1 · retrievable via a standardized protocol A1 A1.1 | 16: [A1: retrieve the described artifact](index.html#/access-protocols) |
| 13 | Open, free, universally implementable A1 A1.1 | 17: [Retrieve source or install a pinned snapshot](index.html#/retrieve-install) |
| 14 | A1.2 · auth is a feature , not a gate A1.2 | 18: [A1.2: authentication where needed](index.html#/authentication) |
| 15 | Authentication, where genuinely necessary A1.2 | 19: [Access is different for each use case](index.html#/access-boundaries) |
| 16 | A2 · metadata outlives the software A2 | 20: [A2: preserve the record of the research](index.html#/persistent-metadata) |
| 17 | Metadata outlives the software A2 | 21: [Zenodo and Software Heritage](index.html#/archives) |
| 18 | F + A · the minimum viable artefacts | 22: [Findable and accessible evidence](index.html#/fa-recap) |
| 19 | Practical 1 · Discover research software | 23: [Practical 1: discover the model](index.html#/practical1) |
| 20 | Find DuMux in 14 minutes | 24: [Search, inspect, and follow the evidence](index.html#/discover) |
| 21 | What made DuMux findable? | 25: [What could you identify without asking the authors?](index.html#/discovery-reflection) |
| 22 | Interoperable research software | 26: [Interoperable](index.html#/interoperable) |
| 23 | I1 · read, write, exchange via community standards I1 | 27: [I1: exchange data with explicit meaning](index.html#/i1) |
| 24 | Open formats > bespoke files I1 | 28: [“CSV” is not a complete data specification](index.html#/formats) |
| 25 | Example · OpenAPI beats a README I1 | 29: [An explicit interface contract](index.html#/api-example) |
| 26 | I2 · qualified references to other objects I2 | 30: [I2: qualified references to other objects](index.html#/i2) |
| 27 | "Alice" vs "ORCID 0000-0001-…" I2 | 31: [Trace a concept through both implementations](index.html#/qualified-references) |
| 28 | awesome-sim/codemeta.json — line by line I2 | 32: [Software metadata connects the artifact](index.html#/codemeta-references) |
| 29 | Controlled vocabularies eliminate ambiguity · and give credit I2 | 33: [One concept, separate declarations and assignments](index.html#/controlled-vocabulary) |
| 30 | Dependencies are also qualified references I2 | 34: [Dependency constraints and tested environments](index.html#/dependencies) |
| 31 | pyproject.toml · from source to installed package I2 | 35: [Installable without reorganizing the model](index.html#/packaging) |
| 32 | Practical 2 · Test interoperability | 36: [Practical 2: inspect, then execute](index.html#/practical2) |
| 33 | Install, run, break, understand | 37: [Open inspection before independent execution](index.html#/inspect-run) |
| 34 | Why I2 (qualified dependencies) matters | 38: [What made the exchange work?](index.html#/interoperability-reflection) |
| 35 | Reusable research software | 39: [Reusable](index.html#/reusable) |
| 36 | R1 · R1.1 · R1.2 · describe, license, trace R1 R1.1 R1.2 | 40: [R1: describe, license, and trace](index.html#/r1) |
| 37 | Documentation is layered R1 | 41: [Documentation at each level](index.html#/documentation) |
| 38 | No license ≠ public domain R1.1 | 42: [The licenses travel with the artifacts](index.html#/licenses) |
| 39 | Who · what · when · why — for free R1.2 | 43: [A configuration is not an execution](index.html#/provenance) |
| 40 | R2 · qualified references to other software R2 | 44: [R2: references to other software](index.html#/r2) |
| 41 | Pin the whole world, not just the code R2 | 45: [Three levels of environment description](index.html#/environments) |
| 42 | R3 · meet domain-relevant community standards R3 | 46: [R3: community standards with evidence](index.html#/r3) |
| 43 | Let CI answer "does it still run?" R3 | 47: [CI protects the scientific example](index.html#/ci) |
| 44 | Write the sustainability plan before the code rots | 48: [A maintenance plan for the whole workflow](index.html#/sustainability) |
| 45 | R · the smallest thing that could break you | 49: [What would a missing artifact prevent?](index.html#/reuse-recap) |
| 46 | RO-Crate · research object in one container R | 50: [An RO-Crate packages a research object](index.html#/ro-crate) |
| 47 | Practical 3 · Capture reusability via RO-Crate | 51: [Practical 3: package an actual run](index.html#/practical3) |
| 48 | Package awesome-sim as a Research Object | 52: [Package the result you actually produced](index.html#/crate-exercise) |
| 49 | The R in FAIR4RS · Reusability across time | 53: [What travels with this result?](index.html#/crate-reflection) |
| 50 | The FAIR4RS checklist — one page | 54: [A FAIR4RS evidence checklist](index.html#/checklist) |
| 51 | The services you touched today | 55: [Services supporting the workflow](index.html#/services) |
| 52 | Your repo, next week — FAIR4RS-shaped. | 56: [Shared science. Traceable implementations.](index.html#/discussion) |
