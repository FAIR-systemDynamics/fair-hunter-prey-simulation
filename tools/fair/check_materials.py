# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Check cross-file metadata, lecture coverage, assets, and preserved semantics."""
import hashlib
import json
import tomllib
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlparse
from bs4 import BeautifulSoup
from rdflib import Graph
from rdflib.compare import isomorphic
from pyshacl import validate

ROOT = Path(__file__).resolve().parents[2]
def check():
    for file in ('tests/fair-preservation.json','docs/fair/stella-sources.json'):
        data=json.loads((ROOT/file).read_text())
        for name, digest in data['sha256'].items():
            assert hashlib.sha256((ROOT/data.get('bundle','')/name).read_bytes()).hexdigest()==digest, name
    project=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']
    metadata=json.loads((ROOT/'codemeta.json').read_text())
    assert metadata['@type']=='SoftwareSourceCode'
    assert metadata['version']==project['version']
    assert metadata['codeRepository']==project['urls']['Repository']
    assert [a['givenName']+' '+a['familyName'] for a in metadata['author']]==[a['name'] for a in project['authors']]
    zenodo=json.loads((ROOT/'.zenodo.json').read_text())
    assert len(zenodo['creators'])==3 and 'doi' not in zenodo
    assert '0.7.0.dev0' in (ROOT/'CITATION.cff').read_text()
    slides=ROOT/'docs/slides'
    soup=BeautifulSoup((slides/'index.html').read_text(),'html.parser')
    ids=[x['id'] for x in soup.select('[id]')]
    assert len(ids)==len(set(ids)), Counter(ids)
    sections=soup.select('.slides > section')
    assert len(sections)==62
    coverage=json.loads((slides/'coverage.json').read_text())
    assert sorted(c['original_slide'] for c in coverage)==list(range(1,53))
    for c in coverage: assert sections[c['adapted_slide']-1]['id']==c['adapted_id']
    for s in sections:
        assert s.select_one('aside.notes').get_text().strip(), s['id']
        assert len(s.select('.workflow li'))==6 and len(s.select('.workflow .active'))==1
    for tag in soup.select('[href], [src]'):
        url=tag.get('src',tag.get('href')); parsed=urlparse(url)
        if url.startswith('https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation/blob/__REVISION__/'):
            path=url.split('/blob/__REVISION__/',1)[1].split('#')[0]
            assert (ROOT/unquote(path)).exists(), path
        if not parsed.scheme and parsed.path:
            assert (slides/unquote(parsed.path)).exists(), url
    site=ROOT/'docs/semantic'
    graph=Graph().parse(site/'model.ttl',format='turtle')
    jsonld=Graph().parse(site/'model.jsonld',format='json-ld')
    assert isomorphic(graph,jsonld), 'semantic graph serialization mismatch'
    conforms, _, report=validate(graph,shacl_graph=Graph().parse(site/'shapes.ttl'),inference='rdfs')
    assert conforms, report
    print('Metadata consistent; 52/52 reference topics; 62 slides with notes and workflow; local links/assets resolve; preserved semantic RDF isomorphic and SHACL-conformant.')
if __name__=='__main__':check()
