"""Scientific overview: explicit MathModDB identities and both implementations.

Local sd: predicates are review proposals, not claimed MathModDB properties.
Only pinned sources are read. No simulations are executed.
"""
import hashlib
import subprocess
import xml.etree.ElementTree as ET
from rdflib import Namespace, RDF, RDFS, OWL, URIRef, Literal

STELLA_REV = '194a8b92e963920e95393accc7d5699348864d85'

def extend(c):
    g, E, edges = c['g'], c['entities'], c['edges']
    add, edge, uri, lit, ref = [c[x] for x in ('add','edge','uri','lit','ref')]
    SD, M4I, SCHEMA, DCT, PROV = [c[x] for x in ('SD','M4I','SCHEMA','DCT','PROV')]
    MARDI=Namespace('https://portal.mardi4nfdi.de/entity/')
    g.bind('mardi',MARDI)
    overview_edges=[]
    def rel(a,p,b,label,show=False):
        edge(a,p,b,label,status='Interpreted')
        if show: overview_edges.append(edges[-1])
    def prop(name,description):
        g.add((SD[name],RDF.type,OWL.ObjectProperty));g.add((SD[name],RDFS.comment,Literal(description)))
    for name,desc in {
        'hasGoverningEquations':'Connects a mathematical model to a collection of its governing formulas.',
        'hasScientificQuantity':'Quantity described by a mathematical model; not a file declaration.',
        'hasParameterGroup':'Collection of configurable scientific and policy quantities.',
        'hasFunctionDefinitions':'Tabulated functions used to specify the equations.',
        'declarationOf':'An implementation-specific declaration represents a scientific quantity. Does not assert identity.',
        'usesQuantity':'A formula involves a scientific quantity.',
        'governs':'A governing equation determines the derivative of a state quantity.',
        'nativeFormatFor':'A model file is in the native format used by this software.',
        'canExecuteTask':'Software is documented as supporting this computational task; no execution is asserted.',
        'solvesModel':'A computational task asks for a numerical solution of this model.',
        'hasSimulationSetup':'Task is specified by a simulation setup plan.',
        'requestsOutput':'A computational task requests these output quantities; no dataset generation is asserted.',
        'offersScenario':'Alternative scenario configuration available for a setup.',
        'hasInitialConditions':'Initial conditions required by a setup plan.',
        'hasNumericalSettings':'Numerical controls and methods required by a setup plan.',
        'offersMethod':'Alternative numerical method, selected according to implementation.',
    }.items(): prop(name,desc)
    for name,desc,parent in [
        ('SimulationSetup','Plan combining a scenario, initial conditions and numerical settings.',PROV.Plan),
        ('OutputSpecification','Specification of requested output quantities, not an observed dataset.',PROV.Plan),
    ]:
        g.add((SD[name],RDF.type,OWL.Class));g.add((SD[name],RDFS.subClassOf,parent));g.add((SD[name],RDFS.comment,Literal(desc)))
    chapter={'label':'Textbook · Chapter 4, §4.12','url':c['CHAPTER']}
    mardi={'label':'MathModDB mathematical-model class','url':'https://portal.mardi4nfdi.de/wiki/Item:Q68663'}
    E['literature']['displayLabel']='System Dynamics\nLearning Guide'
    add('class/mathematical-model','Mathematical model','Ontology class','The mathematical-model class used by MathModDB. The Kaibab model is an instance of this class, not a subclass.',[RDFS.Class],[mardi],external_uri=str(MARDI.Q68663),displayType='MathModDB class',status='Documented')
    g.add((uri('model'),RDF.type,MARDI.Q68663))
    E['model'].update(types=['mardi:Q68663','sd:MathematicalModel'],navigation='explore',displayType='Model instance',definition='A mathematical description of coupled deer, predator and forage dynamics, including predator removal. It is distinct from the two implementation files and any particular simulation execution.')
    rel('model',RDF.type,'class/mathematical-model','is a',True)
    # This documented source relation already exists; reuse it, rather than duplicate it.
    overview_edges.append(next(e for e in edges if e['source']=='model' and e['target']=='literature'))
    quantities=[('deer','Deer population','Deer Population','deer'),('predators','Predator population','Predator Population','predators'),('forage','Forage biomass','Forage Biomass','metric tons')]
    for slug,label,symbol,unit in quantities:
        key='quantity/'+slug
        add(key,label,'Quantity',f'Scientific state quantity represented by the {symbol} stock in both implementations. Units: {unit}. Its initial value and trajectory are distinct from the quantity itself.',[MARDI.Q6534237],[chapter,c['src'](c['model_path'],E[c['names'][symbol]]['line'])],unit=unit,displayType='State quantity · MathModDB',navigation='explore',status='Interpreted')
        rel('model',SD.hasScientificQuantity,key,'has state quantity',True)
        rel(c['names'][symbol],SD.declarationOf,key,'declares quantity')
    def collection(key,label,description,typ=SCHEMA.Collection,kind='Collection',**kw):
        add(key,label,kind,description,[typ],[chapter],navigation='explore',status='Interpreted',**kw)
    collection('overview/equations','Governing equations','Three stock-balance equations determine the changes in deer, predators and forage. Constitutive rate formulas and lookup tables complete the specification.',kind='Formula',displayType='3 balance formulas',equation='dD/dt = Deer Net Growth Rate − Deer Predation\ndP/dt = Net Predator Growth Rate − Predators Hunted\ndF/dt = Net Annual Forage Growth − Total Forage Consumption')
    rel('model',SD.hasGoverningEquations,'overview/equations','has governing equations',True)
    definitions=[('deer','Deer population balance','Deer Population','dD/dt = Deer Net Growth Rate − Deer Predation',['Deer Net Growth Rate','Deer Predation']),('predators','Predator population balance','Predator Population','dP/dt = Net Predator Growth Rate − Predators Hunted',['Net Predator Growth Rate','Predators Hunted']),('forage','Forage biomass balance','Forage Biomass','dF/dt = Net Annual Forage Growth − Total Forage Consumption',['Net Annual Forage Growth','Forage Consumed per Deer'])]
    for slug,label,stock,formula,rates in definitions:
        key='formula/'+slug+'-balance';sources=[c['src'](c['model_path'],E[c['names'][stock]]['line']),chapter]
        add(key,label,'Formula','Governing equation transcribed from the stock declaration. D, P and F are display symbols. Vensim’s Forage Consumed per Deer is the whole-herd consumption rate.',[MARDI.Q96183],sources,displayType='Formula · governing equation',equation=formula,navigation='explore',status='Interpreted')
        lit(key,SD.equation,formula);rel('overview/equations',DCT.hasPart,key,'contains formula');rel(key,SD.governs,'quantity/'+slug,'governs')
        rel(key,SD.declaredIn,'file/'+c['model_path'],'implemented in')
        for rate in rates: rel(key,SD.involvesVariable,c['names'][rate],'uses rate')
    params=[e for e in list(E.values()) if e['kind']=='Parameter' and e['label']!='Auxilliary Time to Deer']
    collection('overview/parameters','Scientific parameters','Eleven configurable scientific and policy quantities. Their identities are distinct from the values assigned by a scenario.',displayType='11 parameter quantities',details=[e['label'] for e in params])
    rel('model',SD.hasParameterGroup,'overview/parameters','has parameters',True)
    for e in params:rel('overview/parameters',DCT.hasPart,e['id'],'includes declaration')
    collection('overview/lookups','Nonlinear responses','Three lookup functions describe how prey density affects predator growth and hunting efficiency, and how forage availability affects consumption. Their points are part of the model specification.',displayType='3 lookup functions')
    rel('overview/equations',SD.hasFunctionDefinitions,'overview/lookups','uses lookup functions',True)
    for e in list(E.values()):
        if e['kind']=='Lookup' and 'Historical' not in e['label']:rel('overview/lookups',DCT.hasPart,e['id'],'includes function')
    # Register the actual Stella file, with its separate revision and content digest.
    stpath='models/kaibab_ecosystem_model.stmx'
    raw=subprocess.check_output(['git','show',f'{STELLA_REV}:{stpath}'],cwd=c['ROOT'])
    tree=ET.fromstring(raw)
    assert len(tree.findall('.//{http://docs.oasis-open.org/xmile/ns/XMILE/v1.0}variables/{http://docs.oasis-open.org/xmile/ns/XMILE/v1.0}stock'))==3
    stsource={'label':'Stella model declaration','url':f'{c["REPO"]}/blob/{STELLA_REV}/{stpath}'}
    file='file/'+stpath
    add(file,'kaibab_ecosystem_model.stmx','File','The Stella Architect model declaration on the inspected stella branch. It declares the three stocks, their flows, algebraic equations and graphical functions.',[SCHEMA.MediaObject],[stsource],path=stpath,revision=STELLA_REV,sha256=hashlib.sha256(raw).hexdigest(),size=len(raw),displayLabel='Stella implementation\nkaibab_ecosystem_model.stmx',displayType='Model declaration · file',status='Extracted')
    for p,v in [(SD.path,stpath),(SD.revision,STELLA_REV),(SD.sha256,hashlib.sha256(raw).hexdigest())]:lit(file,p,v)
    ref(file,SCHEMA.contentUrl,stsource['url'])
    vf='file/'+c['model_path'];E[vf].update(displayLabel='Vensim implementation\nkaibab_ecosystem_model.mdl',displayType='Model declaration · file')
    overview_edges.append(next(e for e in edges if e['source']==vf and e['target']=='model'))
    rel(file,SD.representsModel,'model','implements specification',True)
    for slug,_,_,_ in quantities:rel(file,SD.declarationOf,'quantity/'+slug,'declares quantity')
    for slug,_,_,_,_ in definitions:rel('formula/'+slug+'-balance',SD.declaredIn,file,'implemented in')
    add('tool/stella','Stella Architect','Tool','Authoring and simulation software for the .stmx implementation. The repository also provides an independent Python execution route through PySD.',[M4I.Tool,SCHEMA.SoftwareApplication],[stsource,c['src']('docs/pysd_integration.md')],status='Documented')
    rel(vf,SD.nativeFormatFor,'tool/vensim','native format for',True)
    rel(file,SD.nativeFormatFor,'tool/stella','native format for',True)
    E['tool/pysd'].update(label='Python / PySD',displayType='m4i:Tool',definition='Python execution route for the Vensim and Stella declarations, using the repository runner, input loaders and integration adapters. It translates/adapts a copy of a model; it is not a remote interface driving the original GUI applications.')
    add('task/simulate','Simulate population dynamics','Task','Compute the trajectories of deer population, predator population and forage biomass over 1900–1950. This is a computational task, not a recorded execution. Software choices are alternatives.',[MARDI.Q6534247],[c['src']('docs/pysd_integration.md'),chapter],displayType='Computational task · MathModDB',navigation='explore',status='Interpreted')
    rel('task/simulate',SD.solvesModel,'model','numerically solves',True)
    for tool in ['tool/vensim','tool/stella','tool/pysd']:rel(tool,SD.canExecuteTask,'task/simulate','can perform',True)
    add('overview/setup','Simulation setup','Configuration','A plan selecting the implementation-specific inputs, one scenario, initial conditions, integration method, time interval and output sampling. It is not an execution log.',[SD.SimulationSetup],[c['src']('docs/pysd_integration.md')],displayType='Setup plan',navigation='explore',status='Interpreted')
    rel('task/simulate',SD.hasSimulationSetup,'overview/setup','specified by',True)
    collection('overview/scenarios','Scenario choice','Case 1 uses baseline values. Case 2 changes four values: annual kills per predator 40 → 20; desired consumption 0.75 → 0.5; capacity horizon 2 → 4 years; predator removal 0 → 0.2/year. These labels denote parameter choices, not unique executions.',displayType='Case 1 / Case 2')
    rel('overview/setup',SD.offersScenario,'overview/scenarios','selects scenario',True)
    for case in ['case1','case2']:rel('overview/scenarios',DCT.hasPart,'configuration/'+case,'has option')
    collection('overview/initial','Initial conditions','At 1900: 4,000 deer, 100 predators and 317,000 metric tons of forage. Vensim reads the workbook cells C7, C11 and C9 on the Kaibab Variables sheet. Stella declares stock initial values and supports imported overrides.',displayType='D₀ = 4,000 · P₀ = 100 · F₀ = 317,000')
    rel('overview/setup',SD.hasInitialConditions,'overview/initial','sets initial state',True)
    for key in ['initial-deer-population','initial-predator-population','initial-forage-biomass']:rel('overview/initial',DCT.hasPart,'variable/'+key,'includes condition')
    collection('overview/numerics','Time & integration','1900–1950; time step 0.05 year. The documented Vensim method is RK2 midpoint, while the Stella workflow uses RK2 Heun. The Python runner reproduces the appropriate convention, including STEP handling.',displayType='1900–1950 · Δt = 0.05 year')
    E['overview/numerics']['sources']=[c['src']('docs/pysd_integration.md')]
    rel('overview/setup',SD.hasNumericalSettings,'overview/numerics','sets numerics',True)
    add('method/rk2-heun','RK2 Heun integration','Method','Second-order integration convention documented for the Stella workflow; distinct from the Vensim midpoint convention.',[M4I.Method],[c['src']('docs/pysd_integration.md')],status='Documented')
    for key in ['method/rk2','method/rk2-heun']:rel('overview/numerics',SD.offersMethod,key,'method option')
    for name in ['INITIAL TIME','FINAL TIME','TIME STEP','SAVEPER']:rel('overview/numerics',DCT.hasPart,c['names'][name],'has time setting')
    collection('overview/outputs','Population & forage trajectories','Requested numerical results: deer population, predator population and forage biomass over time. Existing committed outputs are linked as examples, with documented rather than captured run provenance.',typ=SD.OutputSpecification,kind='Dataset',displayType='Requested outputs')
    rel('task/simulate',SD.requestsOutput,'overview/outputs','requests outputs',True)
    for slug,_,_,_ in quantities:rel('overview/outputs',SD.usesQuantity,'quantity/'+slug,'reports quantity')
    for case in ['case1','case2']:rel('overview/outputs',DCT.relation,'recordset/'+case,'documented example')
    # Class display has an external identity, all other statements remain in the draft namespace.
    return dict(entities=list(dict.fromkeys(x for e in overview_edges for x in (e['source'],e['target']))),edges=overview_edges,stellaRevision=STELLA_REV,scope='Scientific overview proposal; selected Stella declaration and workflow evidence added. Full Vensim inventory retained; full Stella symbol mapping is future work.')
