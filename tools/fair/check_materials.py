# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Check cross-file metadata, lecture coverage, assets, and preserved semantics."""
import hashlib
import json
import tomllib
from ruamel.yaml import YAML
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
    expected=['Raphael Ginster','Matthias Papesch','Vasiliy Seibert']
    citation=YAML(typ='safe').load((ROOT/'CITATION.cff').read_text())
    publication=json.loads((ROOT/'docs/fair/publication.json').read_text())
    assert [a['name'] for a in project['authors']]==expected
    assert [a['given-names']+' '+a['family-names'] for a in citation['authors']]==expected
    assert [a['name'] for a in zenodo['creators']]==['Ginster, Raphael','Papesch, Matthias','Seibert, Vasiliy']
    assert citation['version']==zenodo['version']==project['version']==publication['version']
    if publication['status']=='published':
        assert publication['concept_doi'] and publication['version_doi'] and publication['release_revision']
    else:
        assert 'doi' not in zenodo and not publication['version_doi'], 'Do not invent an unreleased DOI'

    slides=ROOT/'docs/slides'
    for evidence in json.loads((slides/'sources.json').read_text())['screenshots']:
        assert hashlib.sha256((slides/evidence['file']).read_bytes()).hexdigest()==evidence['sha256'], evidence['file']
    soup=BeautifulSoup((slides/'index.html').read_text(),'html.parser')
    ids=[x['id'] for x in soup.select('[id]')]
    assert len(ids)==len(set(ids)), Counter(ids)
    sections=soup.select('.slides > section')
    assert len(sections)==63
    assert len(soup.select('section.case-study'))==5
    assert len(soup.select('section.appendix'))==6
    coverage=json.loads((slides/'coverage.json').read_text())
    assert sorted(c['original_slide'] for c in coverage)==list(range(1,53))
    baseline=ROOT/'tools/fair/reference/awesome-sim.html'
    source_manifest=json.loads((slides/'sources.json').read_text())
    assert hashlib.sha256(baseline.read_bytes()).hexdigest()==source_manifest['reference_deck']['html_sha256']
    reference=BeautifulSoup(baseline.read_text(),'html.parser').select('.slides > section')
    assert [int(s['data-reference-slide']) for s in sections if s.has_attr('data-reference-slide')]==list(range(1,53))
    for c in coverage:
        current=sections[c['adapted_slide']-1]; old=reference[c['original_slide']-1]
        assert current['id']==c['adapted_id']
        assert old.get('class')==current.get('class')==c['reference_layout'], current['id']
        # Every original principle quotation and reference layout family survives.
        assert [q.get_text(' ',strip=True) for q in old.select('.principle-quote')]==[q.get_text(' ',strip=True) for q in current.select('.principle-quote')]
        assert all(x['category'] in ('case-study adaptation','verified factual correction','operational update') and x['reason'] and x['before']!=x['after'] for x in c['changes'])
        assert (slides/'comparison'/f"{c['original_slide']:02d}-reference.jpg").is_file()
        assert (slides/'comparison'/f"{c['original_slide']:02d}-adapted.jpg").is_file()
    assert len(soup.select('section.divider'))==6
    assert len(soup.select('section.title-slide'))==2
    for css in ('css/nfdi4ing-theme.css','css/slides.css'):
        # Baseline styles are pinned, rather than inferred from slide counts.
        expected=source_manifest['reference_theme_sha256'][css]
        assert hashlib.sha256((slides/css).read_bytes()).hexdigest()==expected, css
    why=soup.select_one('#why-fair')
    assert len(why.select('table'))==1
    for phrase in ('Why make research software FAIR?', 'Citations', 'Reproducibility', 'Collaboration'):
        assert phrase.lower() in why.get_text().lower(), phrase
    for current in sections:
        assert not any(a.get_text(strip=True).startswith('Source ') for a in current.select('a')), current['id']
    assert 'CHANGELOG.md' in soup.select_one('#provenance').get_text()
    assert 'OpenAPI' in soup.select_one('#api-example').get_text()
    assert 'Alice' in soup.select_one('#qualified-references').get_text()
    assert len(soup.select_one('#checklist').select('.fair-grid > div'))==4

    for s in sections:
        assert s.select_one('aside.notes').get_text().strip(), s['id']
        assert len(s.select('.workflow:not(.workflow-full) li'))==6 and len(s.select('.workflow:not(.workflow-full) .active'))==1
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
    print('Metadata consistent; 52/52 original layouts and principle quotations; 63 slides with notes, workflow and content-level register; local links/assets resolve; preserved semantic RDF isomorphic and SHACL-conformant.')
if __name__=='__main__':check()
