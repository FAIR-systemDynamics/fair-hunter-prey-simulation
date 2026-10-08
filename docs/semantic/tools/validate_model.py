"""Check RDF equivalence, SHACL, source selectors, graph projection, and scenario resolution."""
import argparse
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from decimal import Decimal

import openpyxl
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
from rdflib.compare import isomorphic

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'docs/semantic'
parser=argparse.ArgumentParser();parser.add_argument('--ontology');args=parser.parse_args()
data=json.loads((HERE/'data/model.json').read_text())
rev=data['meta']['revision'];entities={e['id']:e for e in data['entities']}
SD=Namespace(data['meta']['namespace']+'vocabulary#')
M4I=Namespace('http://w3id.org/nfdi4ing/metadata4ing#')
PIMS=Namespace('http://www.molmod.info/semantics/pims-ii.ttl#')
SCHEMA=Namespace('https://schema.org/')
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
def source(path,revision=rev):return subprocess.check_output(['git','show',f'{revision}:{path}'],cwd=ROOT)
g=Graph().parse(HERE/'model.ttl');j=Graph().parse(HERE/'model.jsonld',format='json-ld')
check('Turtle and JSON-LD describe isomorphic RDF graphs',isomorphic(g,j))
conforms,_,report=validate(g,shacl_graph=str(HERE/'shapes.ttl'),inference='rdfs')
check('SHACL application profile conforms',conforms)
for edge in data['edges']:
    check_source=entities.get(edge['source']);check_target=entities.get(edge['target'])
    assert check_source and check_target,edge
    assert (URIRef(check_source['uri']),URIRef(edge['predicate']),URIRef(check_target['uri'])) in g,edge
checks.append('Every browser relation exists in RDF and resolves to a defined entity')
for key,e in entities.items():
    if e['kind']=='File':
        raw=source(e['path'],e['revision'])
        assert hashlib.sha256(raw).hexdigest()==e['sha256'],e['path']
        assert e['revision'] in {rev,data['overview']['stellaRevision']}
    if key.startswith('variable/'):
        lines=source('models/kaibab_ecosystem_model.mdl').decode('utf-8-sig').splitlines()
        assert e['label'] in lines[e['line']-1],(key,e['line'])
        assert e['bindings'],key
    for s in e.get('sources',[]):
        if '/blob/' in s['url']:
            linkrev,suffix=s['url'].split('/blob/',1)[1].split('/',1)
            assert linkrev in {rev,data['overview']['stellaRevision']}
            path,_,anchor=suffix.partition('#')
            raw=source(path,linkrev)
            if anchor.startswith('L'):assert 1<=int(anchor[1:])<=len(raw.splitlines()),s
checks.append('All 51 file hashes and commit-pinned source links match Git content')
check('Overview separates the mathematical model, both native files, task and setup',set(['model','file/models/kaibab_ecosystem_model.mdl','file/models/kaibab_ecosystem_model.stmx','task/simulate','overview/setup']).issubset(set(data['overview']['entities'])))
check('Overview does not mistake an individual case for the simulation task',not any(k.startswith('run/') for k in data['overview']['entities']))
check('Kaibab is typed with the actual MathModDB mathematical-model entity',(URIRef(entities['model']['uri']),RDF.type,URIRef('https://portal.mardi4nfdi.de/entity/Q68663')) in g)
checks.append('All 47 declaration line anchors point at the correct symbols')
vars=[e for e in entities.values() if e['id'].startswith('variable/')]
check('Exactly 47 declarations and three stocks extracted',len(vars)==47 and sum(e['kind']=='Stock' for e in vars)==3)
wb=openpyxl.load_workbook(io.BytesIO(source('models/config/parameters/initial_stock_parameters.xlsx')),data_only=True)
for name,cell,value in [('initial-deer-population','C7',4000),('initial-forage-biomass','C9',317000),('initial-predator-population','C11',100)]:
    e=entities['variable/'+name]
    assert wb['Kaibab Variables'][cell].value==value==e['values']['case1']
    assert any("cell "+cell in b['selector'] for b in e['bindings'])
checks.append('Initial-condition values and worksheet/cell selectors match the workbook')
changed={e['label']:(e['values']['case1'],e['values']['case2']) for e in vars if e.get('values',{}).get('case1')!=e.get('values',{}).get('case2')}
check('Case 2 resolves exactly the four documented overrides',changed=={
 'Baseline Annual Kills per Predator':(40,20),'Deer Carrying Capacity in Years':(2,4),
 'Desired Consumption per Deer':(.75,.5),'Fraction Predators Killed per Year':(0,.2)})
check('Lookup endpoint discrepancy retained explicitly',entities['variable/lookup-effect-of-deer-density-on-predator-births']['points'][-1]==[2,1] and 'review/lookup-endpoint' in entities)
for a in g.subjects(RDF.type,PIMS.Assignment):
    vals=list(g.objects(a,M4I.hasAssignedValue));assert len(vals)==1
    assert len(list(g.objects(a,M4I.hasVariable)))==1
    assert (vals[0],RDF.type,PIMS.Value) in g
checks.append('Assignments separate variable identities from scenario-specific values')
for v in vars:
    if v['kind']!='Lookup':assert list(g.objects(URIRef(v['uri']),SD.denotesConcept))
checks.append('Every numerical declaration maps to a controlled vocabulary concept')
assert len(Graph().parse(HERE/'controlled-vocabulary.ttl'))>0
assert len(Graph().parse(HERE/'vocabulary.ttl'))>0
# Negative SHACL tests: constraints must detect real missing information.
test=Graph()+g
first=next(test.subjects(RDF.type,SD.FileBinding))
test.remove((first,SD.inFile,None))
check('Negative test: a binding without its target file fails validation',not validate(test,shacl_graph=str(HERE/'shapes.ttl'),inference='rdfs')[0])
test=Graph()+g
first=next(test.subjects(RDF.type,PIMS.Assignment))
test.add((first,M4I.hasAssignedValue,URIRef(entities['value/case1/initial-time']['uri'])))
# Ensure the inserted value differs from the original.
if len(list(test.objects(first,M4I.hasAssignedValue)))==1:
    test.add((first,M4I.hasAssignedValue,URIRef(entities['value/case1/final-time']['uri'])))
check('Negative test: multiple values on one assignment fail validation',not validate(test,shacl_graph=str(HERE/'shapes.ttl'),inference='rdfs')[0])
ontology_check='Not run; supply --ontology to check the published m4i terms.'
if args.ontology:
    ontology=Graph().parse(args.ontology)
    used={x for triple in g for x in triple if isinstance(x,URIRef) and str(x).startswith(str(M4I))}
    undefined=used-set(ontology.subjects())
    check('Every m4i class and property used exists in the published ontology',not undefined)
    ontology_check=f'{len(used)} m4i terms verified against the supplied ontology; source versionIRI: '+str(next(ontology.objects(URIRef(str(M4I)),URIRef('http://www.w3.org/2002/07/owl#versionIRI')),None))
result={'conforms':True,'revision':rev,'triples':len(g),'checks':checks,'ontologyTermCheck':ontology_check,'scope':'Structural validation and source-integrity checks, not full OWL consistency or scientific validation. No simulation executed.','shaclReport':report}
(HERE/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
