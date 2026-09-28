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

## The Stella model

`runners/pysd/run.py` is tool-independent: it also runs a Stella model, from
the same parameter files Stella imports. The Kaibab Stella model, its
parameter files and Stella's exports live on the `stella` branch, where this
runs it:

```bash
python runners/pysd/run.py models/kaibab_ecosystem_model.stmx \
    -d models/config/parameters/kaibab_ecosystem_parameters_stella_scenario2.csv \
    -d models/config/lookups/kaibab_ecosystem_lookups_stella.csv \
    -d models/config/timeseries/kaibab_ecosystem_historic_BOT_stella.csv \
    --layout stella -o results/runs/stella_scenario2_pysd.csv
```

These are the files Stella imports: the parameters, the graphical functions
and the reference mode, each as Stella writes them. Run this way, the result
reproduces Stella's own export,
`results/kaibab_ecosystem_results_stella_scenario{1,2}.csv`. Scenario 1 is
exported as the full run, scenario 2 as final values only, and both are
compared in whatever form they were exported. The largest relative deviation
over the 1001 time points of each run, measured when both were exported as
full runs:

| | Deer Population | Forage Biomass | Predator Population |
|---|---|---|---|
| Scenario 1 | 1.3e-12 | 1.6e-12 | 5.1e-13 |
| Scenario 2 | 4.6e-12 | 3.6e-12 | 4.7e-12 |

`tests/test_stella.py` checks this on every run of the test suite where the
Stella files are present, so the Stella results can be verified without a
Stella licence. The mechanics below are also tested on
`tests/fixtures/stella_minimal.stmx`, a small Stella model that ships with the
tests, so they are checked on every branch. Four things had to
be right for that, and none of them is visible in Stella's user interface:

**Stella's RK2 is Heun's method.** The model file says only `method="RK2"`.
Vensim's RK2 is the midpoint rule, and under it the Stella run is reproduced
to no better than 3e-6. Under Heun's method it is reproduced to machine
precision. For a `.stmx` the runner takes the method from the file and reads
Stella's RK2 as `rk2-heun`. `--method` overrides it.

**Stella holds `STEP` for a whole time step.** It evaluates `STEP` once at the
start of each DT and keeps the value through every Runge-Kutta stage. A plain
Runge-Kutta re-evaluates it per stage, so the step switches on one stage early
and follows the stage's trial state. In scenario 2 that alone leaves the final
deer population 22% off Stella's. `rk_integrator.attach(model, method,
hold=[...])` holds the named components, and the runner names every variable
whose equation uses `STEP`.

**A graphical function takes its table from the model, not from `params`.**
PySD builds a Stella graphical function as a function of its input. A table
handed to `model.run(params=...)` would replace it by a time series indexed by
*time*, and the run is wrong from the first step. The runner writes the
table's points into the model copy instead, which is what Stella's import
does.

**A value for a stock is its initial value.** Stella's parameter file sets
`Forage Biomass`, a stock. Given to PySD as a parameter, the stock would become
a constant. The runner passes it as the initial condition instead.

Two things are rewritten in the copy of the model, and reported on stderr:
Stella's safe division `a // b`, which PySD's grammar rejects, becomes
`SAFEDIV(a, b)`, and forms such as `ELSE IF`, `MOD` in capitals and `{notes}`
inside an equation are put into the form PySD reads. Stella's parameter and
export tables use `;` and decimal commas on a German system. Both are read as
they are, as are the `,` and `.` Stella writes elsewhere, and `--layout
stella` writes a run in the same form, with `--decimal-comma` for the German
one, so it can be compared with Stella's export cell by cell. None of
Stella's tables has a header row, which is how they are told apart from the
`variable,value` tables of the Vensim side. A headerless file is also why
they need their own reader: `pandas.read_csv` would take the first
parameter for the header and drop it without a word.

Only the features this model uses were checked against Stella. PySD's XMILE
reader has no support for modules, conveyors, queues or ovens. `PULSE` and
`RAMP` are not held like `STEP`, because no Stella export was available to
check them against.

