"""Render the complete saved notebook without executing or splitting it."""
import base64
import hashlib
import json
from pathlib import Path
import struct

from bs4 import BeautifulSoup
import nbformat
from nbconvert import HTMLExporter
from workflow_sources import REPO

VIEW_PATH = 'notebooks/inspect_results.html'
SOURCE_BASE = f'{REPO}/blob/codex/semantic-workflow-sources/docs/semantic/notebooks/'


def render_notebook(notebook, sections):
    # The base template provides Jupyter cells and saved MIME outputs, without
    # the CDN scripts, fonts and application chrome of the full HTML template.
    exporter = HTMLExporter(template_name='classic', template_file='base.html.j2')
    body, _ = exporter.from_notebook_node(notebook)
    soup = BeautifulSoup(body, 'html.parser')
    contents = soup.find(id='Contents').find_next_sibling('ol')
    for item, section in zip(contents.find_all('li'), sections, strict=True):
        link = soup.new_tag('a', href='#' + section['anchor'])
        link.string = item.get_text()
        item.clear()
        item.append(link)
    for heading in soup.select('h1, h2'):
        heading['tabindex'] = '-1'
    for link in soup.select('a.anchor-link'):
        link['aria-label'] = 'Link to ' + link.parent.get_text().removesuffix('¶')
    for link in soup.select('a[href="inspect_results.py"]'):
        link['href'] = SOURCE_BASE + 'inspect_results.py'
    for cell, section in zip(soup.select('.code_cell'), sections, strict=True):
        area = cell.select_one('.input_area')
        area['tabindex'] = '0'
        area['role'] = 'region'
        area['aria-label'] = f'Code cell {section["number"]}'
        for output in cell.select('.output_subarea'):
            if output.find('table'):
                output['tabindex'] = '0'
                output['role'] = 'region'
                output['aria-label'] = f'Saved output for cell {section["number"]}'
        for table in cell.select('table'):
            table['aria-label'] = section['heading']
        for img in cell.select('img'):
            img['alt'] = 'Case 1 and Case 2 trajectories for deer, predators and forage; the historical deer reference retains its own time axis.'
            # Reserve the saved plot's aspect ratio before the browser scrolls
            # to a heading, including on a cold page load.
            if img['src'].startswith('data:image/png;base64,'):
                raw = base64.b64decode(img['src'].split(',', 1)[1])
                img['width'], img['height'] = struct.unpack('>II', raw[16:24])
    assert not soup.find('script')
    return f'''<!doctype html>
<html lang="en" class="document-view">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inspect Kaibab results with Python — Notebook</title>
<link rel="stylesheet" href="../tokens.css">
<link rel="stylesheet" href="../style.css">
</head>
<body data-view="notebook">
<header>
<a class="brand" href="../index.html#overview">Kaibab <span>semantic map</span></a>
<nav aria-label="Main navigation"><a href="../index.html#overview">Semantic Model</a><a href="../index.html#workflows">Workflows</a><a href="../index.html#nfdi4ing">NFDI4Ing Use Cases</a></nav>
</header>
<main id="notebook-page">
<nav class="notebook-actions" aria-label="Notebook navigation">
<a href="../index.html#workflow-python-inspection">← Back to workflow</a>
<a href="#Contents">Contents</a>
<a href="{SOURCE_BASE}inspect_results.ipynb" target="_blank" rel="noopener noreferrer">Notebook source in Git ↗</a>
</nav>
<p class="notebook-status">Saved notebook · 5 executed cells · Read-only view</p>
{soup}
</main>
</body>
</html>
'''


def write_notebook_view(notebook, sections, destination):
    (destination / VIEW_PATH).write_text(render_notebook(notebook, sections))
    for section in sections:
        section.pop('previewPath', None)
        section['previewUrl'] = VIEW_PATH + '#' + section['anchor']
    return VIEW_PATH


if __name__ == '__main__':
    here = Path(__file__).resolve().parents[1]
    manifest_path = here / 'data/python-inspection-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    notebook = nbformat.read(here / 'notebooks/inspect_results.ipynb', as_version=4)
    path = write_notebook_view(notebook, manifest['sections'], here)
    manifest['outputs'] = {p: digest for p, digest in manifest['outputs'].items()
                           if not p.startswith('notebooks/sections/')}
    manifest['outputs'][path] = hashlib.sha256((here / path).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Rendered {path} from the complete saved notebook; no cells executed.')
