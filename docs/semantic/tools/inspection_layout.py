"""Five-stage inspection diagram: inputs, activity, code, cells, outputs."""
from workflow_layout import render_sequence

INPUTS = ['file/results/runs/case1_external.csv', 'file/results/runs/case2_external.csv']
ACTIVITY = 'processing/inspect-results-python'
READER = 'file/scripts/vensim_csv.py'
NOTEBOOK = 'notebook/inspect-results'
CELLS = [f'notebook-section/inspect-results/cell-{i}' for i in range(1, 6)]
OUTPUTS = ['dataset/python-state-trajectories', 'dataset/python-inspection-summary', 'visualization/python-inspection']
POSITIONS = {
    INPUTS[0]: (20, 235, 260, 100), INPUTS[1]: (20, 465, 260, 100),
    ACTIVITY: (350, 350, 250, 100),
    READER: (670, 235, 250, 100), NOTEBOOK: (670, 465, 250, 100),
    **{key: (1000, 105 + i * 140, 250, 100) for i, key in enumerate(CELLS)},
    **{key: (1330, 385 + i * 140, 250, 100) for i, key in enumerate(OUTPUTS)},
}
ROUTES = {
    (INPUTS[0], ACTIVITY): ([(280, 285), (315, 285), (315, 380), (350, 380)], (312, 253)),
    (INPUTS[1], ACTIVITY): ([(280, 515), (315, 515), (315, 420), (350, 420)], (312, 548)),
    (ACTIVITY, READER): ([(600, 380), (635, 380), (635, 285), (670, 285)], (635, 255)),
    (ACTIVITY, NOTEBOOK): ([(600, 420), (635, 420), (635, 515), (670, 515)], (635, 547)),
}
for i, key in enumerate(CELLS):
    middle = 155 + i * 140
    ROUTES[NOTEBOOK, key] = ([(920, 515), (960, 515), (960, middle), (1000, middle)], (975, middle - 18))
for i, key in enumerate(OUTPUTS):
    middle = 435 + i * 140
    ROUTES[CELLS[i + 2], key] = ([(1250, middle), (1330, middle)], (1290, middle - 30))
LABELS = {
    INPUTS[0]: ('case1_external.csv', 'Saved baseline result'),
    INPUTS[1]: ('case2_external.csv', 'Saved scenario result'),
    ACTIVITY: ('Inspect data with Python', 'm4i:ProcessingStep · executed'),
    READER: ('vensim_csv.py', 'Repository CSV reader'),
    NOTEBOOK: ('inspect_results.ipynb', 'Executed notebook · five cells'),
    CELLS[0]: ('Verify source files', 'Cell 1 · hashes and setup'),
    CELLS[1]: ('Read units and time axes', 'Cell 2 · CSV reader and inventory'),
    CELLS[2]: ('Build the pandas table', 'Cell 3 · compatible state series'),
    CELLS[3]: ('Inspect peaks and\nfinal values', 'Cell 4 · descriptive statistics'),
    CELLS[4]: ('Compare trajectories', 'Cell 5 · three panels'),
    OUTPUTS[0]: ('State trajectories', 'pandas table · CSV'),
    OUTPUTS[1]: ('Peaks and final values', 'Summary table · CSV'),
    OUTPUTS[2]: ('Compare both cases', 'Comparison figure · SVG'),
}
NOTES = [
    (20, 'Start with committed results.', '1,001 samples per simulated state;', '21 historical observations on their own axis.'),
    (670, 'Read one complete notebook.', 'Each cell link opens its section,', 'with the saved tables and figure in context.'),
    (1110, 'Follow the cells into their outputs.', 'Cells 3–5 specify the tables and comparison figure.', 'Actual generation is also recorded in the RDF.'),
]


def render_inspection(model, entities, ids, palette):
    workflow = next(w for w in model['workflows'] if w['slug'] == 'python-inspection')
    return render_sequence(workflow, entities, ids, palette, POSITIONS, ROUTES, LABELS, NOTES)
