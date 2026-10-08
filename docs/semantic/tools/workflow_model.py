"""One evidence-backed artifact sequence through the overview's Kaibab model."""
import hashlib
import json
from rdflib import RDF, RDFS, OWL, Literal, URIRef
from workflow_sources import ARTIFACT_REVISION, artifact_source

TITLE = 'Set predator removal to 0.2/year, simulate the ecosystem, and follow the result into a figure.'


def extend(c):
    E, g = c['entities'], c['g']
    add, edge, uri, lit = (c[k] for k in ('add', 'edge', 'uri', 'lit'))
    SD, PROV, DCT, M4I, OBO, SCHEMA = (c[k] for k in ('SD', 'PROV', 'DCT', 'M4I', 'OBO', 'SCHEMA'))
    manifest = json.loads((c['OUT'] / 'data/workflow-figure.json').read_text())
    assert manifest['revision'] == c['REV']
    for path, digest in manifest['sources'].items():
        assert hashlib.sha256(c['read'](path, True)).hexdigest() == digest
    figure = c['OUT'] / 'data' / manifest['output']
    assert hashlib.sha256(figure.read_bytes()).hexdigest() == manifest['sha256']

    g.add((SD.inputTo, RDF.type, OWL.ObjectProperty))
    g.add((SD.inputTo, OWL.inverseOf, OBO.RO_0002233))
    g.add((SD.inputTo, RDFS.comment, Literal('An artifact supplied as input to a processing step; inverse of obo:RO_0002233. This is a local workflow display predicate.')))
    g.add((SD.artifactSequence, RDF.type, OWL.ObjectProperty))
    g.add((SD.artifactSequence, RDFS.comment, Literal('Ordered presentation of entities in a workflow example. Sequence order alone does not assert derivation or execution provenance.')))

    model = 'file/' + c['model_path']
    scenario = 'file/models/config/scenarios/case2.cin'
    parameter = 'variable/fraction-predators-killed-per-year'
    assignment = 'assignment/case2/fraction-predators-killed-per-year'
    result = 'file/results/runs/case2_external.csv'
    script = 'file/scripts/plot_results.py'
    runner = 'file/runners/vensim/vensim_run_configuration_external'
    plot = 'processing/plot-case2-review'
    output = 'visualization/case2-review'
    workflow = 'workflow/case2-parameter-to-figure'

    add(plot, 'Plot the result', 'Run',
        'Locally executed plotting step using the pinned plot_results.py and vensim_csv.py with the committed Case 2 CSV. Selects the three state trajectories and writes the review SVG. This step does not execute or verify the original simulation.',
        [M4I.ProcessingStep, PROV.Activity], [c['src']('scripts/plot_results.py')],
        status='Executed locally', navigation='explore', displayType='Plotting · executed locally',
        details=[manifest['command']])
    add(output, 'Case 2 trajectories', 'Visualization',
        'Review figure generated locally from the committed Case 2 CSV: deer population, predator population and forage biomass over 1900–1950. This is a newly rendered figure of existing results, not a new simulation result.',
        [SCHEMA.ImageObject, PROV.Entity], [artifact_source('data/' + manifest['output']), c['src']('results/runs/case2_external.csv'), c['src']('scripts/plot_results.py')],
        status='Generated locally', revision=ARTIFACT_REVISION,
        sha256=manifest['sha256'], displayType='SVG figure · repository source')
    lit(output, SD.sha256, manifest['sha256'])
    lit(output, SCHEMA.contentUrl, artifact_source('data/' + manifest['output'])['url'])
    edge(plot, OBO.RO_0002233, result, 'has input', status='Executed locally')
    edge(result, SD.inputTo, plot, 'input to plotting', status='Executed locally')
    edge(plot, PROV.used, script, 'uses plotting script', status='Executed locally')
    edge(plot, PROV.used, 'file/scripts/vensim_csv.py', 'uses CSV reader', status='Executed locally')
    edge(plot, PROV.generated, output, 'generates figure', status='Executed locally')
    edge(output, PROV.wasDerivedFrom, result, 'visualizes committed data', status='Executed locally')
    edge(assignment, PROV.wasDerivedFrom, scenario, 'read from scenario', status='Extracted')
    edge('run/case2', DCT.source, runner, 'documented by', status='Documented')
    for artifact in [model, scenario]:
        assert any(e['source'] == 'run/case2' and e['target'] == artifact and e['predicate'] == str(OBO.RO_0002233) for e in c['edges'])
        edge(artifact, SD.inputTo, 'run/case2', 'input to simulation', status='Documented')

    stages = [dict(label='Model declaration', entity=model),
              dict(label='Set the parameter', entity=scenario),
              dict(label='Run the simulation', entity='run/case2'),
              dict(label='Obtain the result', entity=result),
              dict(label='Visualize the result', entity=output)]
    add(workflow, TITLE, 'Workflow',
        'A worked sequence connecting a model declaration, external parameter assignment, documented simulation, committed result and locally generated visualization. Case 2 includes four overrides; it is not a single-parameter experiment.',
        [SCHEMA.CreativeWork], [c['src']('runners/vensim/vensim_run_configuration_external')],
        navigation='explore', status='Review example')
    sequence = URIRef(str(uri(workflow)) + '/sequence')
    g.add((uri(workflow), SD.artifactSequence, sequence))
    g.add((sequence, RDF.type, RDF.Seq))
    for index, stage in enumerate(stages, 1):
        g.add((sequence, URIRef(str(RDF) + '_' + str(index)), uri(stage['entity'])))
        edge(workflow, DCT.hasPart, stage['entity'], 'includes workflow entity', status='Interpreted')

    pairs = [(parameter, model), (assignment, parameter), (assignment, scenario),
             (model, 'run/case2'), (scenario, 'run/case2'),
             ('run/case2', 'configuration/case2'), ('configuration/case2', assignment),
             ('run/case2', 'tool/vensim'), ('run/case2', runner),
             ('run/case2', result), (result, plot), (plot, script), (plot, output)]
    selected_edges = []
    for a, b in pairs:
        matches = [e for e in c['edges'] if e['source'] == a and e['target'] == b]
        assert len(matches) == 1, (a, b, matches)
        selected_edges.append(matches[0])
    return dict(id=workflow, slug='case2-parameter-to-figure',graphKey='diagram/case2-parameter-to-figure',title=TITLE, stages=stages,
                entities=list(dict.fromkeys(k for e in selected_edges for k in (e['source'], e['target']))),
                edges=selected_edges, figure=manifest,
                summary='Follow the Case 2 scenario from its model declaration and parameter file to the saved simulation result and plot.',
                caveat='Case 2 also changes three other parameters. The simulation is documented; only the figure was generated locally.',
                actions=[dict(label='View figure in repository',url=artifact_source('data/'+manifest['output'])['url'])])
