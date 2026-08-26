# Versioning a system dynamics model with git

The plan for this repository's commit history. The history here is **teaching
material**: every commit is one step of model development.

## Configure Vensim first, or the diffs are unreadable

Before you commit a model you need to change some Vensim settings: **Model → Settings → File Format**. Without these, Vensim
writes changes into the model file on every save that nobody made. 

| Setting | Value | What it prevents |
|---|---|---|
| Equation order | Alphabetical by group | Vensim otherwise reorders equations arbitrarily, so the diff shows reshuffling instead of content |
| Equation format | Verbose | Expanded equations, so a change is actually visible in the diff |
| Model settings | Store user specific settings in a separate file | Keeps personal settings out of the shared model file |
| Override sketch zoom | Autofit to screen | Stops zoom level and viewport from being written into the model |
| Disable sketch recenter on edit | ticked | Vensim otherwise recentres the view while editing and records that |

Source: <https://vensim.com/documentation/svn_git.html>


## Which results belong in the repository

**Working output → the binary files stays out.** `*.vdfx` and `*.vdf` are
git-ignored. The text and image output in `results/` *is* versioned and saves anyone reading the repository from having to re-run the model to see the results. However, that convenience is not a substitute for being able to reproduce it.

**Reference results → committed**, in `results/reference/`. Anyone who clones this repository without a licence can never re-run the model. Without a committed reference they cannot check anything at all. Moreover, `tests/test_reference.py` compares a PySD run against those files.

**Results behind a publication → committed**, in `results/`. 

## The commit sequence

| Commit | Content | Tag |
|---|---|---|
| 1 | Directory structure, README, CITATION.cff, LICENSE, **.gitignore**, **.gitattributes** | `v0.1-scaffold` |
| 2 | Stock-and-flow structure, no parameters | `v0.2-structure` |
| 3 | Parameterised model, settings pinned (1900–1950, DT 1/20, RK2) | `v0.3-parameterized` |
| 4 | Parameters moved to `models/config/` | `v0.4-config-external` |
| 5 | Scenario case2 | `v0.5-scenario` |