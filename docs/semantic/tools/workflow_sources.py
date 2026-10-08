"""Commit-pinned links to the notebook and generated workflow artifacts."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_REVISION = '23e58532d8014dbcc2299cd496896846605af968'
REPO = 'https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation'


def artifact_source(path, anchor=None, label=None):
    repository_path = 'docs/semantic/' + path
    committed = subprocess.check_output(
        ['git', 'show', f'{ARTIFACT_REVISION}:{repository_path}'], cwd=ROOT)
    assert committed == (ROOT / repository_path).read_bytes(), repository_path
    url = f'{REPO}/blob/{ARTIFACT_REVISION}/{repository_path}'
    if anchor:
        url += '#' + anchor
    return dict(url=url, label=label or repository_path)
