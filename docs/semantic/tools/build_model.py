"""Build an evidence-linked RDF model and browser data from an immutable Git revision.

Run from any directory: python docs/semantic/tools/build_model.py
Requires rdflib and openpyxl. Does not execute simulations or fetch remote data.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from decimal import Decimal

import openpyxl
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL, XSD

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/semantic'
REV = 'f156dcf37597c0587958f463985986f0ea91accf'
REPO = 'https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation'
BASE = 'https://fair-systemdynamics.github.io/fair-hunter-prey-simulation/semantic/'
NS = Namespace(BASE + '#')
SD = Namespace(BASE + 'vocabulary#')
M4I = Namespace('http://w3id.org/nfdi4ing/metadata4ing#')
PIMS = Namespace('http://www.molmod.info/semantics/pims-ii.ttl#')
SCHEMA = Namespace('https://schema.org/')
PROV = Namespace('http://www.w3.org/ns/prov#')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
DCT = Namespace('http://purl.org/dc/terms/')
QUDT = Namespace('http://qudt.org/schema/qudt/')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
OBO = Namespace('http://purl.obolibrary.org/obo/')
CR = Namespace('http://mlcommons.org/croissant/')
BOOK = 'https://pressbooks.lib.jmu.edu/sdlearningguide/'
CHAPTER = BOOK + 'chapter/chapter-4-introduction-to-system-dynamics-modeling/'
g = Graph()
for prefix, namespace in [('kaibab',NS),('sd',SD),('m4i',M4I),('pims',PIMS),('schema',SCHEMA),('prov',PROV),('skos',SKOS),('dcterms',DCT),('qudt',QUDT),('dcat',DCAT),('obo',OBO),('cr',CR)]:
    g.bind(prefix, namespace)
entities, edges = {}, []

def read(path, binary=False):
    data = subprocess.check_output(['git','show',f'{REV}:{path}'],cwd=ROOT)
    return data if binary else data.decode('utf-8-sig')

def slug(text):
    return re.sub(r'[^a-z0-9]+','-',text.lower()).strip('-')

def uri(key): return URIRef(entities.get(key,{}).get('uri',str(NS[key])))
def lit(s,p,value):
    if isinstance(value,Decimal) and value==value.to_integral():
        value=Literal(format(value,'.1f'),datatype=XSD.decimal)
    g.add((uri(s),p,Literal(value)))
def ref(s,p,value): g.add((uri(s),p,URIRef(value)))
def source(path,line=None): return f'{REPO}/blob/{REV}/{path}' + (f'#L{line}' if line else '')

def add(key,label,kind,definition,types,sources=None,external_uri=None,**extra):
    entities[key] = dict(id=key,uri=external_uri or str(uri(key)),label=label,kind=kind,definition=definition,
                         types=[g.namespace_manager.normalizeUri(t) for t in types],sources=sources or [],**extra)
    for t in types:g.add((uri(key),RDF.type,t))
    lit(key,RDFS.label,label); lit(key,DCT.description,definition)
    for s in sources or []:ref(key,DCT.source,s['url'])
    return key

def edge(a,p,b,label=None,evidence=None,status='Extracted'):
    g.add((uri(a),p,uri(b)))
    edges.append(dict(source=a,target=b,predicate=str(p),label=label or str(p).split('#')[-1],status=status,evidence=evidence))

def src(path,line=None,label=None):return dict(url=source(path,line),label=label or path)

# The project extension is explicit; no project-specific relation is minted under m4i.
classes = {
 'Stock':('An accumulated state in a system dynamics model.',M4I.NumericalVariable),
 'Flow':('A rate contributing to the change of a stock.',M4I.NumericalVariable),
 'Auxiliary':('A numerical variable calculated from other quantities.',M4I.NumericalVariable),
 'Parameter':('A configurable model quantity.',M4I.NumericalVariable),
 'InitialCondition':('A parameter supplying the starting value of a stock.',SD.Parameter),
 'Control':('A numerical control of simulation time or output sampling.',M4I.NumericalVariable),
 'ReferenceSeries':('A reference-mode series used for comparison.',M4I.NumericalVariable),
 'LookupFunction':('A tabulated function; its table is not a scalar parameter.',SCHEMA.CreativeWork),
 'MathematicalModel':('The mathematical specification, distinct from its file representation.',SCHEMA.CreativeWork),
 'FileBinding':('A versioned selector connecting a variable to a location in a file.',SCHEMA.CreativeWork),
 'DocumentedRun':('A processing step reconstructed from repository documentation and committed artifacts; not a newly executed or independently verified run.',M4I.ProcessingStep),
 'ReviewIssue':('An explicit ambiguity or mismatch requiring review.',SCHEMA.CreativeWork),
 'Mechanism':('A model-specific interpretation of interacting equations, not an independently established empirical claim.',SCHEMA.CreativeWork),
}
for name,(definition,parent) in classes.items():
    g.add((SD[name],RDF.type,OWL.Class));g.add((SD[name],RDFS.label,Literal(name)));g.add((SD[name],RDFS.comment,Literal(definition)));g.add((SD[name],RDFS.subClassOf,parent))
object_properties = {
 'denotesConcept':'Connects an implementation entity to a controlled concept; does not assert identity.',
 'declaredIn':'File in which a variable or model is declared.',
 'hasBinding':'A concrete file selector associated with a variable.',
 'inFile':'File targeted by a binding.',
 'dependsOn':'Syntactic equation dependency; not necessarily a positive causal effect.',
 'initializes':'Stock whose initial condition is supplied by this parameter.',
 'inflowTo':'Stock to whose derivative this rate is added.',
 'outflowFrom':'Stock from whose derivative this rate is subtracted.',
 'hasAssignment':'A parameter assignment included in a configuration.',
 'overrides':'A scenario assignment supersedes a baseline assignment.',
 'representsModel':'Connects an implementation file to its mathematical specification.',
 'hasVariable':'Variable or lookup belonging to a mathematical model; distinct from m4i:hasVariable on assignments.',
 'hasLookup':'Table function determining a mechanism.',
 'concerns':'Entity discussed by a review issue.',
 'illustrates':'Model-specific interpretation of a scientific concept.',
 'documentedOutput':'Output associated with a documented run, based on repository evidence.',
 'informs':'A source informs a scientific concept or interpretation.',
 'inputFile':'An external data file supplying values read or loaded for a model file.',
 'involvesVariable':'A variable involved in an interpreted model mechanism; does not assert a fixed causal sign.',
 'explainsConcept':'A model mechanism elaborates a scientific concept.',
}
data_properties = {
 'equation':'Equation text as implemented in the source model.',
 'sourceUnit':'Original model unit string; preserves domain-specific counting units.',
 'selector':'Human-readable selector, such as a model symbol, CSV key, or spreadsheet cell.',
 'path':'Repository-relative file path.',
 'revision':'Git commit identifying inspected source content.',
 'sha256':'SHA-256 digest of the inspected bytes.',
 'evidenceStatus':'Origin of an assertion: Extracted, Literature, Interpreted, or Documented.',
 'reviewNote':'A qualification or interpretation needing review.',
 'lookupPoints':'JSON array of pairs copied from an external lookup table.',
 'sourceLine':'One-based source line of a declaration or value.',
 'timeAxis':'Role of a simulation time axis; not a wall-clock execution timestamp.',
 'inferredFrom':'Description of the evidence used to reconstruct a relationship.',
}
for mapping,t in [(object_properties,OWL.ObjectProperty),(data_properties,OWL.DatatypeProperty)]:
    for name,definition in mapping.items():
        g.add((SD[name],RDF.type,t));g.add((SD[name],RDFS.label,Literal(name)));g.add((SD[name],RDFS.comment,Literal(definition)))
ontology=URIRef(BASE+'vocabulary')
g.add((ontology,RDF.type,OWL.Ontology));g.add((ontology,OWL.versionInfo,Literal('0.2.0-review')))
g.add((ontology,DCT.conformsTo,URIRef('http://w3id.org/nfdi4ing/metadata4ing/1.4.0')))
g.add((ontology,RDFS.comment,Literal('Draft application extension aligned to m4i 1.4.0. The proposed GitHub Pages namespace is not yet published.')))

add('vocabulary','Kaibab controlled vocabulary','Vocabulary','Draft concepts for this model. Scientific definitions and implementation entities remain distinct.',[SKOS.ConceptScheme])
add('repository','FAIR hunter–prey repository','Repository','Versioned source of the concrete model, inputs, software, and committed results.',[SCHEMA.SoftwareSourceCode],[dict(label='Repository on GitHub',url=REPO)],revision=REV)
lit('repository',SD.revision,REV)
add('literature','System Dynamics Learning Guide','Literature','Deaton & MacDonald (2025), James Madison University Libraries. Open textbook underlying the reimplementation.',[SCHEMA.Book],[dict(label='Read the textbook',url=BOOK),dict(label='Read Chapter 4 · §4.12',url=CHAPTER)],status='Literature')
ref('literature',DCT.license,'https://creativecommons.org/licenses/by-nc-sa/4.0/')
add('model','Kaibab ecosystem model','Model','Three coupled stocks describe deer, predators, and forage. This semantic representation separates the specification, implementation, and execution evidence.',[SD.MathematicalModel],[src('models/kaibab_ecosystem_model.mdl'),dict(label='Figure 4.19 and §4.12',url=CHAPTER)],status='Interpreted')
edge('model',PROV.wasDerivedFrom,'literature','reimplemented from',status='Documented')

# Concise paraphrases of the cited textbook, connected to concrete model quantities below.
concepts = [
 ('deer','Mule deer population','Mule deer form the prey population in the Kaibab example.'),
 ('predators','Predator population','Predators remove deer through predation; prey availability affects predator growth.'),
 ('forage','Available forage','Forage is a renewable resource consumed by deer.'),
 ('capacity','Resource-limited carrying capacity','Available forage constrains the deer population that can be sustained.'),
 ('predation','Predation','Deer losses depend on predators and a response to deer density.'),
 ('regrowth','Forage regeneration','Forage regrowth replenishes biomass, with growth limited by capacity.'),
 ('consumption','Herd forage consumption','Total consumption combines herd size and intake per animal.'),
 ('policy','Predator-removal policy','Hunting removes predators after a chosen start year.'),
 ('overshoot','Overshoot and collapse','Resource depletion can follow population growth beyond sustainable levels.'),
 ('feedback','Feedback and interdependence','Changes in populations and resources affect subsequent rates of change.'),
 ('initial-state','Initial state','Stocks require initial quantities to start a simulation.'),
 ('reference-mode','Historical reference mode','A historical population trajectory is used to compare model behavior.'),
]
for key,label,definition in concepts:
    add('concept/'+key,label,'Concept',definition,[SKOS.Concept],[dict(label='Textbook · Chapter 4',url=CHAPTER)],status='Literature')
    lit('concept/'+key,SKOS.prefLabel,label);lit('concept/'+key,SKOS.definition,definition)
    edge('concept/'+key,SKOS.inScheme,'vocabulary','in vocabulary')
    edge('literature',SD.informs,'concept/'+key,'informs',status='Literature')
    edge('model',SD.illustrates,'concept/'+key,'illustrates',status='Interpreted')

tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',REV],cwd=ROOT,text=True).splitlines()
files=[p for p in tracked if p.startswith(('models/','runners/','scripts/','results/','docs/','tests/','.github/workflows/')) and not p.endswith('.gitkeep')]
files += ['README.md','CITATION.cff','LICENSE','REUSE.toml']
for path in files:
    data=read(path,True)
    add('file/'+path,Path(path).name,'File',f'Versioned repository artifact: {path}',[SCHEMA.MediaObject],[src(path)],path=path,revision=REV,size=len(data),sha256=hashlib.sha256(data).hexdigest(),status='Extracted')
    for prop,value in [(SD.path,path),(SD.revision,REV),(SD.sha256,hashlib.sha256(data).hexdigest())]:lit('file/'+path,prop,value)
    ref('file/'+path,SCHEMA.contentUrl,source(path));edge('file/'+path,DCT.isPartOf,'repository','part of repository')
edge('file/models/kaibab_ecosystem_model.mdl',SD.representsModel,'model','implements specification')
edge('file/models/config/parameters/basic_parameters.cin',PROV.wasDerivedFrom,'file/models/config/parameters/basic_parameters.csv','generated from',status='Documented')
for path in ['models/config/parameters/basic_parameters.cin','models/config/parameters/initial_stock_parameters.xlsx']:
    edge('file/models/kaibab_ecosystem_model.mdl',SD.inputFile,'file/'+path,'reads input',status='Documented')

model_path='models/kaibab_ecosystem_model.mdl'
text=read(model_path)
model_text=text.split('\\\\\\---///')[0]
variables=[]
offset=0
for block in model_text.split('|'):
    start=offset;offset+=len(block)+1
    parts=block.split('~')
    if len(parts)<3:continue
    head=parts[0].replace('{UTF-8}','').strip()
    if not head or head.startswith('*'):continue
    head=re.sub(r'\\\s*\n',' ',head)
    head=re.sub(r'\s+',' ',head).strip()
    if '=' in head:name,eq=[x.strip() for x in head.split('=',1)]
    elif head.startswith('Lookup '):name,eq=head.split(' (',1);eq='('+eq
    else:name,eq=head,''
    unit=parts[1].strip().split(' [')[0].strip()
    desc=re.sub(r'\s+',' ',parts[2].replace('\\',' ')).strip()
    line=text[:text.find(name,start)].count('\n')+1
    kind=('Stock' if eq.startswith('INTEG') else 'Lookup' if name.startswith('Lookup ') else 'Initial condition' if name.startswith('Initial ') else 'Control' if name in ['FINAL TIME','INITIAL TIME','TIME STEP','SAVEPER'] else 'Parameter' if eq==':NA:' or re.fullmatch(r'-?[\d.]+',eq) else 'Reference series' if name=='Historical Deer BOT' else 'Flow' if name in ['Deer Net Growth Rate','Deer Predation','Net Annual Forage Growth','Forage Consumed per Deer','Net Predator Growth Rate','Predators Hunted'] else 'Auxiliary')
    typ=SD[{'Initial condition':'InitialCondition','Reference series':'ReferenceSeries','Lookup':'LookupFunction'}.get(kind,kind)]
    key='variable/'+slug(name)
    add(key,name,kind,desc or 'Initial forage quantity, read from the configured workbook.',[typ]+([] if kind=='Lookup' else [M4I.NumericalVariable]),[src(model_path,line)],unit=unit,equation=eq,line=line,status='Extracted',bindings=[],values={})
    lit(key,SD.equation,eq);lit(key,SD.sourceUnit,unit);lit(key,SD.sourceLine,line)
    if kind!='Lookup':lit(key,M4I.hasVariableDescription,entities[key]['definition']);lit(key,M4I.hasSymbol,name)
    edge(key,SD.declaredIn,'file/'+model_path,'declared in');edge('model',SD.hasVariable,key,'has variable')
    # Each implementation symbol is linked to its own reusable vocabulary concept.
    concept='term/'+slug(name)
    pref={'Forage Consumed per Deer':'Total herd forage consumption rate','Deer Density':'Normalized deer density','Normal Deer Density per Acre':'Reference deer density per thousand acres'}.get(name,name)
    add(concept,pref,'Vocabulary term',entities[key]['definition'],[SKOS.Concept],[src(model_path,line)],status='Interpreted',implementation=key)
    lit(concept,SKOS.prefLabel,pref);lit(concept,SKOS.definition,entities[key]['definition'])
    if pref!=name:lit(concept,SKOS.altLabel,name)
    edge(concept,SKOS.inScheme,'vocabulary','in vocabulary');edge(key,SD.denotesConcept,concept,'denotes concept',status='Interpreted')
    if kind!='Lookup':
        u='unit/'+slug(unit)
        if u not in entities:add(u,unit,'Unit','Model-native unit expression. Species counts and thousand-acre scale are preserved; no unverified external unit equivalence is asserted.',[QUDT.Unit])
        edge(key,M4I.hasUnit,u,'has unit')
    variables.append(key)

names={entities[k]['label']:k for k in variables}
for key in variables:
    eq=entities[key]['equation']
    # Remove strings and match longest complete names first, preventing substring dependencies.
    remaining=re.sub(r"'[^']*'",'',eq)
    for name in sorted(names,key=len,reverse=True):
        pattern=r'(?<![A-Za-z0-9_])'+re.escape(name)+r'(?![A-Za-z0-9_])'
        if re.search(pattern,remaining) and names[name]!=key:
            edge(key,SD.dependsOn,names[name],'depends on');remaining=re.sub(pattern,' ',remaining)
    if entities[key]['kind']=='Stock':
        match=re.match(r'INTEG\(\s*(.*?)\s*-\s*(.*?)\s*,\s*(.*?)\s*\)',eq)
        assert match,eq
        for name,prop,label in [(match[1],SD.inflowTo,'inflow to'),(match[2],SD.outflowFrom,'outflow from'),(match[3],SD.initializes,'initializes')]:edge(names[name.strip()],prop,key,label)

mapping={'deer':['Deer Population','Deer Net Growth Rate'],'predators':['Predator Population','Net Predator Growth Rate'],'forage':['Forage Biomass'],'capacity':['Kaibab Deer Carrying Capacity','Kaibab Forage Carrying Capacity','Deer Carrying Capacity in Years'],'predation':['Deer Predation','Baseline Annual Kills per Predator','Deer Density'],'regrowth':['Net Annual Forage Growth','Actual Biomass Growth Fraction'],'consumption':['Forage Consumed per Deer','Actual Consumption per Deer','Desired Consumption per Deer'],'policy':['Predators Hunted','Fraction Predators Killed per Year','Program Start Year'],'reference-mode':['Historical Deer BOT'],'initial-state':['Initial Deer Population','Initial Predator Population','Initial Forage Biomass']}
for concept,vs in mapping.items():
    for name in vs:edge(names[name],SD.denotesConcept,'concept/'+concept,'scientific meaning',status='Interpreted')

mechanisms=[
 ('resource-pressure','Resource pressure and deer growth','The model computes deer carrying capacity from forage biomass, desired intake, and a required forage horizon. As the herd approaches that capacity, its net growth rate decreases; above capacity it can become negative. This is an interpretation of the implemented equations.', 'capacity',['Forage Biomass','Kaibab Deer Carrying Capacity','Ratio of the Deer Population to Carrying Capacity','Kaibab Adequacy to Support the Deer Population','Deer Net Growth Rate','Deer Population']),
 ('consumption-depletion','Consumption and forage depletion','The implemented consumption outflow multiplies the herd size by actual intake per deer. Intake is reduced through a nonlinear lookup when forage becomes scarce. Depletion therefore changes both intake and the capacity supporting future deer growth.', 'consumption',['Deer Population','Forage Consumed per Deer','Actual Consumption per Deer','Effect of Forage Availability on Consumption','Forage Biomass','Kaibab Deer Carrying Capacity']),
 ('predator-response','Predators respond to prey','Normalized deer density drives two separate lookup responses: predator net growth and hunting efficiency. Predator abundance then affects deer predation. The feedback is represented through aggregate populations, not individual animals.', 'predation',['Deer Density','Effect of Deer Density on Predator Births','Effect of Deer Density on Predator Hunting Efficiency','Net Predator Growth Rate','Predator Population','Deer Predation']),
 ('policy-pathway','A policy acts through feedback','The STEP expression activates predator removal at Program Start Year. Removal changes predator abundance, which changes predation pressure on deer. Any later overshoot is a model behavior contingent on the complete parameter set, not a consequence asserted for every intervention.', 'policy',['Program Start Year','Fraction Predators Killed per Year','Predators Hunted','Predator Population','Deer Predation','Deer Population']),
]
for key,label,definition,concept,vs in mechanisms:
    key='mechanism/'+key
    add(key,label,'Mechanism',definition,[SD.Mechanism],[src(model_path,entities[names[vs[0]]]['line']),src('docs/kaibab_example.md')],status='Interpreted')
    edge(key,SD.explainsConcept,'concept/'+concept,'explains concept',status='Interpreted')
    if concept in ['consumption','policy']:edge(key,SD.explainsConcept,'concept/overshoot','helps explain overshoot',status='Interpreted')
    for name in vs:edge(key,SD.involvesVariable,names[name],'involves variable',status='Interpreted')

def binding(var,path,selector,line=None):
    key='binding/'+slug(var+'-'+path+'-'+selector)
    add(key,selector,'Binding','Concrete location of a declaration or input value.',[SD.FileBinding],[src(path,line)],path=path,selector=selector,status='Extracted')
    lit(key,SD.selector,selector);lit(key,SD.revision,REV)
    edge(var,SD.hasBinding,key,'located at');edge(key,SD.inFile,'file/'+path,'in file')
    entities[var]['bindings'].append(dict(file=path,selector=selector,url=source(path,line),id=key))
    return key

for key in variables:binding(key,model_path,'Model symbol: '+entities[key]['label'],entities[key]['line'])
base_values={}
csv_path='models/config/parameters/basic_parameters.csv'
for rowno,row in enumerate(csv.DictReader(io.StringIO(read(csv_path))),2):
    key=names[row['variable_name']];val=float(row['value']);base_values[key]=val
    binding(key,csv_path,f"row variable_name = {row['variable_name']}; column value",rowno)
    cin='models/config/parameters/basic_parameters.cin'; line=next(i for i,s in enumerate(read(cin).splitlines(),1) if s.startswith(row['variable_name']+' ='))
    binding(key,cin,f"assignment: {row['variable_name']}",line)
workbook='models/config/parameters/initial_stock_parameters.xlsx'
wb=openpyxl.load_workbook(io.BytesIO(read(workbook,True)),data_only=True)
for key in variables:
    match=re.search(r"GET XLS CONSTANTS\('([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\)",entities[key]['equation'])
    if match:
        p='models/'+match[1];base_values[key]=wb[match[2]][match[3]].value;binding(key,p,f"sheet '{match[2]}', cell {match[3]}")
overrides={}
casepath='models/config/scenarios/case2.cin'
for line,s in enumerate(read(casepath).splitlines(),1):
    name,val=s.split('=');key=names[name.strip()];overrides[key]=float(val);binding(key,casepath,'assignment: '+name.strip(),line)

for path in files:
    if path.startswith('models/config/lookups/'):
        content=read(path);name=content[:content.index('(')].strip();key=names[name]
        points=[list(map(float,p)) for p in re.findall(r'\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)',content)]
        entities[key]['points']=points;entities[key]['equation']='External table overrides the placeholder in the .mdl file.'
        lit(key,SD.lookupPoints,json.dumps(points));binding(key,path,'lookup table: '+name,1)
binding(names['Historical Deer BOT'],'models/config/timeseries/historical_deer_botg.csv','row label Historical Deer BOT; first row contains years',2)

add('method/system-dynamics','System dynamics simulation','Method','Numerical integration of coupled stocks and their rates of change.',[M4I.Method],[src('docs/kaibab_example.md')])
add('method/rk2','RK2 midpoint integration','Method','Integration method documented for the Vensim comparison. Numerical method is distinct from the ecological model.',[M4I.Method],[src('tests/test_reference.py'),src('docs/pysd_integration.md')],status='Documented')
add('tool/vensim','Vensim','Tool','Simulation tool associated with the committed external-configuration exports. Exact generating version is not recorded here.',[M4I.Tool,SCHEMA.SoftwareApplication],[src('runners/vensim/vensim_run_configuration_external')],status='Documented')
add('tool/pysd','PySD runner','Tool','Repository runner for translating and replaying the model. No new replay was executed while building this atlas.',[M4I.Tool,SCHEMA.SoftwareSourceCode],[src('runners/pysd/run.py'),src('runners/pysd/rk_integrator.py')],status='Documented')
edge('tool/pysd',SD.declaredIn,'file/runners/pysd/run.py','implemented in')
for key in base_values:edge('method/system-dynamics',M4I.hasParameter,key,'has parameter')
for case in ['case1','case2']:
    config='configuration/'+case
    add(config,'Case 1 · baseline' if case=='case1' else 'Case 2 · four overrides','Configuration','Baseline configuration.' if case=='case1' else 'Baseline plus four overrides applied last. Differences cannot be attributed solely to predator removal.',[M4I.Configuration],[src('runners/vensim/vensim_run_configuration_external')]+([src(casepath)] if case=='case2' else []),status='Extracted')
    edge(config,M4I.configures,'tool/vensim','configures')
    for key,base_value in base_values.items():
        value=overrides.get(key,base_value) if case=='case2' else base_value
        entities[key]['values'][case]=value
        a=f'assignment/{case}/{key.split("/")[-1]}'
        v=f'value/{case}/{key.split("/")[-1]}'
        locations=entities[key]['bindings']
        file=casepath if case=='case2' and key in overrides else workbook if entities[key]['kind']=='Initial condition' else 'models/config/parameters/basic_parameters.cin'
        selected=next(b for b in locations if b['file']==file)
        add(a,f'{entities[key]["label"]} = {value:g}','Assignment','Resolved value for this configuration, with its supplying location.',[PIMS.Assignment],[dict(label=selected['selector'],url=selected['url'])],value=value,unit=entities[key]['unit'],case=case,status='Extracted')
        add(v,str(value),'Value','Numerical value scoped to a configuration assignment.',[PIMS.Value]);lit(v,RDF.value,Decimal(str(value)))
        edge(a,M4I.hasVariable,key,'assigns variable');edge(a,M4I.hasAssignedValue,v,'assigns value');edge(config,SD.hasAssignment,a,'includes assignment');edge(a,PROV.wasDerivedFrom,selected['id'],'read from')
        if case=='case2' and key in overrides:edge(a,SD.overrides,'assignment/case1/'+key.split('/')[-1],'overrides')
    run='run/'+case
    add(run,f'{case.title()} · documented Vensim run','Run','Reconstructed from the run configuration and committed result file. Execution time, software version, and original machine are unknown; this is not a verified execution log.',[M4I.ProcessingStep,SD.DocumentedRun],[src('runners/vensim/vensim_run_configuration_external'),src(f'results/runs/{case}_external.csv')],status='Documented')
    edge(run,M4I.usesConfiguration,config,'uses configuration');edge(run,M4I.hasEmployedTool,'tool/vensim','used tool',status='Documented');edge(run,M4I.realizesMethod,'method/rk2','realizes method',status='Documented');edge(run,M4I.investigates,'model','investigates')
    for path in [model_path,workbook,'models/config/parameters/basic_parameters.cin']+[p for p in files if p.startswith('models/config/lookups/')]+([casepath] if case=='case2' else []):edge(run,OBO.RO_0002233,'file/'+path,'has input',status='Documented')
    # Runtime settings use assignments too; simulation calendar is never encoded as prov:startedAtTime.
    for name,value in [('INITIAL TIME',1900),('FINAL TIME',1950),('TIME STEP',0.05),('SAVEPER',0.05)]:
        key=names[name];a=f'assignment/{case}/{slug(name)}';v=f'value/{case}/{slug(name)}'
        add(a,f'{name} = {value}','Assignment','Simulation-time setting reconstructed from the model, not a wall-clock timestamp.',[PIMS.Assignment],[src(model_path,entities[key]['line'])],value=value,case=case,status='Documented')
        add(v,str(value),'Value','Numerical time setting.',[PIMS.Value]);lit(v,RDF.value,Decimal(str(value)))
        edge(a,M4I.hasVariable,key,'assigns variable');edge(a,M4I.hasAssignedValue,v,'assigns value');edge(run,M4I.hasRuntimeAssignment,a,'runtime setting');entities[key]['values'][case]=value
    result='file/results/runs/'+case+'_external.csv'
    edge(run,SD.documentedOutput,result,'documented output',status='Documented')
    # Explicit provenance caveat attached to the assertion prevents the inferred linkage masquerading as a captured execution record.
    statement=uri('assertion/output/'+case)
    for p,o in [(RDF.type,RDF.Statement),(RDF.subject,uri(run)),(RDF.predicate,SD.documentedOutput),(RDF.object,uri(result)),(SD.evidenceStatus,Literal('Documented')),(DCT.source,URIRef(source('runners/vensim/vensim_run_configuration_external')))]:g.add((statement,p,o))

# Output fields are explicitly connected to variables using m4i's Croissant bridge.
series={}
for case in ['case1','case2']:
    path=f'results/runs/{case}_external.csv';rows=list(csv.reader(io.StringIO(read(path))));time=[];series[case]={}
    record='recordset/'+case
    add(record,f'{case.title()} output records','Dataset','Rows in the Vensim export represent variable series; Time rows introduce time axes.',[CR.RecordSet,DCAT.Dataset],[src(path)])
    edge(record,DCT.isPartOf,'file/'+path,'stored in')
    for line,row in enumerate(rows,1):
        if not row:continue
        if row[0]=='Time':time=[float(v) for v in row[2:] if v];continue
        if row[0] not in names:continue
        key=names[row[0]];field='field/'+case+'/'+slug(row[0])
        add(field,row[0]+' output series','Field','A variable series within a Vensim record set.',[CR.Field],[src(path,line)])
        edge(record,CR.field,field,'has field');edge(field,M4I.representsVariable,key,'represents variable')
        binding(key,path,f'row label {row[0]}; preceding Time row defines axis',line)
        if row[0] in ['Deer Population','Predator Population','Forage Biomass']:
            values=[float(v) for v in row[2:] if v]
            assert len(time)==len(values)
            series[case][row[0]]={'time':time[::5],'values':values[::5],'unit':row[1]}

issues=[
 ('consumption-name','A per-deer name for a herd total','Forage Consumed per Deer multiplies Deer Population by Actual Consumption per Deer. Its unit is Metric Tons/Year. The proposed preferred vocabulary label is Total herd forage consumption rate.',[names['Forage Consumed per Deer']], [src(model_path,entities[names['Forage Consumed per Deer']]['line'])]),
 ('density-name','Density is normalized','Deer Density divides population by area and by a reference density. It is dimensionless. Normal Deer Density per Acre is expressed per thousand acres in the model.',[names['Deer Density'],names['Normal Deer Density per Acre']], [src(model_path,entities[names['Deer Density']]['line'])]),
 ('lookup-endpoint','Lookup comment and table disagree','The predator-birth comment describes a multiplier of 1.5 at density 2 or above. The external table ends at (2, 1). This draft preserves the table and flags the discrepancy; it does not silently reconcile them.',[names['Lookup Effect of Deer Density on Predator Births'],names['Effect of Deer Density on Predator Births']],[src('models/config/lookups/effect_deer_density_on_predator_births.cin'),src(model_path,entities[names['Effect of Deer Density on Predator Births']]['line'])]),
 ('section-number','Literature section numbering differs','The repository cites the combined ecosystem model as §4.11; the current online chapter labels it §4.12. Figure 4.19 remains the cited model figure. Source version needs confirmation.',['literature','model'],[src('docs/kaibab_example.md'),dict(label='Current textbook chapter',url=CHAPTER)]),
 ('history','Historical evidence needs a deeper citation','The historical series is described as a reference mode derived from the source graph. Its primary observational provenance and uncertainty have not been established in this review.',[names['Historical Deer BOT']],[src('docs/kaibab_example.md'),src('models/config/timeseries/historical_deer_botg.csv')]),
 ('case-two','Case 2 changes four parameters','Predator removal changes from 0 to 0.2/year, annual kills per predator from 40 to 20, carrying-capacity horizon from 2 to 4 years, and desired consumption from 0.75 to 0.5. The comparison is not a single-factor experiment.',['configuration/case2'],[src(casepath),src(csv_path)]),
 ('execution','Run provenance is reconstructed','Committed result files and run instructions exist. The original execution timestamps and exact generating software version are not recorded by this semantic model. No simulations have been executed for this preview.',['run/case1','run/case2'],[src('runners/vensim/vensim_run_configuration_external')]),
]
for key,label,definition,targets,sources in issues:
    issue='review/'+key;add(issue,label,'Review note',definition,[SD.ReviewIssue],sources,status='Interpreted')
    for target in targets:edge(issue,SD.concerns,target,'concerns');entities[target].setdefault('notes',[]).append(definition)
from overview_model import extend
overview = extend(globals())
from workflow_model import extend as extend_workflow
workflow = extend_workflow(globals())
from inspection_model import extend as extend_inspection
workflows = [workflow, extend_inspection(globals())]
for key,e in entities.items():lit(key,SD.evidenceStatus,e.get('status','Extracted'))
lit('repository',SD.reviewNote,'Repository is private at inspection. Source links may require GitHub access. Proposed entity namespace is not deployed.')
for e in edges:
    if e['status']=='Interpreted':
        statement=uri('assertion/'+hashlib.sha256((e['source']+e['predicate']+e['target']).encode()).hexdigest()[:18])
        for p,o in [(RDF.type,RDF.Statement),(RDF.subject,uri(e['source'])),(RDF.predicate,URIRef(e['predicate'])),(RDF.object,uri(e['target'])),(SD.evidenceStatus,Literal('Interpreted'))]:g.add((statement,p,o))

g.add((uri('dataset'),RDF.type,DCAT.Dataset));lit('dataset',DCT.title,'Kaibab semantic atlas — review draft')
lit('dataset',DCT.description,'Source model comments retain their attribution. Literature interpretations and semantic alignments require human review. Scope: pinned main branch plus the Stella model declaration and reviewed workflow evidence.')
ref('dataset',DCT.license,'https://creativecommons.org/licenses/by-nc-sa/4.0/')
ref('dataset',DCT.source,REPO+'/tree/'+REV)
ref('dataset',DCT.source,REPO+'/tree/'+overview['stellaRevision'])
g.serialize(OUT/'model.ttl',format='turtle')
g.serialize(OUT/'model.jsonld',format='json-ld',indent=2,context={prefix:str(ns) for prefix,ns in g.namespaces()},auto_compact=True)
vg=Graph()
for prefix,ns in g.namespaces():vg.bind(prefix,ns)
for s in list(g.subjects(RDF.type,SKOS.Concept))+[uri('vocabulary')]:
    for triple in g.triples((s,None,None)):vg.add(triple)
vg.serialize(OUT/'controlled-vocabulary.ttl',format='turtle')
schema_graph=Graph()
for prefix,ns in g.namespaces():schema_graph.bind(prefix,ns)
for triple in g:
    if str(triple[0]).startswith(str(SD)) or triple[0]==ontology:schema_graph.add(triple)
schema_graph.serialize(OUT/'vocabulary.ttl',format='turtle')
for filename in ['model.ttl', 'controlled-vocabulary.ttl', 'vocabulary.ttl']:
    path = OUT / filename
    path.write_text(path.read_text().rstrip() + '\n')
model=dict(meta=dict(title='Kaibab semantic atlas',revision=REV,repository=REPO,namespace=BASE,ontology='MathModDB + m4i 1.4.0',version='0.2.0-review',scope=overview['scope'],triples=len(g),variableCount=len(variables),fileCount=sum(e['kind']=='File' for e in entities.values())),overview=overview,workflow=workflow,workflows=workflows,entities=list(entities.values()),edges=edges,series=series)
(OUT/'data/model.json').write_text(json.dumps(model,indent=2))
(OUT/'data/model.js').write_text('window.KAIBAB = '+json.dumps(model,separators=(',',':'))+';\n')
print(json.dumps(dict(entities=len(entities),variables=len(variables),files=sum(e['kind']=='File' for e in entities.values()),relationships=len(edges),triples=len(g)),indent=2))
