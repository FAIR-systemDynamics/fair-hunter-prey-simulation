# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Run unchanged original Stella tests against their isolated source snapshot."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="fair-stella-tests-") as folder:
    target = Path(folder)
    for name in ("runners", "scripts", "tests"):
        shutil.copytree(ROOT / name, target / name, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    shutil.copytree(ROOT / "examples/stella-source", target, dirs_exist_ok=True)
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "tests/test_stella.py", "-q"], cwd=target))
