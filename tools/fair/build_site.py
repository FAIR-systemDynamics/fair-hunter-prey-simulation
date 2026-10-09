# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Assemble the immutable semantic site and additional slides in one artifact."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def build(destination):
    destination = Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Choose a new or empty build destination')
    destination.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / 'tests/fair-preservation.json').read_text())['sha256']
    count = 0
    for name, expected in manifest.items():
        if not name.startswith('docs/semantic/'): continue
        source = ROOT / name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, name
        target = destination / source.relative_to(ROOT / 'docs/semantic')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        count += 1
    shutil.copytree(ROOT / 'docs/slides', destination / 'slides')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    for name in ('index.html', 'catalog.json', 'sources.json', 'comparison.html'):
        file = destination / 'slides' / name
        file.write_text(file.read_text().replace('__REVISION__', revision))
    (destination / '.nojekyll').touch()
    print(f'{count} unchanged semantic-site files + slides at {destination}; revision {revision}')
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='_site')
    build(parser.parse_args().output_dir)
