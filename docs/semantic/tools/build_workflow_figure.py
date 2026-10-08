"""Render a review figure using the pinned repository's own plotting code.

This executes plotting only, never a simulation. The manifest records the exact
input, software and output hashes so the semantic graph can describe this step.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/semantic/data'
REV = 'f156dcf37597c0587958f463985986f0ea91accf'
INPUT = 'results/runs/case2_external.csv'
SOURCES = [INPUT, 'scripts/plot_results.py', 'scripts/vensim_csv.py']
COLUMNS = ['Deer Population', 'Predator Population', 'Forage Biomass']

with tempfile.TemporaryDirectory(prefix='kaibab-workflow-') as scratch:
    scratch = Path(scratch)
    hashes = {}
    for path in SOURCES:
        raw = subprocess.check_output(['git', 'show', f'{REV}:{path}'], cwd=ROOT)
        target = scratch / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        hashes[path] = hashlib.sha256(raw).hexdigest()
    # Stable SVG IDs/date make repeated builds comparable.
    (scratch / 'matplotlibrc').write_text('svg.hashsalt: kaibab-case2-workflow\n')
    args = ['scripts/plot_results.py', INPUT, '--columns', *COLUMNS,
            '--format', 'svg', '--name', 'case2-workflow', '--outdir', str(OUT)]
    subprocess.run([sys.executable, *args], cwd=scratch, check=True,
                   env={**os.environ, 'MPLCONFIGDIR': str(scratch / '.mpl'),
                        'XDG_CACHE_HOME': str(scratch / '.cache'),
                        'SOURCE_DATE_EPOCH': '0'})

figure = OUT / 'case2-workflow.svg'
figure.write_text('\n'.join(line.rstrip() for line in figure.read_text().splitlines()) + '\n')
manifest = dict(revision=REV, sources=hashes, output=figure.name,
                sha256=hashlib.sha256(figure.read_bytes()).hexdigest(),
                columns=COLUMNS, simulationExecuted=False,
                command='python scripts/plot_results.py results/runs/case2_external.csv '
                        '--columns "Deer Population" "Predator Population" "Forage Biomass" '
                        '--format svg --name case2-workflow --outdir docs/semantic/data')
(OUT / 'workflow-figure.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Rendered and recorded the Case 2 figure from committed results; no simulation executed.')
