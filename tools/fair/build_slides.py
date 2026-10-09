# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""Adapt the pinned 52-slide lecture in place; record every content substitution."""
from pathlib import Path
from copy import deepcopy
from html import escape
import difflib
import hashlib
import json
import re
import tomllib
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/slides'
REFERENCE = Path(__file__).with_name('reference') / 'awesome-sim.html'
REFERENCE_SHA = 'e354ef2e567223ab8ba6eaac3d572d589efb5ab8'
REPO = 'https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation'
BLOB = REPO + '/blob/__REVISION__/'
SITE = 'https://fair-systemdynamics.github.io/fair-hunter-prey-simulation/'
STATE = json.loads((ROOT/'docs/fair/publication.json').read_text())
VERSION = tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
PUBLISHED = STATE['status'] == 'published'
INSTALL_REF = 'v'+VERSION if PUBLISHED else '__REVISION__'
INSTALL = f'python -m pip install "fair-hunter-prey[teaching] @ git+{REPO}@{INSTALL_REF}"'
CONCEPT = STATE['concept_doi'] or 'Concept DOI: awaiting first release'
DOI = STATE['version_doi'] or 'Version DOI: awaiting first release'
CONCEPT_URL = 'https://doi.org/'+STATE['concept_doi'] if PUBLISHED else BLOB+'docs/fair/release.md'
DOI_URL = 'https://doi.org/'+STATE['version_doi'] if PUBLISHED else BLOB+'docs/fair/release.md'
C = 'case-study adaptation'
F = 'verified factual correction'
O = 'operational update'
soup = BeautifulSoup(REFERENCE.read_text(), 'html.parser')
slides = soup.select('.slides > section')
original = [deepcopy(s) for s in slides]
changes = {i:[] for i in range(1,53)}
ids = ['title','recap','agenda','why-fair','running-example','findable-accessible','f1','zenodo-webhook','version-identifiers','metadata-principles','citation-codemeta','access-protocols','retrieve-install','authentication','access-boundaries','persistent-metadata','archives','fa-recap','practical1','discover','discovery-reflection','interoperable','i1','formats','api-example','i2','qualified-references','codemeta-references','controlled-vocabulary','dependencies','packaging','practical2','inspect-run','interoperability-reflection','reusable','r1','documentation','licenses','provenance','r2','environments','r3','ci','sustainability','reuse-recap','ro-crate','practical3','crate-exercise','crate-reflection','checklist','services','discussion']

def parsed(html): return BeautifulSoup(html, 'html.parser')
def text(node): return node.get_text(' ',strip=True)
def record(n, selector, before, after, category, reason):
    if before != after:
        changes[n].append(dict(selector=selector,category=category,reason=reason,before=before,after=after))
def inner(n, selector, html, category=C, reason='Replace heat-diffusion evidence with the verified hunter–prey counterpart.', index=0):
    node=slides[n-1].select(selector)[index]
    before=node.decode_contents()
    node.clear()
    for child in list(parsed(html).contents): node.append(child)
    record(n,selector+f' [{index}]',before,node.decode_contents(),category,reason)
def replace_text(n, before, after, category=C, reason='Adapt the repository-specific example.'):
    count=0
    for node in list(slides[n-1].find_all(string=True)):
        if before in node:
            node.replace_with(str(node).replace(before,after));count+=1
    if count: record(n,'text',before,after,category,reason)
def attribute(n,selector,name,value,category=C,reason='Link to the corresponding artifact in this repository.'):
    node=slides[n-1].select_one(selector);before=node.get(name,'');node[name]=value
    record(n,selector+' @'+name,before,value,category,reason)
def append(n,selector,html,category=C,reason='Add the case-study evidence while retaining the original teaching content.'):
    node=slides[n-1].select_one(selector)
    for child in list(parsed(html).contents):node.append(child)
    record(n,selector+' append','',html,category,reason)
def col(n,index,html,category=C,reason='Preserve the theory column and adapt the worked example.'):
    inner(n,'.two-col > .col',html,category,reason,index)
def a(url,label,cls=''): return f'<a href="{escape(url)}"'+(f' class="{cls}"' if cls else '')+f'>{label}</a>'
def file(path,label=None):return a(BLOB+path,label or path)
def ul(*items,cls='check'):return '<ul class="'+cls+'">'+''.join('<li>'+i+'</li>' for i in items)+'</ul>'
def p(value,cls=''):return '<p'+(f' class="{cls}"' if cls else '')+'>'+value+'</p>'
def code(value,label,lang='python'):
    return f'<div class="artefact"><div class="file-head"><span>{label}</span><span>{lang}</span></div><pre><code class="language-{lang}">{escape(value)}</code></pre></div>'
def table(headers,rows):return '<table class="compare"><thead><tr>'+''.join('<th>'+x+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'
def mapping():return '<div class="mapping-title">In <code>fair-hunter-prey</code></div>'
def shot(name,alt,caption=''):
    return '<figure class="evidence">'+a('assets/evidence/'+name,f'<img src="assets/evidence/{name}" alt="{escape(alt)}" loading="eager">')+'<figcaption>'+caption+' '+a('assets/evidence/'+name,'Inspect full-size screenshot ↗')+'</figcaption></figure>'
def two(left,right):return '<div class="two-col mt"><div class="col">'+left+'</div><div class="col">'+right+'</div></div>'

# Shell substitutions retain the reference slide classes and all typography/layout assets.
for n,s in enumerate(slides,1):
    s['id']=ids[n-1];s['data-reference-slide']=str(n)
    replace_text(n,'awesome-sim','fair-hunter-prey')
    replace_text(n,'awesome_sim','fair_hunter_prey')
    replace_text(n,'https://github.com/VasiliySeibert/fair-hunter-prey',REPO)
    replace_text(n,'github.com/VasiliySeibert/fair-hunter-prey','github.com/FAIR-systemDynamics/fair-hunter-prey-simulation')
    for node in s.select('a[href]'):
        href=node['href']
        if href.startswith('https://github.com/VasiliySeibert/awesome-sim'):
            suffix=href.split('awesome-sim',1)[1]
            node['href']=REPO+suffix.replace('/tree/gh-pages','/tree/codex/fair4rs-hunter-prey/docs/slides')
            record(n,'a @href',href,node['href'],C,'Update the repository destination.')
    if s.select_one('.mapping-title'):
        inner(n,'.mapping-title',mapping()[len('<div class="mapping-title">'):-6])

for n,section in enumerate(slides,1):
    if section.select_one('a[href="https://www.rd-alliance.org/group/fair-principles-research-software-working-group"]'):
        attribute(n,'a[href="https://www.rd-alliance.org/group/fair-principles-research-software-working-group"]','href','https://www.rd-alliance.org/groups/fair-research-software-fair4rs-wg/outputs/',F,'Replace the retired RDA URL with the official working-group output page, verified 2026-10-09.')
# Opening: preserve title, motivation, and their visual hierarchy.
inner(1,'.hero .subtitle','From shared science in Vensim and Stella to inspectable, citable research artifacts — in 90 minutes.')
inner(1,'.meta',f'''<div><span class="label">Authors</span>Raphael Ginster · Matthias Papesch<br>Vasiliy Seibert<br><span class="presenter">Lecturer: Vasiliy Seibert · {a('https://orcid.org/0000-0002-7121-6816','ORCID')}</span></div><div><span class="label">Running example</span>{a(REPO,'FAIR-systemDynamics/<wbr>fair-hunter-prey-simulation')}<br>{a(CONCEPT_URL,CONCEPT,'doi-status')}</div><div><span class="label">Session</span>90 min · 57 core slides · EN<br>6 optional walkthroughs<br>Lecture: CC BY 4.0 · model evidence: CC BY-NC-SA 4.0</div>''')
# Keep all eight agenda rows and their columns.
for row,time in zip(slides[2].select('tbody tr'),['0:00–0:10','0:10–0:22','0:22–0:34','0:34–0:46','0:46–1:00','1:00–1:12','1:12–1:26','1:26–1:30']):
    old=row.select_one('td').decode_contents();row.select_one('td').string=time
    record(3,'agenda time',old,time,O,'Allow ten minutes for the five added case-study slides while keeping a 90-minute session.')
replace_text(3,'Opening & recap','Opening, recap & shared model')
replace_text(3,'Discover porous media','Discover the hunter–prey model')
replace_text(3,'90 min · ~50 slides','90 min · 57 core + 6 optional slides',O)
replace_text(4,'Every downstream study that runs your code shows up in your ORCID profile, CrossRef, Google Scholar.','Citing the archived version gives authors credit. Citation tracking depends on authors, records, and indexing services.',F,'A DOI enables citation; it does not automatically report every use or populate every index.')
replace_text(4,'Pinned deps + an archived snapshot means the paper figures you generated in 2026 can still be regenerated in 2034.','Pinned dependencies + an archived snapshot preserve the context needed to attempt the same computation years later.',F,'Preservation improves future reproducibility without guaranteeing future execution.')
inner(5,'.two-col > .col', '<h3><code>fair-hunter-prey</code> <span class="tag">shared model</span></h3>'+p('A Kaibab ecosystem model implemented in Vensim and Stella Architect. Both implementations share a scientific specification and two cases; their file formats and numerical execution differ.')+'<div class="callout blue">Every theory slide connects a FAIR4RS concept to evidence in this repository — from the CI badge to the Zenodo release workflow and <code>CITATION.cff</code>.</div>'+shot('stella-case2.jpg','Existing Stella Architect model screenshot','Existing native evidence; no new native execution.')+'<div class="links">'+a(REPO,'GitHub · fair-hunter-prey-simulation','chip-link gh')+' '+a(CONCEPT_URL,CONCEPT,'chip-link doi')+'</div>',index=0)
inner(5,'.two-col > .col',shot('repository.jpg','Hunter–prey repository with metadata and teaching entry points','Review-branch repository evidence. DOI publication follows approval of the exact release commit.')+p(file('docs/fair/README.md','Runnable examples')+' · '+a(SITE,'Semantic model and vocabulary'),'small'),index=1)

# F and A: retain principle quotations and general explanations.
replace_text(7,'keeps resolving forever','is maintained for persistent resolution',F,'Persistence is a stewardship commitment, not a guarantee of eternal availability.')
col(7,1,mapping()+ul(f'<strong>Concept DOI</strong>: {a(CONCEPT_URL,CONCEPT)} → F1 / F1.1.',f'<strong>Version DOI</strong>: {a(DOI_URL,DOI)} → F1.2.',f'<strong>v{VERSION}</strong> identifies the first planned archived software release; prior teaching tags remain distinct.','Identify the scientific model, Vensim/Stella source, Case 1/2 configuration, and each recorded run separately.')+'<div class="callout blue">One project · distinct versions · traceable research objects.</div>')
# DOI anatomy retains its concrete published reference as an explicitly labelled teaching example.
append(8,'.two-col > .col',p('Anatomy example: the published awesome-sim DOI. The hunter–prey DOI is '+('linked below.' if PUBLISHED else 'issued after the reviewed release.'),'small muted'),O,'Retain the useful real DOI anatomy without falsely assigning the reference DOI to this repository.')
inner(8,'.two-col > .col:first-child p.small','A DOI is designed for long-term resolution through maintained registration and repository services, independently of a GitHub URL.',F,'Remove an absolute persistence guarantee.')
inner(8,'.two-col > .col:nth-child(2)', '<h3>How you get one · live demonstration</h3>'+ul('Connect the repository in '+a('https://zenodo.org/account/settings/github/','Zenodo’s GitHub settings')+'. The switch installs the release webhook.',f'Review authors, licenses and <code>.zenodo.json</code>; approve the exact source commit for <code>v{VERSION}</code>.','Create a GitHub release from that commit. Verify the delivery and Zenodo record before claiming a DOI.','Keep main and the live semantic site unchanged; the release uses the reviewed branch snapshot.')+'<div class="links">'+a('https://zenodo.org/account/settings/github/','Zenodo · GitHub settings','chip-link zen')+'</div>'+code('reviewed commit → GitHub release\n→ release webhook → Zenodo archive\n→ verify concept DOI + version DOI','git → GitHub → Zenodo','text')+p(file('docs/fair/release.md','Release checklist')+' · '+a(CONCEPT_URL,CONCEPT),'small'))
replace_text(9,'never changes.','identifies one archived version.',F)
replace_text(9,'so the exact inputs are reproducible in 10 years.','so readers can identify the exact archived version and its inputs.',F)
inner(9,'.two-col > .col:nth-child(1) p:last-child','Git teaching milestones <code>v0.1-scaffold</code> through <code>v0.6-verification</code> document development. They are not Zenodo deposits.')
col(9,1,'<h3>Hunter–prey release identities</h3>'+table(['Level','Identifier','Meaning'],[['Concept',a(CONCEPT_URL,CONCEPT),'Project across archived versions'],[f'v{VERSION}',a(DOI_URL,DOI),'Exact reviewed software snapshot'],['Execution','Implementation + case + source hash','A particular PySD run']])+p('A single release establishes both a project-level and a version-level identifier. Future releases receive distinct version DOIs.','small'))
col(10,1,mapping()+ul(file('CITATION.cff')+' — GitHub’s citation entry point.',file('codemeta.json')+' — structured software metadata and qualified references.',file('.zenodo.json')+' — creators, version, licensing and related literature for Zenodo.',f'DOI and CI badges make publication and verification evidence visible. Publication status: <strong>{escape(STATE["status"])}</strong>.')+p('Metadata supports discovery; actual indexing and search results must be checked.','small'),F,'Preserve the metadata lesson while removing unsupported claims of automatic indexing and completion.')
inner(11,'pre code','cff-version: 1.2.0\ntype: software\ntitle: fair-hunter-prey-simulation\nversion: '+VERSION+'\nauthors:\n  - family-names: Ginster\n    given-names: Raphael\n  - family-names: Papesch\n    given-names: Matthias\n  - family-names: Seibert\n    given-names: Vasiliy\n# Full file: identifiers, licenses, references',index=0)
inner(11,'pre code',escape(json.dumps({'@context':'https://doi.org/10.5063/schema/codemeta-2.0','@type':'SoftwareSourceCode','name':'fair-hunter-prey-simulation','version':VERSION,'programmingLanguage':'Python','runtimePlatform':['Python 3.12','Python 3.13'],'softwareRequirements':['pysd==3.14.3','pandas>=2.2,<3']},indent=2)),index=1)
for idx in range(2):
    paras=slides[10].select('.two-col > .col')[idx].select('p')
    if paras: inner(11,'.two-col > .col:nth-child('+str(idx+1)+') p',file('CITATION.cff' if idx==0 else 'codemeta.json','Read the complete metadata')+' · Zenodo uses .zenodo.json when both files are present.',O,'Link the real files and document the actual Zenodo metadata precedence.')
col(12,1,mapping()+ul('<code>git clone</code> over HTTPS retrieves models, configurations, readers and history.','<code>pip install</code> installs the package and PySD execution route.',('The verified Zenodo archive is retrievable over HTTPS.' if PUBLISHED else 'Zenodo archive retrieval becomes available after the first approved release.'),'Text, CSV, HTML and SVG can be inspected openly. Native editing and execution depend on the relevant vendor tool.')+p('Standard retrieval protocols and native application access are separate questions.','small'))
inner(13,'pre code',escape('# (a) clone — full history\ngit clone '+REPO+'\n\n# (b) install the exact reviewed snapshot\n'+INSTALL+'\n\n# (c) archived release\n# '+(DOI_URL if PUBLISHED else 'Zenodo archive: pending reviewed release')),O,'Use an actual commit before publication; switch to the verified tag and DOI only after release.')
replace_text(13,'Private FTP? Proprietary portal requiring a PDF application? Not A1.1.','Check the retrieval protocol separately from authentication and vendor application requirements.',F)
col(14,1,mapping()+ul('Public model sources and saved results can be retrieved without login.','GitHub authentication supports contributions and release administration.','Zenodo connects through GitHub OAuth; the hosted Jupyter service has its own sign-in.','Vendor applications have separate access terms. Proprietary software does not always mean paid access.'))
inner(15,'pre code','gh auth login\ngh repo clone OWNER/PRIVATE-REPOSITORY\n\n# CI: use the workflow-scoped GITHUB_TOKEN\n# for GitHub operations; OIDC for supported\n# external cloud identity federation.',F,'Avoid embedding credentials in clone URLs and distinguish GitHub tokens from cloud OIDC.')
replace_text(15,'Practical 1 uses OAuth to log into the Betty Research Engine via GitHub — you will see A1.2 in action.','Betty may offer GitHub sign-in for broader results. Native Vensim/Stella access is a separate software requirement.',O)
col(16,1,mapping()+ul('Archive a reviewed source snapshot with authors, licenses and environment information.','Preserve citation metadata even if future native software access changes.','Check Zenodo deposit and Software Heritage ingestion separately; record only observed identifiers.','Keep the original saved results inspectable alongside the model sources.')+p(file('docs/fair/release.md','Publication and preservation checklist'),'small'))
replace_text(17,'must remain resolvable forever','should remain accessible',F)
replace_text(17,'Already crawls all of GitHub, GitLab, PyPI, Debian, …','Archives software from many supported origins; verify ingestion for the specific repository.',F)
replace_text(17,'content-addressed forever.','content-addressed identifiers.',F)
inner(17,'pre code','swh:1:dir:…   # directory identifier shape\nswh:1:rev:…   # revision identifier shape\nswh:1:snp:…   # snapshot identifier shape\n\n# Illustrative syntax, not issued identifiers.\n# Check this repository’s archival status.',F,'Do not present illustrative SWHID syntax as a verified archived object.')
replace_text(17,'fair-hunter-prey on Software Heritage','Software Heritage identifier shapes')
replace_text(17,'resolves even if GitHub is gone.','Verify the archived content independently of GitHub.',F)
inner(18,'.three-col > :nth-child(3)', '<h3>Your repo today has</h3>'+p('<code>CITATION.cff</code>, <code>codemeta.json</code>, environment locks and preserved examples. The first DOI follows the reviewed release.'))
inner(18,'.recap','<h3>Bring to Practical 1</h3><p>FAIR metadata helps search engines describe and index software. Next: step into the shoes of a <em>consumer</em>. What does Betty actually find, and what evidence can you inspect directly?</p>',F,'Metadata does not guarantee rank 1 or any particular search result.')
# Practical 1: preserve search, sort, export, inspect, and reflection.
replace_text(20,'14 min','12 min',O,'Rebalance the schedule around the added scientific introduction.')
inner(20,'h1','Find the hunter–prey model in 12 minutes')
inner(20,'.task-list',''.join('<li>'+x+'</li>' for x in [
 'Open the '+a('https://software.nfdi4ing.de/','Betty Research Engine')+'.',
 'Search for <code>fair-hunter-prey-simulation</code>, then <code>system dynamics</code>.',
 'Inspect the search sources. Use GitHub search or sign-in where the service offers them.',
 'Sort by citations if available. Record the result source and missing fields.',
 'Export the result set as JSON if available; record the query and date.',
 'Find this repository, or record the indexing gap and follow the '+a(REPO,'direct GitHub link')+'.',
 'Inspect authors, version, license and citation metadata. Follow the literature, both implementations, and Case 1/2 inputs.',
 'Follow the '+a(CONCEPT_URL,'Zenodo publication evidence')+'. Does a citation count measure scientific quality or only observed citations?'
]))
inner(21,'h1','What made the hunter–prey model findable?')
inner(21,'.callout','<strong>Prompt:</strong> Which fields did Betty expose? Which came from GitHub or Zenodo? Which were absent? Compare what the repository declares with what the search service actually indexed.',F,'Replace unsupported rank-1 claims with observed discovery evidence.')
replace_text(21,'SPDX id + semver tag — without these, aggregators de-rank the record.','SPDX identifiers and release versions describe reuse conditions and the source snapshot.',F)
replace_text(21,'Populated by CrossRef/DataCite once the DOI is minted and cited back.','A citation count depends on the index and the citing records it has collected.',F)
inner(21,'.recap','<h3>Takeaway</h3><p>Rich metadata improves discoverability and interpretation. Missing search results are indexing evidence, not a verdict on the model. Follow direct references when a new repository is not yet indexed.</p>',F,'Remove unverified guarantees about search ranking and discoverability.')

# I: keep the general standards and qualified-reference teaching examples.
col(23,1,mapping()+ul('<strong>Model sources:</strong> text-based Vensim <code>.mdl</code>; XML/XMILE in Stella <code>.stmx</code>.','<strong>Inputs:</strong> existing .cin, CSV and workbook files; shared scientific quantities, different representations.','<strong>Results:</strong> CSV readers preserve headers, units and independent time axes before pandas/Matplotlib analysis.','<strong>Execution:</strong> PySD translates copies of either implementation using the existing compatibility adapters.')+p('An OpenAPI service remains an illustrative option, shown next.','small'))
# Keep the original four-row formats comparison; add the concrete lesson below it.
append(24,'.callout','<br><strong>Here:</strong> Vensim trajectories and historical data can have different time axes. Stella Case 2 contains final values only. A CSV extension alone does not define these semantics.')
inner(25,'pre code',escape('openapi: 3.1.0\ninfo: {title: Kaibab results API, version: 0.1.0}\npaths:\n  /results/{implementation}/{case}:\n    get:\n      summary: Inspect saved simulation evidence\n      parameters:\n        - {name: implementation, in: path, required: true,\n           schema: {type: string, enum: [vensim, stella]}}\n        - {name: case, in: path, required: true,\n           schema: {type: string, enum: [case1, case2]}}\n      responses:\n        "200":\n          description: Values, units, time axes and export kind'))
append(25,'.two-col > .col:nth-child(2)',p('<strong>Illustrative design; no HTTP service is implemented.</strong> A response must distinguish <code>trajectory</code> and <code>final-values</code>. The working interfaces are the Python API, CLI and CSV readers.','small'),O,'Retain OpenAPI teaching without inventing a deployed API.')
col(26,1,mapping()+ul('Authors: verified '+a('https://orcid.org/0000-0003-2394-7064','Raphael Ginster ORCID')+' and '+a('https://orcid.org/0000-0002-7121-6816','Vasiliy Seibert ORCID')+'; no invented identifier for Matthias Papesch.','Original model: '+a('https://pressbooks.lib.jmu.edu/sdlearningguide/','Deaton & MacDonald, System Dynamics Learning Guide')+'.','Licensing: SPDX identifiers and '+file('REUSE.toml','per-file mappings')+'.','Scientific meaning: '+a(SITE+'#workflows/term%2Ffraction-predators-killed-per-year','predator-removal concept')+' linked to declarations and assignments.'))
# Preserve Alice/ORCID, SPDX and PyPI comparison; clarify the software-reference principle.
append(27,'.two-col > .col:nth-child(2)',p('Author/license references illustrate I2. The dependency row illustrates R2, the specific principle for other software.','small'),F,'Separate I2 object references from R2 software references.')
meta=json.loads((ROOT/'codemeta.json').read_text())
meta_excerpt={k:meta[k] for k in ('@context','@type','name','version','codeRepository','programmingLanguage','runtimePlatform')}
meta_excerpt['author']=[{'@type':'Person','name':x['givenName']+' '+x['familyName'],**({'@id':x['@id']} if '@id' in x else {})} for x in meta['author']]
inner(28,'h1','<code>codemeta.json</code> — line by line<span class="fair-pill I">I2</span>')
inner(28,'pre code',escape(json.dumps(meta_excerpt,indent=2)))
col(28,1,'<h3>Every URL identifies its subject</h3>'+ul('Repository URL — current source and collaboration.','Version and DOI — the released research artifact.','SPDX — per-file license semantics.','ORCID — verified person identity.','Literature and concept URI — scientific context.','PyPI references — dependencies, under R2.')+p(file('codemeta.json','Complete CodeMeta file')+' · '+file('.zenodo.json','Zenodo creators and related identifiers'))+'<div class="back-ref">← Lecture 3 · CodeMeta &amp; Metadata4Ing</div>')
# Keep the ambiguity/credit explanation and example/code split, replacing heat diffusion.
col(29,0,'<h3>The ambiguity problem</h3>'+p('Two files name <strong>“Fraction Predators Killed per Year”</strong>. Does a value describe the scientific quantity, a model declaration, or a scenario assignment?')+ul('Scientific concept: annual predator-removal fraction, with its declared meaning and unit.','Case 1 assignment: <strong>0</strong>; Case 2 assignment: <strong>0.2</strong>.','Vensim and Stella encode those assignments in different files.',cls='')+'<h3>The credit problem</h3>'+p('A resolvable concept URI identifies the definition being reused. Cite the literature and vocabulary source rather than leaving the meaning implicit.')+'<div class="back-ref">← Lecture 3 · controlled vocabularies for data</div>',C,'Use the actual shared concept and distinguish scientific meaning from a file assignment; free text is not itself a claim of inventing a concept.')
col(29,1,'<div class="service-chip ts">Semantic model · controlled vocabulary</div>'+shot('vocabulary.jpg','Controlled-vocabulary entry for the annual predator-removal fraction','Local vocabulary term, explicitly a review draft.')+p(a(SITE+'#workflows/term%2Ffraction-predators-killed-per-year','Open the concept')+' · '+a(SITE+'#workflows/assignment%2Fcase2%2Ffraction-predators-killed-per-year','Follow its configuration binding'))+p('Case 2: '+file('models/config/scenarios/case2.cin','Vensim .cin')+' · '+file('examples/stella-source/models/config/parameters/kaibab_ecosystem_parameters_stella_scenario2.csv','Stella CSV'),'small'))
append(29,'.two-col > .col:nth-child(1)', code('Vensim .cin: Fraction Predators Killed per Year = 0.2\nStella CSV:  Fraction Predators Killed per Year,0.2','Case 2 · two bindings of one concept','text')+p('The selected assignment is hashed into each run record; the inspected data keeps its implementation and case identity.','small'))
replace_text(27,'Which version of NumPy, how constrained?','Which version of pandas, how constrained?')
for n in (30,31,34):
    replace_text(n,'I2','R2',F,'FAIR4RS R2 covers qualified references to other software; retain the lesson at its original point in the sequence.')
    for badge in slides[n-1].select('.fair-pill.I'):badge['class']=['fair-pill','R']
replace_text(30,'numpy>=1.26,<2.0','pandas>=2.2,<3')
replace_text(30,'numpy','pandas')
replace_text(30,'>=1.26,<2.0','>=2.2,<3')
replace_text(30,'numpy 3.0','a future incompatible version')
replace_text(30,"That's a promise.","That declares the supported range.",F)
inner(31,'pre code',escape('[build-system]\nrequires = ["setuptools>=77,<83", "wheel"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "fair-hunter-prey"\nversion = "'+VERSION+'"\nrequires-python = ">=3.12,<3.14"\ndependencies = [\n  "pysd==3.14.3", "pandas>=2.2,<3",\n  "matplotlib>=3.8,<4", "openpyxl>=3.1,<4",\n]'),index=0)
if len(slides[30].select('pre code'))>1:inner(31,'pre code',escape(INSTALL),index=1)
replace_text(31,'push tag → installable','an installable commit can be pinned')
replace_text(31,'Publish to PyPI (optional)','Publish to PyPI (optional; not done here)')
replace_text(31,'package name matches imports.','distribution: fair-hunter-prey; import: fair_hunter_prey.')
replace_text(31,'Pin to a git tag:','Pin to the reviewed commit; use v0.7.0 after publication:')
append(31,'.two-col > .col:nth-child(2)',p(file('pyproject.toml','Complete pyproject.toml')+' · Both native implementations are bundled without reorganizing the scientific source tree.','small'))

# Practical 2: actual inspection and all four independently executed cases.
inner(33,'.task-list',''.join('<li>'+x+'</li>' for x in [
 'Open '+a('https://jupyter.nfdi4ing.de','NFDI4Ing Jupyter')+' with Python 3.12/3.13. Install the '+file('docs/fair/README.md','pinned teaching package')+'.',
 'Open '+file('examples/fair/02_interoperability.ipynb','02_interoperability.ipynb')+'. First inspect saved CSV exports with the unchanged readers, pandas and Matplotlib. This performs no simulation.',
 'Run both implementations and both cases through <strong>PySD</strong>. Compare each with its own reference, preserving numerical methods and tolerances.',
 'Inspect package versions. Explain what an absent dependency constraint or a misread final-values export could break. Do not modify the original research inputs.'
]))
inner(33,'pre code',escape('from fair_hunter_prey import inspect_results, run_example\n\ninspect_results("out/inspection")  # saved exports only\nfor implementation in ("vensim", "stella"):\n    for case in ("case1", "case2"):\n        run_example(implementation, case,\n                    f"out/{implementation}-{case}")'))
inner(33,'.file-head','<span>Notebook · inspect exports, then execute with PySD</span><span>Python 3.12 / 3.13</span>')
replace_text(34,'numpy>=1.26,<2.0','pandas>=2.2,<3')
replace_text(34,'works everywhere','uses standard tools on supported platforms',F)
replace_text(34,'No proprietary lock-in.','The Python route is independent; native authoring still uses vendor tools.',F)
append(34,'.recap','<p class="small">Inspecting a CSV and executing a model are different activities. Stella Case 2’s native export contains final values only; a new PySD trajectory is new execution evidence.</p>')

# R: preserve all documentation, licensing, changelog, standards and sustainability lessons.
col(36,1,mapping()+ul(file('README.md')+', '+file('docs/fair/README.md','docs/')+' and '+file('examples/fair/02_interoperability.ipynb','examples/')+' — layered documentation, R1.',file('REUSE.toml')+' — MIT code, CC BY 4.0 documentation, CC BY-NC-SA 4.0 model-derived artifacts, R1.1.',file('CHANGELOG.md')+' and preserved teaching tags — the human-readable history, R1.2.','Execution provenance records the implementation, case, PySD engine, inputs, environment and output hashes.','The '+file('docs/fair/evidence.md','FAIR4RS evidence table')+' links each claim to its evidence.'))
inner(37,'.three-col + .three-col > :nth-child(3) p','An explicit self-audit — the linked FAIR4RS evidence table records this repository’s status.')
append(37,'.three-col + .three-col',p(file('docs/fair/evidence.md','Open the FAIR4RS evidence table'),'small'))
append(38,'.two-col > .col:nth-child(1)',p('<strong>Here:</strong> '+file('REUSE.toml','REUSE maps each file')+' to MIT, CC BY 4.0, or the inherited CC BY-NC-SA 4.0 model license. Vensim and Stella retain their own proprietary terms.','small'))
replace_text(38,'Others legally cannot reuse it, even if the repo is public.','Public visibility alone grants no general reuse license; applicable permissions and exceptions still matter.',F,'Avoid an absolute legal claim while preserving the license lesson.')
inner(39,'pre code',escape('207ca01 fix: identify PySD explicitly in execution output and logs\n2648c8c docs: record FAIR verification and presentation review evidence\nfd82aa2 ci: install the teaching package before the full existing test suite\neaa529e feat: add FAIR4RS lecture and reproducible hunter-prey workflows\n\n# Earlier teaching milestones remain intact.'),index=0)
inner(39,'pre code',escape('# Abridged; read the complete changelog below\n## [0.7.0] — release candidate\n### Added\n- Both implementations and both cases via PySD.\n- Saved-export inspection and RO-Crate examples.\n- FAIR4RS lecture and evidence map.\n### Changed\n- Restore all 52 reference lessons and styling.\n### Preserved\n- Models, configurations, readers and tolerances.'),index=1)
append(39,'.two-col > .col:nth-child(2)',p(file('CHANGELOG.md','Read the full versioned changelog')+' · '+a(REPO+'/commits/codex/fair4rs-hunter-prey','Inspect actual commits'),'small'))
replace_text(39,'Conventional-commit style turns the log itself into a changelog draft.','Descriptive commit messages support a changelog draft; the changelog records the curated story.',F,'Use the real history rather than inventing or rewriting conventional commit messages.')
col(40,1,mapping()+ul('<code>pysd==3.14.3</code> — translation and simulation with documented feature limits.','<code>pandas&gt;=2.2,&lt;3</code>, <code>matplotlib&gt;=3.8,&lt;4</code>, <code>openpyxl&gt;=3.1,&lt;4</code>.','<code>requires-python = ">=3.12,<3.14"</code>; exact tested teaching locks for both interpreters.','Authority: '+a('https://pypi.org/project/pysd/','PyPI')+' and '+a('https://pysd.readthedocs.io/en/latest/','PySD documentation')+'.','Native Vensim and Stella are separate software dependencies for native authoring/execution.')+p('Package outputs identify PySD and the existing compatibility adapters.','small'))
replace_text(41,'Good enough for a tolerant reuser.','Declares the supported dependency contract.',F)
replace_text(41,'every transitive dep at a concrete version.','every transitive dep at a concrete version. Here: teaching-py312.txt and teaching-py313.txt.')
replace_text(41,'The OS, libc, CUDA, everything.','Records additional OS/runtime layers when actually built and identified. No container image is published here.',F)
inner(41,'pre code',escape('# Illustrative Dockerfile; not a published image\nFROM python:3.13-slim\n# For a frozen build, record a verified base-image digest.\nCOPY dist/fair_hunter_prey-0.7.0-py3-none-any.whl /tmp/\nRUN pip install /tmp/*.whl\nENTRYPOINT ["fair-hunter-prey"]'),O,'Keep container teaching but remove a fake digest and distinguish it from the tested lock files.')
col(42,1,mapping()+ul('<strong>Packaging:</strong> PEP 621 pyproject.toml and an installed-package check.','<strong>Citation:</strong> CFF and CodeMeta with verified creators and references.','<strong>Tests:</strong> existing scientific tests plus four implementation/case combinations.','<strong>CI:</strong> Python 3.12 and 3.13; unchanged reference tolerances.','<strong>Licensing:</strong> REUSE and SPDX, preserving the inherited model terms.'))
replace_text(43,'a tagged GitHub release + a DOI remains installable for years.','a tagged GitHub release + a DOI preserves an identifiable source snapshot; environment checks support reuse.',F)
inner(43,'pre code',escape('name: FAIR teaching verification\non: [push, pull_request]\njobs:\n  verify:\n    strategy:\n      matrix: {python: ["3.12", "3.13"]}\n    runs-on: ubuntu-latest\n    steps:\n      # checkout and locked environment setup\n      - run: python -m pytest -q\n      - run: python tools/fair/check_stella.py\n      - run: python tools/fair/check_materials.py\n      - run: python tools/fair/execute_notebooks.py\n      # build and test wheel outside the checkout'))
append(43,'.two-col > .col:nth-child(1)',p(file('.github/workflows/fair.yml','Read the complete workflow')+' · CI also checks protected-file hashes and both Pages surfaces.','small'))
append(44,'.two-col > .col:nth-child(2)',p('This repository’s '+file('docs/fair/release.md','release checklist')+' records the process. Maintainer responsibilities and support promises must be agreed with the collaborators.','small'))
inner(45,'.recap','<h3>Bring to Practical 3</h3><p>You have inspected saved exports and run an implementation in a fresh Python environment. Now package its source, selected case, actual outputs, licenses and environment together.</p><p>In a disposable copy of the crate, change an output or remove an input. Re-run the hash check and explain why it fails. Discuss how missing licenses and unconstrained dependencies would obstruct reuse.</p>',C,'Keep the failure/reflection exercise while protecting collaborator files and using the implemented crate checks.')
replace_text(46,'Everything needed to regenerate a figure in 2034 is in one crate.','The crate collects the available context needed to attempt regeneration years later.',F)
replace_text(46,'Execute the same crate in Jupyter, Docker, your laptop, or an HPC cluster — the metadata tells each system what it needs.','Inspect the same standard crate across tools. Execution still requires compatible software and dependencies. This practical uses Jupyter.',F,'An RO-Crate is portable metadata and content, not a universal execution runtime.')
replace_text(46,'Deposit the entire crate on Zenodo or Software Heritage once.','Deposit a research-object archive in a suitable repository such as Zenodo; verify source-code archiving separately.',F,'Do not imply that Software Heritage universally archives arbitrary crates and research data.')
inner(48,'h1','Package hunter–prey as a Research Object')
inner(48,'.task-list',''.join('<li>'+x+'</li>' for x in [
 'In '+a('https://jupyter.nfdi4ing.de','Jupyter')+', open '+file('examples/fair/03_ro_crate.ipynb','03_ro_crate.ipynb')+' using the same locked teaching environment.',
 'Select one implementation and case. Generate a fresh PySD run into a separate output directory.',
 'Create the crate. It includes the model, inputs, references, licenses, recorded environment, actual outputs and execution provenance.',
 'Inspect <code>ro-crate-metadata.json</code>. Follow creator identifiers and find the selected scenario.',
 'Verify file hashes; alter only a disposable copy to demonstrate detection of changed evidence.'
]))
inner(48,'.callout',code('from fair_hunter_prey import run_example, create_crate\nrun_example("stella", "case2", "out/crate-run")\ncrate = create_crate("out/crate-run", "out/research-object")\nprint(crate / "ro-crate-metadata.json")','Jupyter · actual execution and packaging')+p('The adapter uses '+a('https://pypi.org/project/rocrate/','rocrate')+' to describe files, authors and provenance.','small'))
replace_text(49,'Run it identically in 2034.','Identify what was actually run and assess future execution requirements.',F)
replace_text(49,'RO-Crate pins the entire execution context:','This crate records the observed execution context:',F)
replace_text(49,'future-proofing your research.','preserving the context needed for future reuse.',F)
replace_text(50,'Indexed by at least one registry (Betty Engine, PyPI, …)','Check actual indexing in a registry or discovery service',F)
replace_text(50,'Software Heritage + Zenodo snapshot','Verify Zenodo deposit and Software Heritage ingestion',F)
replace_text(50,'Qualified references: ORCID, SPDX, ROR, PyPI, Wikidata URIs','Qualified references: ORCID, SPDX, ROR, vocabulary URIs',F)
replace_text(50,'Pinned dependencies with version constraints','Documented CSV meanings, units and time axes',C)
append(50,'.fair-grid > :nth-child(4) ul','<li>Qualified software references and tested dependency locks (R2)</li>',F,'Keep dependency evidence on the checklist under R2.')
inner(50,'p.small','Use the '+file('docs/fair/evidence.md','FAIR4RS evidence table')+' to distinguish implemented, verified and pending items. This checklist supports assessment; it is not a certification.',F)
attribute(51,'a[href="https://www.ing.grid"]','href','https://www.inggrid.org/',F,'Correct the journal’s destination URL.')
inner(52,'.meta > div:nth-child(3)','<span class="label">This deck and example</span>'+a('index.html','Hunter–prey slides (this preview)')+'<br>'+a(REPO,'GitHub repository')+'<br>'+a(CONCEPT_URL,CONCEPT)+'<br>'+a('https://vasiliyseibert.github.io/awesome-sim/','Original awesome-sim lecture')+'<br>CC BY 4.0 lecture; inherited model licensing')
append(52,'.hero',p('Authors: Raphael Ginster · Matthias Papesch · Vasiliy Seibert','closing-authors'))

# Five additive case-study slides and six existing, optional screenshot walkthroughs.
case_source=json.loads((Path(__file__).with_name('reference')/'case-study.json').read_text())
case_titles={'shared-specification':'Shared scientific specification','shared-use-cases':'Shared use cases, tool-specific implementations','artifacts-access':'Tool-specific artifacts and access','two-cases':'Case 1 and Case 2','open-workflows':'Open inspection and independent execution'}
case_slides=[];appendix=[]
for id,raw in case_source.items():
    old=parsed(raw).select_one('section'); s=soup.new_tag('section',id=id)
    s['class']=['content','case-study' if id in case_titles else 'appendix']
    group='Case-study addition' if id in case_titles else 'Optional appendix'
    header=parsed(f'<div class="slide-header"><span class="brand">{group}</span><span class="chip">Vensim · Stella · Case 1 / Case 2</span></div>').div
    s.append(header)
    title=soup.new_tag('h1');title.string=case_titles.get(id,text(old.h1));s.append(title)
    body=old.select_one('.slide-body')
    for child in list(body.contents):s.append(child)
    for c in s.select('.two-col > div'):c['class']=list(c.get('class',[]))+['col']
    for img in s.select('figure'):img['class']=['evidence']
    footer=parsed('<div class="slide-footer"><span class="fair">NFDI4ING · RDM Basics 4</span><span>'+group+'</span></div>').div
    s.append(footer)
    s['data-stage']={'shared-specification':'specification','shared-use-cases':'implementation','artifacts-access':'implementation','two-cases':'configuration','open-workflows':'results'}.get(id,'results')
    note=soup.new_tag('aside',attrs={'class':'notes'})
    old_note=deepcopy(old.select_one('aside.notes'))
    for link in old_note.select('a'):
        href=link['href']
        label=href.rsplit('/',1)[-1].replace('%2F',' / ') or 'Semantic model'
        if 'pressbooks' in href:label='Original scientific specification'
        elif 'pysd.readthedocs' in href:label='PySD documentation'
        elif 'github.com' in href and '/blob/' not in href:label='GitHub repository'
        link.string=label
    for child in list(old_note.contents):note.append(child)
    s.append(note)
    (case_slides if id in case_titles else appendix).append(s)
# Source case-study markup uses a different figure helper; retain clear captions and add primary links.
case_slides[0].append(parsed('<p class="small">'+a(SITE+'#overview','Open the unchanged semantic model')+' · '+a('https://pressbooks.lib.jmu.edu/sdlearningguide/','Original scientific specification')+'</p>').p)
case_slides[1].select_one('tbody').clear()
for row in [
 ['Define','Equations and sketch in .mdl','Equations and views in .stmx (XML/XMILE)'],
 ['View','Native view or exported HTML/SVG','Native view or exported PDF/SVG'],
 ['Document / comment','Model text, variable descriptions, report','Model documentation, equations, screenshots'],
 ['Edit','Vensim authoring tools','Stella Architect authoring tools'],
 ['Configure','Existing .cin, CSV and workbook inputs','Parameter, lookup and historical-data CSVs'],
 ['Execute','Native Vensim engine; separate PySD route','Native Stella engine; separate PySD route'],
 ['Export','Source, documentation and result data','Source, documentation and result data'],
]:case_slides[1].select_one('tbody').append(parsed('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>').tr)
case_slides[2].append(parsed('<p class="small">Proprietary does not always mean paid: '+a('https://vensim.com/vensim-applications/','Vensim Model Reader')+' and '+a('https://www.iseesystems.com/resources/help/v4/Content/Welcome.htm','isee Player')+' offer restricted viewing/runtime workflows. Compatibility with this snapshot was not newly tested.</p>').p)
case_slides[3].select_one('.case-files').clear()
case_slides[3].select_one('.case-files').append(parsed('Vensim: '+file('models/config/parameters/basic_parameters.cin','Case 1 parameters')+' + initial-stock workbook; '+file('models/config/scenarios/case2.cin','Case 2 changes')+'.<br>Stella: '+file('examples/stella-source/models/config/parameters/kaibab_ecosystem_parameters_stella_scenario1.csv','Case 1 parameters')+' / '+file('examples/stella-source/models/config/parameters/kaibab_ecosystem_parameters_stella_scenario2.csv','Case 2 parameters')+'.'))
case_slides[4].append(parsed('<p class="small">'+a('https://pysd.readthedocs.io/en/latest/','PySD supports translation and simulation, with feature limitations')+'. Stella Case 2’s native CSV has final values only; a new PySD trajectory is separate evidence.</p>').p)
# Keep the full scientific-to-archive diagram in the introduction; compact form uses footer space.
STAGES=['specification','implementation','configuration','execution','results','archive']
LABELS=['Science','Vensim / Stella','Case 1 / Case 2','Execution','Inspection','FAIR record']
def workflow(stage,full=False):
    return '<ol class="workflow'+(' workflow-full' if full else '')+'" aria-label="Shared research workflow">'+''.join('<li'+(' class="active" aria-current="step"' if k==stage else '')+'>'+v+'</li>' for k,v in zip(STAGES,LABELS))+'</ol>'
case_slides[0].append(parsed(workflow('specification',True)).ol)
for s in case_slides:slides[4].insert_after(s) # Correct order is established by rebuilding the slide container below.
all_slides=slides[:5]+case_slides+slides[5:]+appendix
container=soup.select_one('.slides');container.clear()
for s in all_slides:container.append(s)
for i,s in enumerate(all_slides,1):
    n=int(s['data-reference-slide']) if s.has_attr('data-reference-slide') else None
    stage=s.get('data-stage') or ('specification' if n and n<=5 else 'archive' if n and n<=21 else 'results' if n and n<=25 else 'configuration' if n and n<=29 else 'execution' if n and n<=34 else 'archive')
    stage={12:'implementation',13:'implementation',14:'implementation',15:'implementation',39:'execution',40:'execution',41:'execution',42:'execution',43:'execution'}.get(n,stage)
    s['data-stage']=stage
    if not s.select_one('.workflow:not(.workflow-full)'):s.append(parsed(workflow(stage)).ol)
    note=s.select_one('aside.notes')
    if note is None:
        note=soup.new_tag('aside',attrs={'class':'notes'});s.append(note)
        note.append('Reference slide '+str(n)+': '+text(original[n-1].h1)+'. Preserve its teaching purpose and visual layout. ')
        if changes[n]:
            note.append('Adaptations: '+' '.join(dict.fromkeys(x['reason'] for x in changes[n]))+' ')
        else:note.append('General teaching content retained. ')
    note.append('Shared workflow stage: '+LABELS[STAGES.index(stage)]+'. Distinguish native tool operations, saved-result inspection, and observed PySD execution. ')
    if n in (20,21):note.append('Observed 2026-10-09: anonymous exact-name Betty search returned no repository; authenticated enrichment was not tested. Record current observations rather than promise ranking. ')
    if n in (7,8,9,10,11,16,17,18):note.append('Publication status is '+STATE['status']+'. Do not imply that a configured webhook is already a completed deposit. ')
    note.append(parsed('<p>'+a(REPO,'Repository')+' · '+a(SITE,'Semantic model')+' · '+file('docs/fair/evidence.md','FAIR4RS evidence')+'</p>'))
    if n:note.append(parsed('<p>'+a('https://vasiliyseibert.github.io/awesome-sim/#/'+str(n-1),'Original slide '+str(n))+' · '+a('comparison.html#reference-'+str(n),'Exact adaptation register')+'</p>'))

# Local dependencies preserve the reference theme and work offline after cloning.
def localize(page,reference=False):
    for link in list(page.select('head link')):
        href=link.get('href','')
        if 'katex' in href or 'fonts.googleapis.com' in href or 'fonts.gstatic.com' in href:link.decompose()
        elif 'cdn.jsdelivr.net/npm/reveal.js@5.1.0/' in href:link['href']=href.replace('https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/','vendor/reveal/')
    link=page.new_tag('link',rel='stylesheet',href='css/local-fonts.css');page.head.append(link)
    if not reference:
        page.head.append(page.new_tag('link',rel='stylesheet',href='css/hunter-prey.css?v='+hashlib.sha256((OUT/'css/hunter-prey.css').read_bytes()).hexdigest()[:12]))
        page.title.string='RDM Basics 4 · FAIR4RS · Hunter–prey'
        page.select_one('meta[name="author"]')['content']='Raphael Ginster; Matthias Papesch; Vasiliy Seibert'
    for script in list(page.select('script')):script.decompose()
    for src in ['vendor/reveal/dist/reveal.js','vendor/reveal/plugin/highlight/highlight.js','vendor/reveal/plugin/notes/notes.js','vendor/reveal/plugin/search/search.js','presentation.js']:
        page.body.append(page.new_tag('script',src=src))
    if reference:page.body['data-reference']='true'
# Give refreshed evidence deterministic URLs so a browser cannot reuse an older capture.
for node in soup.select('img[src],a[href]'):
    attr='src' if node.name=='img' else 'href'
    path=node.get(attr,'')
    if path.startswith('assets/evidence/'):
        node[attr]=path+'?v='+hashlib.sha256((OUT/path).read_bytes()).hexdigest()[:12]
localize(soup)
(OUT/'index.html').write_text(str(soup).rstrip()+'\n')
reference_page=parsed(REFERENCE.read_text());localize(reference_page,True)
# Reference-only rendering retains the unadapted source; existing original image assets are local.
(OUT/'reference.html').write_text(str(reference_page).rstrip()+'\n')

# Content-level register: before/after replacements, retained blocks, layout identity, and full diff.
coverage=[];catalog=[]
for i,s in enumerate(all_slides,1):
    title=text(s.h1);n=int(s['data-reference-slide']) if s.has_attr('data-reference-slide') else None
    catalog.append(dict(id=s['id'],slide=i,title=title,original=n,stage=s['data-stage'],kind=s['class'][0]))
    if not n:continue
    orig=original[n-1]
    retained=[]
    for block in orig.select('h1,h3,h4,p,li,q,th,td'):
        value=text(block)
        if value and value in text(s):retained.append(value)
    coverage.append(dict(original_slide=n,original_title=text(orig.h1),adapted_slide=i,adapted_id=s['id'],adapted_title=title,reference_revision=REFERENCE_SHA,reference_layout=orig.get('class',[]),adapted_layout=s.get('class',[]),retained_blocks=list(dict.fromkeys(retained)),changes=changes[n],added_elements=['Speaker notes with adaptation reasons and sources','Compact shared workflow in the footer area'],original_text=text(orig),adapted_text=text(deepcopy(s))))
(OUT/'coverage.json').write_text(json.dumps(coverage,indent=2,ensure_ascii=False)+'\n')
(OUT/'catalog.json').write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
md=['# Reference lecture: content-level adaptation register','','Source: [awesome-sim lecture](https://vasiliyseibert.github.io/awesome-sim/), revision `'+REFERENCE_SHA+'`.','','52 original slides remain in order, with five added case-study slides and six optional walkthroughs: **57 core / 63 total**. The original HTML is preserved in `tools/fair/reference/awesome-sim.html`.','','[Side-by-side comparison and exact substitutions](comparison.html). Backgrounds, typography, original layout families and the six divider compositions are retained. All slides additionally receive notes and a compact workflow indicator.','','| Reference | Revised | Changes | Retained content blocks |','|---|---|---|---|']
for c in coverage:md.append(f"| {c['original_slide']}: {c['original_title']} | [{c['adapted_slide']}: {c['adapted_title']}](index.html#/{c['adapted_id']}) | {len(c['changes'])} recorded substitutions | {len(c['retained_blocks'])} |")
md+=['','## Additions','', 'Five labelled slides after reference slide 5: shared specification; shared use cases; artifacts/access; Case 1/2; inspection versus execution.','', 'Six optional screenshot walkthroughs follow the original closing slide.','', 'The register records wording changes, exact replaced fragments, added elements and reasons. It does not treat a topic-level match as proof of retained content.']
(OUT/'coverage.md').write_text('\n'.join(md)+'\n')
css='body{font:16px/1.5 Arial,sans-serif;margin:0;background:#f7f8fb;color:#0c113d}header,main{max-width:1500px;margin:auto;padding:24px}a{color:#2839cc}section{background:white;margin:22px 0;padding:24px;border:1px solid #d7dbe6}iframe{width:100%;aspect-ratio:1.6;border:1px solid #ddd}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f5f9;padding:12px;font-size:13px}summary{cursor:pointer;font-weight:bold}.change{border-left:3px solid #2839cc;padding-left:16px;margin:18px 0}.shots img{width:100%}@media(max-width:850px){.pair{grid-template-columns:1fr}}'
html=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>52-slide fidelity comparison</title><style>'+css+'</style><header><h1>Reference lecture: 52-slide comparison</h1><p>Original order and layout families retained. Five case-study additions and six optional walkthroughs are identified separately.</p><p>'+a('index.html','Open revised presentation')+' · '+a('coverage.md','Coverage map')+' · '+a('handout.pdf','Print review PDF')+' · '+a('coverage.json','Machine-readable exact changes')+'</p></header><main>']
for c in coverage:
    n=c['original_slide'];html.append(f'<section id="reference-{n}"><h2>Reference {n} → revised {c["adapted_slide"]}: {escape(c["original_title"])}</h2><p>Layout: {escape(" ".join(c["reference_layout"]))}. General teaching content is retained except the explicitly recorded replacements below.</p><div class="pair shots"><a href="comparison/{n:02d}-reference.jpg"><img loading="lazy" src="comparison/{n:02d}-reference.jpg" alt="Reference slide {n}"></a><a href="comparison/{n:02d}-adapted.jpg"><img loading="lazy" src="comparison/{n:02d}-adapted.jpg" alt="Revised slide {c["adapted_slide"]}"></a></div><p>'+a('reference.html#/'+str(n-1),'Open original slide')+' · '+a('index.html#/'+c['adapted_id'],'Open adapted slide')+'</p>')
    html.append('<details><summary>Retained content ('+str(len(c['retained_blocks']))+' blocks)</summary>'+ul(*(escape(x) for x in c['retained_blocks']))+'</details>')
    html.append('<details><summary>Exact substitutions ('+str(len(c['changes']))+')</summary>')
    for change in c['changes']:
        html.append('<div class="change"><h3>'+escape(change['category'])+'</h3><p>'+escape(change['reason'])+'</p><p><code>'+escape(change['selector'])+'</code></p><div class="pair"><pre>'+escape(change['before'])+'</pre><pre>'+escape(change['after'])+'</pre></div></div>')
    html.append('</details><p>Added on this slide: speaker notes, source/adaptation links in notes, compact workflow indicator.</p></section>')
html.append('</main></html>');(OUT/'comparison.html').write_text('\n'.join(html)+'\n')
(OUT/'comparison').mkdir(exist_ok=True)
sources=json.loads((OUT/'sources.json').read_text())
sources['reference_deck']['html_sha256']=hashlib.sha256(REFERENCE.read_bytes()).hexdigest()
sources['reference_deck']['content_license']='CC-BY-4.0 (as stated by the source lecture)'
sources['publication']={'software_version':VERSION,'archived_software_revision':STATE['release_revision'],'presentation_revision':'__REVISION__','status':STATE['status']}
(OUT/'sources.json').write_text(json.dumps(sources,indent=2,ensure_ascii=False)+'\n')
print('52 original slides retained; 5 case-study additions; 6 appendix slides; exact content register generated.')
