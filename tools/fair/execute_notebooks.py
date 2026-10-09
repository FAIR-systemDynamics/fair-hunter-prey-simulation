# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
import argparse
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpec
import sys

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('--output-dir', required=True)
args = p.parse_args()
out = Path(args.output_dir).resolve()
out.mkdir(parents=True, exist_ok=False)
for path in sorted((ROOT / 'examples/fair').glob('*.ipynb')):
    book = nbformat.read(path, as_version=4)
    manager = KernelManager()
    manager._kernel_spec = KernelSpec(argv=[sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'], display_name='Verified teaching Python', language='python')
    NotebookClient(book, timeout=300, km=manager, resources={'metadata': {'path': str(out)}}).execute()
    nbformat.write(book, out / path.name)
    print('Executed', path.name, 'with', sys.executable)
