"""Artifact sequence with real semantic links and an actual generated figure."""
from html import escape
import textwrap

MODEL = 'file/models/kaibab_ecosystem_model.mdl'
SCENARIO = 'file/models/config/scenarios/case2.cin'
PARAMETER = 'variable/fraction-predators-killed-per-year'
ASSIGNMENT = 'assignment/case2/fraction-predators-killed-per-year'
RUN = 'run/case2'
CONFIG = 'configuration/case2'
RESULT = 'file/results/runs/case2_external.csv'
PLOT = 'processing/plot-case2-review'
FIGURE = 'visualization/case2-review'
SCRIPT = 'file/scripts/plot_results.py'
RUNNER = 'file/runners/vensim/vensim_run_configuration_external'

POSITIONS = {
    MODEL: (20, 165, 260, 100), SCENARIO: (350, 165, 250, 100),
    RUN: (670, 165, 250, 100), RESULT: (1000, 165, 250, 100),
    FIGURE: (1330, 165, 250, 100),
    PARAMETER: (20, 430, 260, 100), ASSIGNMENT: (350, 430, 250, 100),
    CONFIG: (670, 430, 250, 100), PLOT: (1220, 430, 270, 100),
    'tool/vensim': (600, 685, 170, 70), RUNNER: (810, 685, 290, 88),
    SCRIPT: (1220, 685, 270, 88),
}
ROUTES = {
    (PARAMETER, MODEL): ([(150,430),(150,265)], (200,365)),
    (ASSIGNMENT, PARAMETER): ([(350,480),(280,480)], (315,445)),
    (ASSIGNMENT, SCENARIO): ([(475,430),(475,265)], (542,365)),
    (MODEL, RUN): ([(150,165),(150,110),(730,110),(730,165)], (450,98)),
    (SCENARIO, RUN): ([(600,215),(670,215)], (635,183)),
    (RUN, CONFIG): ([(795,265),(795,430)], (854,353)),
    (CONFIG, ASSIGNMENT): ([(670,480),(600,480)], (635,445)),
    (RUN, 'tool/vensim'): ([(708,265),(635,320),(635,610),(685,610),(685,685)], (635,589)),
    (RUN, RUNNER): ([(885,265),(955,320),(955,685)], (1024,610)),
    (RUN, RESULT): ([(920,215),(1000,215)], (960,183)),
    (RESULT, PLOT): ([(1125,265),(1125,355),(1280,355),(1280,430)], (1198,340)),
    (PLOT, SCRIPT): ([(1355,530),(1355,685)], (1430,610)),
    (PLOT, FIGURE): ([(1430,430),(1455,355),(1455,265)], (1515,348)),
}
LABELS = {
    MODEL: ('kaibab_ecosystem_model.mdl', 'Model file · Vensim'),
    SCENARIO: ('case2.cin', 'Scenario file · four overrides'),
    RUN: ('Case 2 simulation', 'm4i:ProcessingStep · documented'),
    RESULT: ('case2_external.csv', 'Committed simulation result'),
    FIGURE: ('Case 2 trajectories', 'SVG figure · repository source'),
    PARAMETER: ('Fraction Predators Killed\nper Year', 'm4i:NumericalVariable · 1/Year'),
    ASSIGNMENT: ('Predator removal = 0.2/year', 'pims:Assignment · baseline 0'),
    CONFIG: ('Case 2 configuration', 'm4i:Configuration'),
    PLOT: ('Plot the three trajectories', 'm4i:ProcessingStep · run locally'),
    RUNNER: ('vensim_run_configuration\n_external', 'Run instructions · file'),
    SCRIPT: ('plot_results.py', 'Plotting script · file'),
}


NOTES = [
    (20, 'Declared here; assigned externally.', 'The model leaves this value as :NA:.'),
    (350, 'Four changes, one scenario.', 'Kills: 40 → 20; capacity: 2 → 4 years;', 'consumption: 0.75 → 0.5; removal: 0 → 0.2/year.'),
    (670, '1900–1950 · Δt = 0.05 year · RK2', 'Also loads baseline values, initial stocks', 'and lookup tables. Provenance is reconstructed.'),
    (1130, 'A figure of existing simulation results.', 'Deer, predators and forage, each on its own axis.', 'Open the figure node to view its repository source.'),
]


def render_workflow(model, entities, ids, palette):
    return render_sequence(model['workflow'], entities, ids, palette,
                           POSITIONS, ROUTES, LABELS, NOTES)


def render_sequence(workflow, entities, ids, palette, positions, routes, labels, notes):
    assert set(workflow['entities']) == set(positions)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 970"><defs><marker id="flow-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 Z" fill="#56636c"/></marker></defs>']
    for i, stage in enumerate(workflow['stages'], 1):
        x, _, w, _ = positions[stage['entity']]
        parts.append(f'<text x="{x}" y="40" font-size="17" font-weight="700" fill="#182f3a">{i} · {escape(stage["label"])}</text>')
        parts.append(f'<path d="M{x},58 h{w}" stroke="#d6e0e3"/>')
    for e in workflow['edges']:
        points, (lx, ly) = routes[(e['source'], e['target'])]
        path = 'M' + ' L'.join(f'{x},{y}' for x,y in points)
        parts.append(f'<g class="edge" data-source="{escape(e["source"])}" data-target="{escape(e["target"])}"><path d="{path}" fill="none" stroke="#657580" stroke-width="1.4" marker-end="url(#flow-arrow)"/>')
        limit = 12 if abs(points[0][0]-points[-1][0]) < 100 else 25
        for n, line in enumerate(textwrap.wrap(e['label'], limit, break_long_words=False, break_on_hyphens=False)):
            parts.append(f'<text x="{lx}" y="{ly+n*16}" text-anchor="middle" font-size="13">{escape(line)}</text>')
        parts.append('</g>')
    for key, (x,y,w,h) in positions.items():
        entity = entities[key]
        fill, stroke = palette.get(entity['kind'], ('#ffffff','#7f8a92'))
        label, caption = labels.get(key, (entity['label'],entity['types'][0]))
        lines = label.split('\n')
        parts.append(f'<g class="node" id="entity-{ids.index(key)}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.7"/>')
        for n,line in enumerate(lines):
            size = 15 if key in (MODEL, RUNNER) else 17
            parts.append(f'<text x="{x+w/2}" y="{y+(h-len(lines)*21-14)/2+17+n*21}" text-anchor="middle" font-size="{size}">{escape(line)}</text>')
        parts.append(f'<text x="{x+w/2}" y="{y+h-15}" text-anchor="middle" font-size="11">{escape(caption)}</text></g>')
    for x, heading, *lines in notes:
        parts.append(f'<text x="{x}" y="855" font-size="15" font-weight="700" fill="#182f3a">{escape(heading)}</text>')
        for i,line in enumerate(lines):
            parts.append(f'<text x="{x}" y="882" dy="{i*21}" font-size="13" fill="#546872">{escape(line)}</text>')
    parts.append('</svg>')
    return ''.join(parts)
