"""Check RDF equivalence, SHACL, source selectors, graph projection, and scenario resolution."""
import argparse
import csv
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
from workflow_sources import ARTIFACT_REVISION

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
            assert linkrev in {rev,data['overview']['stellaRevision'],ARTIFACT_REVISION}
            path,_,anchor=suffix.partition('#')
            raw=source(path,linkrev)
            if anchor.startswith('L'):
                bounds=[int(part.removeprefix('L')) for part in anchor.split('-')]
                assert 1<=min(bounds)<=max(bounds)<=len(raw.splitlines()),s
checks.append('All 51 file hashes and commit-pinned source links match Git content')
check('Overview separates the mathematical model, both native files, task and setup',set(['model','file/models/kaibab_ecosystem_model.mdl','file/models/kaibab_ecosystem_model.stmx','task/simulate','overview/setup']).issubset(set(data['overview']['entities'])))
check('Overview does not mistake an individual case for the simulation task',not any(k.startswith('run/') for k in data['overview']['entities']))
check('Kaibab is typed with the actual MathModDB mathematical-model entity',(URIRef(entities['model']['uri']),RDF.type,URIRef('https://portal.mardi4nfdi.de/entity/Q68663')) in g)
checks.append('All 47 declaration line anchors point at the correct symbols')
workflow=data['workflow']
expected=['file/models/kaibab_ecosystem_model.mdl','file/models/config/scenarios/case2.cin',
          'run/case2','file/results/runs/case2_external.csv','visualization/case2-review']
check('Workflow stages preserve the model, scenario, simulation, result and figure sequence',
      [s['entity'] for s in workflow['stages']]==expected)
sequence=URIRef(entities[workflow['id']]['uri']+'/sequence')
for index,key in enumerate(expected,1):
    assert (sequence,URIRef(str(RDF)+'_'+str(index)),URIRef(entities[key]['uri'])) in g
check('Every curated workflow arrow reuses an actual semantic relationship',
      all(e in data['edges'] for e in workflow['edges']))
manifest=workflow['figure']
check('The plotted input and plotting code match the pinned revision',
      manifest['revision']==rev and all(hashlib.sha256(source(p)).hexdigest()==digest
                                      for p,digest in manifest['sources'].items()))
check('The generated figure exists and matches its provenance hash',
      hashlib.sha256((HERE/'data'/manifest['output']).read_bytes()).hexdigest()==manifest['sha256']
      ==entities['visualization/case2-review']['sha256'])
check('Visualization is explicitly separate from simulation execution',
      manifest['simulationExecuted'] is False
      and entities['processing/plot-case2-review']['status']=='Executed locally'
      and entities['run/case2']['status']=='Documented')
input_predicate='http://purl.obolibrary.org/obo/RO_0002233'
check('Data-flow display arrows have matching input relationships in the inverse direction',
      all(any(r['source']==e['target'] and r['target']==e['source'] and r['predicate']==input_predicate
              for r in data['edges']) for e in data['edges'] if e['predicate']==str(SD.inputTo)))
check('Workflow catalog contains both examples with unique section anchors',
      [w['slug'] for w in data['workflows']]==['case2-parameter-to-figure','python-inspection'])
for item in data['workflows']:
    assert all(e in data['edges'] for e in item['edges'])
    sequence=URIRef(entities[item['id']]['uri']+'/sequence')
    for index,stage in enumerate(item['stages'],1):
        assert (sequence,URIRef(str(RDF)+'_'+str(index)),URIRef(entities[stage['entity']]['uri'])) in g
checks.append('Both workflow sequences and every displayed arrow are present in RDF')
inspection=data['workflows'][1]
for path,digest in inspection['manifest']['sources'].items():
    assert hashlib.sha256(source(path)).hexdigest()==digest
for path,digest in inspection['manifest']['outputs'].items():
    assert hashlib.sha256((HERE/path).read_bytes()).hexdigest()==digest
    assert hashlib.sha256(source('docs/semantic/'+path, ARTIFACT_REVISION)).hexdigest()==digest
checks.append('Notebook, exported tables and plot match recorded hashes; inputs and reader match the pinned revision')
notebook=json.loads((HERE/'notebooks/inspect_results.ipynb').read_text())
cells=[c for c in notebook['cells'] if c['cell_type']=='code']
check('All five notebook code cells executed successfully with a saved inline figure',
      len(cells)==5 and [c['execution_count'] for c in cells]==list(range(1,6))
      and not any(o['output_type']=='error' for c in cells for o in c['outputs'])
      and any('image/png' in o.get('data',{}) for c in cells for o in c['outputs']))
python_lines=(HERE/'notebooks/inspect_results.py').read_text().splitlines()
for section in inspection['sections']:
    cell=notebook['cells'][section['cellIndex']]
    assert cell['id']==section['cellId'] and cell['execution_count']==section['number']
    heading=notebook['cells'][section['cellIndex']-1]
    assert heading['id']==section['markdownCellId']
    assert ''.join(heading['source']).splitlines()[0]=='## '+section['heading']
    actual=python_lines[section['pythonStartLine']:section['pythonEndLine']]
    expected=[line if not line.startswith('%') else '# Jupyter: '+line
              for line in ''.join(cell['source']).splitlines()]
    assert actual==expected, section['id']
    assert section['url'].endswith('/docs/semantic/'+section['previewPath'])
    excerpt=json.loads((HERE/section['previewPath']).read_text())
    assert excerpt['cells'][0]==heading
    assert excerpt['cells'][-1]==cell
    assert len([c for c in excerpt['cells'] if c['cell_type']=='code'])==1
    assert '../inspect_results.ipynb' in ''.join(excerpt['cells'][1]['source'])
checks.append('All five notebook links open notebook excerpts preserving the exact executed cells and outputs')
check('Inspection flows from the activity to code before notebook sections and outputs',
      {e['target'] for e in inspection['edges'] if e['source']=='processing/inspect-results-python'}
      == {'file/scripts/vensim_csv.py','notebook/inspect-results'})
check('Workflow artifact links use repository sources without local downloads',
      all('/blob/' in action['url'] and not action.get('download') for w in data['workflows'] for action in w['actions'])
      and not any(e.get('localUrl') or e.get('localDownload') for e in entities.values()))
inspection_report=inspection['report']
check('Python inspection preserves the 1001-point states and separate 21-point reference',
      inspection_report['tableShape']==[2002,3] and inspection_report['historicalInterpolated'] is False
      and all(r['points']==(21 if r['variable']=='Historical Deer BOT' else 1001)
              for r in inspection_report['inventory']))
for case in ('case1','case2'):
    for row in csv.reader(io.StringIO(source(f'results/runs/{case}_external.csv').decode())):
        if row[0]=='Time':
            axis=[float(x) for x in row[2:] if x]
        elif row[0] in ('Deer Population','Predator Population','Forage Biomass'):
            values=[float(x) for x in row[2:] if x]
            summary=next(r for r in inspection_report['summary'] if r['case']==case and r['variable']==row[0])
            assert summary['maximum']==max(values) and summary['minimum']==min(values)
            assert summary['peak_year']==axis[values.index(max(values))]
            assert summary['final_value']==values[-1] and summary['unit']==row[1]
checks.append('Notebook statistics independently match the committed CSV values, units and time axes')
check('Python inspection makes no claim of a new simulation',
      inspection['manifest']['simulationExecuted'] is False and inspection_report['simulationExecuted'] is False)
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
