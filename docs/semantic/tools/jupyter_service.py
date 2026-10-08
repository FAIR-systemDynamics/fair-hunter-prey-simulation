"""One verified JupyterLab destination for the notebook and all its sections.

Only activate the destination after cloning the repository and checking the five
heading links in an authenticated NFDI4Ing session. Repository provenance and
the saved HTML reading view remain independent of this execution destination.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urlsplit

HERE = Path(__file__).resolve().parents[1]
SERVICE_HOST = 'jupyter-nfdi.tik.uni-stuttgart.de'


def notebook_url(section=None, *, here=HERE):
    config = json.loads((here / 'jupyter.json').read_text())
    url = config['notebookUrl']
    if url is None:
        return None
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.netloc != SERVICE_HOST
            or not parsed.path.startswith('/hub/user-redirect/lab/workspaces/kaibab-inspection/tree/')
            or not parsed.path.endswith('/inspect_results.ipynb')
            or parsed.query or parsed.fragment):
        raise ValueError('Use the NFDI4Ing shareable notebook URL without a query or fragment.')
    digest = hashlib.sha256((here / 'notebooks/inspect_results.ipynb').read_bytes()).hexdigest()
    if config['verifiedNotebookSha256'] != digest:
        raise ValueError('The notebook has changed or its NFDI4Ing copy is unverified. '
                         'Update the Hub clone and verify it before enabling the launch links.')
    if section:
        # Preserve JupyterLab's documented empty query before the heading fragment.
        # The UI opens this dedicated workspace in the same tab to avoid the
        # service's automatic workspace cloning, which can discard the fragment.
        return url + '?#' + quote(section['anchor'], safe='-._~')
    return url
