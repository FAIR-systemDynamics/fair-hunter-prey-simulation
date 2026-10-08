# Generated from inspect_results.ipynb; edit the notebook builder to regenerate.
# Cell numbers below match the executed notebook.

# %% [markdown]
# # Inspect Kaibab results with Python
#
# This new example uses the repository's existing CSV reader and committed Case 1
# and Case 2 results. Run the cells in order in Jupyter with **pandas** and
# **matplotlib** installed. Start Jupyter anywhere inside the repository.
#
# **No simulation is run.** Case 2 changes four parameters, so this comparison
# does not isolate the effect of predator removal. The historical deer series is
# a repository reference curve; its primary observational provenance is unresolved.
#
# The path is: **CSV files → repository reader → pandas tables → inspection → plot**.
# The reader matters: each state has 1,001 time points, while the historical
# reference has its own 21-point time axis. We preserve those separate axes.
#
# ## Contents
#
# 1. Locate and check the source artifacts — code cell 1.
# 2. Read the data without losing units or time axes — code cell 2.
# 3. Build a table for the three simulated states — code cell 3.
# 4. Inspect peaks and final values — code cell 4.
# 5. Compare trajectories on their own axes — code cell 5.
#
# The companion [Python source](inspect_results.py) contains the same numbered
# cells, with stable GitHub line links used by the semantic model.

# %% [markdown]
# ## 1. Locate and check the source artifacts

# %% Cell 1: Locate and check the source artifacts
# Jupyter: %matplotlib inline
from pathlib import Path
import hashlib
import json
import sys
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

ROOT = next((p for p in (Path.cwd(), *Path.cwd().parents)
             if (p / "scripts/vensim_csv.py").exists()
             and (p / "results/runs/case2_external.csv").exists()), None)
if ROOT is None:
    raise FileNotFoundError("Start this notebook from a folder inside the Kaibab repository.")
REVISION = 'f156dcf37597c0587958f463985986f0ea91accf'
EXPECTED_HASHES = {'scripts/vensim_csv.py': '68fe6d24ebdb4291bd7c5a062669dc23bfacc90c67fa7327efb438ff036f77e3', 'results/runs/case1_external.csv': '850db08ffe3cd3743155069f5e962e60482eba68ce2c7dd30acb645dfa830f2e', 'results/runs/case2_external.csv': '15cfacf7146a2506b65b526af0572b21dcb1e153b59c2b54e69f876e1efcfb63'}

for name, expected in EXPECTED_HASHES.items():
    if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
        raise ValueError(f"{name} differs from the reviewed revision {REVISION}. Check the inputs before comparing results.")
sys.path.insert(0, str(ROOT / "scripts"))
from vensim_csv import read_dataset, time_bases

OUT = ROOT / "docs/semantic/data"
OUT.mkdir(parents=True, exist_ok=True)
print("Verified the CSV reader and both result files against the reviewed revision.")

# %% [markdown]
# ## 2. Read the data without losing units or time axes

# %% Cell 2: Read the data without losing units or time axes
loaded = {case: read_dataset(ROOT / f"results/runs/{case}_external.csv")
          for case in ("case1", "case2")}
inventory = pd.DataFrame([
    {"case": case, "variable": name, "unit": units.get(name, ""),
     "points": len(values), "first_year": values.index.min(), "last_year": values.index.max()}
    for case, (series, units) in loaded.items() for name, values in series.items()
])
display(inventory)
for case, (series, _) in loaded.items():
    assert sorted(len(axis) for axis in time_bases(series)) == [21, 1001]
    assert all(values.index.is_monotonic_increasing and values.index.is_unique
               for values in series.values())

# %% [markdown]
# ## 3. Build a table for the three simulated states
#
# Only series with identical time axes are combined. The historical reference
# remains a separate Series; no interpolation or filling is performed.

# %% Cell 3: Build a table for the three simulated states
STATES = ["Deer Population", "Predator Population", "Forage Biomass"]
frames = {}
for case, (series, units) in loaded.items():
    axis = series[STATES[0]].index
    assert all(series[name].index.equals(axis) for name in STATES), "State time axes differ. Keep these series separate."
    frames[case] = pd.DataFrame({name: series[name] for name in STATES})
    frames[case].index.name = "year"
    assert frames[case].shape == (1001, 3) and not frames[case].isna().any().any()
trajectories = pd.concat(frames, names=["case", "year"])
trajectories.to_csv(OUT / "python-state-trajectories.csv")
display(trajectories.head())

# %% [markdown]
# ## 4. Inspect peaks and final values
#
# Peak years below are the maxima among the recorded samples, not a continuous
# optimization of the underlying equations. These are descriptive comparisons.

# %% Cell 4: Inspect peaks and final values
summary = pd.DataFrame([
    {"case": case, "variable": name, "unit": loaded[case][1][name],
     "points": len(values), "minimum": float(values.min()),
     "maximum": float(values.max()), "peak_year": float(values.idxmax()),
     "final_value": float(values.iloc[-1])}
    for case, frame in frames.items() for name, values in frame.items()
])
summary.to_csv(OUT / "python-inspection-summary.csv", index=False)
display(summary.round(2))
report = {"revision": REVISION, "simulationExecuted": False,
          "inventory": inventory.to_dict(orient="records"),
          "summary": summary.to_dict(orient="records"),
          "tableShape": list(trajectories.shape), "historicalInterpolated": False}
_ = (OUT / "python-inspection.json").write_text(json.dumps(report, indent=2) + "\n")

# %% [markdown]
# ## 5. Compare trajectories on their own axes

# %% Cell 5: Compare trajectories on their own axes
plt.rcParams.update({"svg.hashsalt": "kaibab-python-inspection", "svg.fonttype": "none"})
figure, axes = plt.subplots(3, 1, sharex=True, figsize=(9, 7), layout="constrained")
styles = {"case1": ("Case 1 · baseline", "#245a8d", "-"),
          "case2": ("Case 2 · four overrides", "#846114", "--")}
for ax, name in zip(axes, STATES):
    for case, frame in frames.items():
        label, color, style = styles[case]
        ax.plot(frame.index, frame[name], label=label, color=color, linestyle=style)
    ax.set_title(name, loc="left", fontsize=11)
    ax.set_ylabel(loaded["case1"][1][name])
    ax.grid(axis="y", alpha=0.2)
    ax.set_xlim(1900, 1950)
    ax.set_ylim(bottom=0)
historical = loaded["case1"][0]["Historical Deer BOT"]
assert historical.equals(loaded["case2"][0]["Historical Deer BOT"])
axes[0].plot(historical.index, historical.values, ":o", color="#546872",
             markersize=3, label="Historical reference · 21 points")
axes[0].legend(fontsize=8, loc="upper left")
axes[-1].set_xlabel("Year")
figure.savefig(OUT / "python-inspection.svg", metadata={"Date": None})
plt.show()

# %% [markdown]
# ## Where the Python simulation interface fits
#
# The repository also supports running the model via `runners/pysd/run.py`.
# It collects external parameters and lookups, prepares a temporary model copy,
# applies the repository's RK2 adapter, and writes tidy CSV by default. That CSV
# can also be read by `read_dataset`; tidy files do not carry units, so retrieve
# those from the model documentation when inspecting a new Python run.
#
# This notebook starts with **existing results**. To make a fresh Case 2 result,
# the repository-root command below is an optional separate step (not executed here):
#
# ```sh
# python runners/pysd/run.py models/kaibab_ecosystem_model.mdl \
#   -d models/config/parameters/basic_parameters.cin \
#   -d models/config/lookups/ \
#   -d models/config/timeseries/historical_deer_botg.csv \
#   -d models/config/scenarios/case2.cin \
#   --columns "Deer Population" "Predator Population" "Forage Biomass" \
#   -o results/runs/case2_notebook_pysd.csv
# ```
#
# Use the repository runner for this externalized model: the short direct-PySD
# example in the integration notes omits preparation and the complete inputs.
