# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Bundle original artifacts at build time without moving or editing sources."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

ROOT = Path(__file__).parent


class BuildWithArtifacts(build_py):
    def run(self):
        super().run()
        target = Path(self.build_lib) / "fair_hunter_prey" / "_bundle"
        files = []
        for folder in ("models", "runners/pysd", "scripts", "results/reference", "results/runs", "examples/stella-source/models", "examples/stella-source/results"):
            files.extend(p for p in (ROOT / folder).rglob("*") if p.is_file())
        files.extend(ROOT / p for p in ("CITATION.cff", "codemeta.json", "REUSE.toml", "LICENSE", "pyproject.toml", "CHANGELOG.md", "docs/fair/stella-sources.json"))
        files.extend((ROOT / "LICENSES").glob("*.txt"))
        files.extend((ROOT / "environments").glob("*.txt"))
        hashes = {}
        for source in files:
            if "__pycache__" in source.parts or source.suffix in (".pyc", ".pyo") or source.name == ".DS_Store":
                continue
            relative = source.relative_to(ROOT)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            hashes[relative.as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()
        saved = ROOT / "src/fair_hunter_prey/_build_info.json"
        try:
            revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            revision = json.loads(saved.read_text())["revision"] if saved.exists() else "unrecorded-source"
        (target.parent / "_build_info.json").write_text(json.dumps({"revision": revision, "sha256": hashes}, indent=2) + "\n")


class SourceWithRevision(sdist):
    def make_release_tree(self, base_dir, files):
        super().make_release_tree(base_dir, files)
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        target = Path(base_dir) / "src/fair_hunter_prey/_build_info.json"
        target.write_text(json.dumps({"revision": revision}) + "\n")


setup(cmdclass={"build_py": BuildWithArtifacts, "sdist": SourceWithRevision})
