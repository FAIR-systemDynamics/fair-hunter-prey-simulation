"""Save rendered-on-GitHub notebook excerpts without re-executing any cells."""
from copy import deepcopy
import nbformat as nb


def write_section_notebooks(notebook, sections, destination):
    paths = []
    for section in sections:
        number, index = section['number'], section['cellIndex']
        path = f'notebooks/sections/cell-{number}.ipynb'
        intro = nb.v4.new_markdown_cell(
            f'Saved excerpt of **code cell {number}** from '
            '[the complete inspection notebook](../inspect_results.ipynb). '
            'The output below comes from its executed run. '
            'Open the complete notebook to run the cells in order.',
            id=f'cell-{number}-context')
        excerpt = nb.v4.new_notebook(
            cells=[deepcopy(notebook.cells[index - 1]), intro, deepcopy(notebook.cells[index])],
            metadata=deepcopy(notebook.metadata))
        nb.validate(excerpt)
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        nb.write(excerpt, target)
        section['previewPath'] = path
        paths.append(path)
    return paths
