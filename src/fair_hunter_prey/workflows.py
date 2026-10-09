# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Additive workflows around unchanged repository runners and CSV readers."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY = "https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation"
STELLA_REVISION = "194a8b92e963920e95393accc7d5699348864d85"
STOCKS = ("Deer Population", "Predator Population", "Forage Biomass")


def _root():
    bundled = Path(__file__).parent / "_bundle"
    return bundled if bundled.is_dir() else Path(__file__).resolve().parents[2]


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _reader(name):
    spec = importlib.util.spec_from_file_location(f"fair_hunter_prey._{name}", _root() / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _destination(path):
    path = Path(path).expanduser().resolve()
    # Never write into a source/model/resource tree, even if a subfolder is empty.
    root = _root().resolve()
    for protected in ("models", "runners", "scripts", "results", "docs/semantic", "src", "examples/stella-source"):
        if path.is_relative_to(root / protected):
            raise ValueError(f"Choose a separate output directory outside {protected}")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise FileExistsError(f"Output directory must be new or empty: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _environment():
    return {d.metadata["Name"]: d.version for d in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata["Name"].lower())}


def _revision():
    info = Path(__file__).parent / "_build_info.json"
    if info.exists():
        return json.loads(info.read_text())["revision"]
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_root(), stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unrecorded-source"


def _inputs(implementation, case):
    if implementation not in ("vensim", "stella") or case not in ("case1", "case2"):
        raise ValueError("implementation must be vensim or stella; case must be case1 or case2")
    root = _root()
    if implementation == "vensim":
        model = root / "models/kaibab_ecosystem_model.mdl"
        data = [root / "models/config/parameters/basic_parameters.cin", root / "models/config/lookups", root / "models/config/timeseries/historical_deer_botg.csv"]
        # Pass explicit Vensim inputs to retain the established configuration.
        data = [data[0], *sorted(data[1].glob("effect_*.cin")), data[2]]
        if case == "case2":
            data.append(root / "models/config/scenarios/case2.cin")
        resources = [model, *data, root / "models/config/parameters/initial_stock_parameters.xlsx"]
    else:
        root = root / "examples/stella-source"
        model = root / "models/kaibab_ecosystem_model.stmx"
        data = [root / f"models/config/parameters/kaibab_ecosystem_parameters_stella_scenario{case[-1]}.csv", root / "models/config/lookups/kaibab_ecosystem_lookups_stella.csv", root / "models/config/timeseries/kaibab_ecosystem_historic_BOT_stella.csv"]
        resources = [model, *data]
    missing = [str(p) for p in resources if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing model input(s): " + ", ".join(missing))
    return model, data, resources


def run_example(implementation: str, case: str, output_dir: str | Path) -> dict[str, Path]:
    """Run an existing implementation with PySD; return CSV and provenance paths.

    Neither vendor application is invoked. The implementation selects the source
    format and its existing numerical adapter, not a vendor execution engine.
    """
    model, data, inputs = _inputs(implementation, case)
    out = _destination(output_dir)
    target = out / "simulation.csv"
    runner = _root() / "runners/pysd/run.py"
    args = [sys.executable, str(runner), str(model)]
    for path in data:
        args.extend(["-d", str(path)])
    args.extend(["--columns", *STOCKS, "--layout", implementation, "-o", str(target)])
    if implementation == "vensim":
        # Match the established compare_tools.sh / test_reference.py grid.
        # This selects saved samples, while the original model retains DT=0.05.
        args.extend(["--saveper", "1"])
    start = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(args, capture_output=True, text=True)
    (out / "runner.log").write_text(
        f"Execution engine: PySD\nSource implementation: {implementation}\nCase: {case}\n"
        + completed.stdout + completed.stderr)
    if completed.returncode:
        raise RuntimeError(f"PySD failed; see {out / 'runner.log'}\n{completed.stderr[-1800:]}")
    code = sorted((_root() / "runners/pysd").glob("*.py")) + sorted((_root() / "scripts").glob("*.py"))
    provenance = {"activity": "simulation", "engine": "PySD", "implementation": implementation, "case": case,
                  "method": "rk2-midpoint" if implementation == "vensim" else "rk2-heun", "started": start,
                  "save_interval_years": 1 if implementation == "vensim" else 0.05,
                  "ended": datetime.now(timezone.utc).isoformat(), "repository": REPOSITORY, "revision": _revision(),
                  "model_source_revision": STELLA_REVISION if implementation == "stella" else _revision(),
                  "python": sys.version, "dependencies": _environment(),
                  "inputs": {p.relative_to(_root()).as_posix(): _hash(p) for p in inputs},
                  "code": {p.relative_to(_root()).as_posix(): _hash(p) for p in code},
                  "command": args[1:], "outputs": {name: _hash(out / name) for name in ("simulation.csv", "runner.log")}}
    manifest = out / "provenance.json"
    manifest.write_text(json.dumps(provenance, indent=2) + "\n")
    return {"csv": target, "provenance": manifest, "log": out / "runner.log"}


def inspect_results(output_dir: str | Path) -> dict[str, Path]:
    """Inspect all four saved exports. No PySD simulation is performed.

    Native time axes are retained. Stella's final-only Case 2 export produces
    final-value rows with no invented time axis or variable units.
    """
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = _destination(output_dir)
    rows, final, sources = [], [], {}
    for implementation in ("vensim", "stella"):
        for case in ("case1", "case2"):
            if implementation == "vensim":
                source = _root() / f"results/runs/{case}_external.csv"
                series, units = _reader("vensim_csv").read_dataset(source)
                for name, values in series.items():
                    for time, value in values.items():
                        rows.append([implementation, case, name, float(time), float(value), units.get(name, ""), "export"])
            else:
                source = _root() / f"examples/stella-source/results/kaibab_ecosystem_results_stella_scenario{case[-1]}.csv"
                times, series, time_unit = _reader("stella_csv").read_results(source)
                for name, values in series.items():
                    if times:
                        for time, value in zip(times, values, strict=True):
                            rows.append([implementation, case, name, time, value, "", "not supplied in export"])
                    else:
                        final.append([implementation, case, name, values[0], "", "final value only; no time axis in export"])
            sources[source.relative_to(_root()).as_posix()] = _hash(source)
    frame = pd.DataFrame(rows, columns=["implementation", "case", "variable", "time", "value", "unit", "unit_source"])
    frame.to_csv(out / "trajectories.csv", index=False)
    pd.DataFrame(final, columns=["implementation", "case", "variable", "value", "unit", "note"]).to_csv(out / "final-values.csv", index=False)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True, layout="constrained")
    for ax, stock in zip(axes, STOCKS, strict=True):
        subset = frame[frame.variable == stock]
        for (implementation, case), data in subset.groupby(["implementation", "case"], sort=False):
            ax.plot(data.time, data.value, label=f"{implementation.title()} · {case}", linestyle="--" if implementation == "stella" else "-")
        ax.set_ylabel(stock); ax.grid(alpha=.2)
    axes[0].legend(fontsize=9); axes[-1].set_xlabel("Simulation time (year)")
    fig.suptitle("Saved trajectories · Stella Case 2 is available as final values only", fontsize=12)
    fig.savefig(out / "saved-results.png", dpi=160); plt.close(fig)
    report = {"activity": "inspection of saved exports", "simulation_executed": False, "sources": sources,
              "revision": _revision(), "python": sys.version, "dependencies": _environment(),
              "notes": ["Case 2 changes four parameters.", "Historical observations retain their own time axis.", "Missing Stella variable units remain empty; consult the model declarations.", "Stella Case 2 has no exported trajectory."],
              "outputs": {n: _hash(out / n) for n in ("trajectories.csv", "final-values.csv", "saved-results.png")}}
    (out / "inspection.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"trajectories": out / "trajectories.csv", "final_values": out / "final-values.csv", "figure": out / "saved-results.png", "provenance": out / "inspection.json"}


def create_crate(run_dir: str | Path, output_dir: str | Path) -> Path:
    """Package an actual completed run; refuse changed inputs or outputs."""
    from rocrate.rocrate import ROCrate
    run_dir = Path(run_dir).resolve()
    provenance = json.loads((run_dir / "provenance.json").read_text())
    for name, expected in provenance["outputs"].items():
        if _hash(run_dir / name) != expected:
            raise ValueError(f"Run output changed: {name}")
    for name, expected in {**provenance["inputs"], **provenance["code"]}.items():
        if _hash(_root() / name) != expected:
            raise ValueError(f"Source changed since execution: {name}")
    out = _destination(output_dir)
    crate = ROCrate()
    crate.name = f"Kaibab {provenance['implementation']} {provenance['case']} executed with PySD"
    crate.description = "Recorded simulation, original scientific inputs, runner, environment and output. Model-derived material retains CC BY-NC-SA 4.0; software code is MIT. See REUSE.toml."
    crate.root_dataset["license"] = {"@id": "https://creativecommons.org/licenses/by-nc-sa/4.0/"}
    crate.root_dataset["isBasedOn"] = {"@id": REPOSITORY + "/tree/" + provenance["revision"]}
    for name in {**provenance["inputs"], **provenance["code"]}:
        license_url = "https://creativecommons.org/licenses/by-nc-sa/4.0/" if name.startswith("models/") or "/models/" in name else "https://spdx.org/licenses/MIT.html"
        crate.add_file(_root() / name, dest_path=name, properties={"sha256": _hash(_root() / name), "license": {"@id": license_url}})
    for name in ("CITATION.cff", "codemeta.json", "REUSE.toml", "LICENSE", "pyproject.toml", "CHANGELOG.md"):
        crate.add_file(_root() / name, dest_path=name)
    for source in (_root() / "LICENSES").glob("*.txt"):
        crate.add_file(source, dest_path="LICENSES/" + source.name)
    for source in run_dir.iterdir():
        if source.is_file(): crate.add_file(source, dest_path="execution/" + source.name)
    from rocrate.model.person import Person
    people = [crate.add(Person(crate, "https://orcid.org/0000-0003-2394-7064", properties={"name": "Raphael Ginster"})),
              crate.add(Person(crate, "#matthias-papesch", properties={"name": "Matthias Papesch"})),
              crate.add(Person(crate, "https://orcid.org/0000-0002-7121-6816", properties={"name": "Vasiliy Seibert"}))]
    crate.root_dataset["creator"] = people
    from rocrate.model.contextentity import ContextEntity
    engine = crate.add(ContextEntity(crate, "https://pysd.readthedocs.io/", properties={
        "@type": "SoftwareApplication", "name": "PySD", "softwareVersion": provenance["dependencies"]["pysd"]}))
    reference = (f"results/reference/{provenance['case']}.csv" if provenance["implementation"] == "vensim" else
                 f"examples/stella-source/results/kaibab_ecosystem_results_stella_scenario{provenance['case'][-1]}.csv")
    crate.add_file(_root() / reference, dest_path=reference, properties={"sha256": _hash(_root() / reference),
        "description": "Native reference export; Stella Case 2 contains final values only.",
        "license": {"@id": "https://creativecommons.org/licenses/by-nc-sa/4.0/"}})
    action = crate.add(ContextEntity(crate, "#execution", properties={
        "@type": "CreateAction", "name": crate.name, "instrument": engine,
        "actionStatus": {"@id": "http://schema.org/CompletedActionStatus"},
        "startTime": provenance["started"], "endTime": provenance["ended"],
        "object": [{"@id": name} for name in provenance["inputs"]],
        "result": {"@id": "execution/simulation.csv"},
        "description": f"{provenance['method']} integration; see execution/provenance.json for settings and hashes."}))
    crate.root_dataset["mentions"] = action
    # Materialize the exact observed environment without modifying the run.
    environment_text = "\n".join(f"{name}=={version}" for name, version in provenance["dependencies"].items()) + "\n"
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        environment = Path(tmp) / "environment.txt"
        environment.write_text(environment_text)
        crate.add_file(environment, dest_path="environment.txt", properties={"description": "Exact installed distributions at execution; platform-specific, not a cross-platform lock."})
        # A portable rerun command points into the crate, not the producer's paths.
        original = provenance["command"]
        args = []
        for index, value in enumerate(original):
            if index and original[index-1] == "-o":
                args.append("reproduced/simulation.csv")
            else:
                args.append(value.replace(str(_root()) + "/", ""))
        script = Path(tmp) / "reproduce.py"
        script.write_text("# SPDX-FileCopyrightText: 2026 Vasiliy Seibert\n# SPDX-License-Identifier: MIT\n"
            "import os, subprocess, sys\nfrom pathlib import Path\nos.chdir(Path(__file__).parent)\n"
            "Path('reproduced').mkdir(exist_ok=False)\nsubprocess.run([sys.executable, *" + repr(args) + "], check=True)\n")
        crate.add_file(script, dest_path="reproduce.py", properties={"license": {"@id": "https://spdx.org/licenses/MIT.html"}})
        readme = Path(tmp) / "README-crate.txt"
        readme.write_text("This is an actual PySD execution, not a new native vendor run.\n"
            "Use the recorded Python version and install the dependencies listed in environment.txt.\n"
            "That file records the producer platform, including platform-specific distributions.\n"
            "Run python reproduce.py from an extracted copy. It creates a new reproduced/ directory.\n"
            "Original results remain in execution/. Compare each implementation against its own reference.\n"
            "Stella Case 2's native reference supplies final values only.\n"
            "Model-derived files are CC BY-NC-SA 4.0, code MIT, general documentation CC BY 4.0.\n"
            "The original contributors and literature references are retained in CITATION.cff and REUSE.toml.\n")
        crate.add_file(readme, dest_path="README-crate.txt")
        crate.write(out)
        # Hash every payload, including logs and provenance (metadata is excluded to avoid a cycle).
        for entity in crate.get_entities():
            path = out / entity.id
            if entity.type == "File" and path.is_file() and path.name != "ro-crate-metadata.json":
                entity["sha256"] = _hash(path)
        crate.write(out)
    return out
