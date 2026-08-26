# Running the model with PySD

PySD 3.14 reads `kaibab_ecosystem_model.mdl` without modification.
Translation picks up the three stocks and the simulation settings from the
model file (1900–1950, DT = 0.05), so no settings have to be repeated in the
runner:

```python
import pysd
model = pysd.read_vensim("models/kaibab_ecosystem.mdl")
result = model.run(params={"Fraction Predators Killed per Year": 0.2})
```

## The externalised model

The externalised model takes every parameter out of the model file.

| Mechanism in Vensim | Used for | PySD |
|---|---|---|
| `= :NA:` | constants, supplied by a `.cin` at run time | **works**: translates, value comes from `params` |
| Lookups reduced to a placeholder `[(0,0)-(10,10)],(0,0),(1,0)` | the three effect table functions | **works**: supply a `pandas.Series` via `params` |
| `GET XLS CONSTANTS('config/parameters/initial_stock_parameters.xlsx', …)` | the three initial stock values | **works**: see below |

### Reading a workbook: the path has to be reproduced, not the file

Vensim resolves a file reference **relative to the model**, which is why the
model sits at `models/` with `models/config/` beneath it: `config/parameters/…`
has to be reachable from where the `.mdl` lives.

`runners/pysd/run.py` reads the references out of the model and places each file at exactly the referenced relative path inside its work directory.

### One change is still needed before PySD will take the file

`Historical Deer BOT` is declared with a unit and a comment but no equation, since it is a 
data variable. Vensim accepts that for a variable fed entirely from a dataset. PySD's grammar
does not. Therefore, the runner patches a **copy** and reports every patch on stderr.

## Standard PySD integrates with Euler only

`Model._integrate_step` calls `Model._euler_step`, and there is no switch. The
model should be simulated with **RK2** (see `docs/kaibab_example.md`). Therefore, `runners/pysd/rk_integrator.py` replaces `_integrate_step` on a model instance:

```python
import pysd
from rk_integrator import attach

model = attach(pysd.read_vensim("model.mdl"), "rk2")
result = model.run()
```

Methods: `euler`, `rk2-midpoint` (alias `rk2`), `rk2-heun`, `rk4`.
