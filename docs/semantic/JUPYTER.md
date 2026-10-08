# Run the inspection notebook on NFDI4Ing

The [public repository](https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation)
can be cloned directly into the [NFDI4Ing Jupyter service](https://jupyter.nfdi4ing.de/).
The notebook is on the `codex/semantic-workflow-sources` branch. It needs the
repository's CSV reader and both saved result files at their original paths.

## Set up your workspace once

1. [Sign in](https://jhublogin-nfdi.tik.uni-stuttgart.de/login) with your
   institution and start a Python datascience environment.
2. Open a JupyterLab terminal and clone the notebook branch into persistent
   storage:

   ```sh
   cd ~/work
   git clone --branch codex/semantic-workflow-sources https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation.git
   ```

   The service mounts `~/work` separately from the container's temporary root
   filesystem. Keep the repository there. If you already cloned it, keep your
   local changes and update that copy instead of cloning over it.
3. Open
   `work/fair-hunter-prey-simulation/docs/semantic/notebooks/inspect_results.ipynb`
   and select the Python kernel. Run all five code cells in order. They verify
   input hashes, inspect saved results, and write tables and a comparison plot
   under `docs/semantic/data/`. No simulation is run.
4. Pandas and Matplotlib are already installed in the tested datascience
   environment. If another selected kernel lacks them, install into that
   kernel from a temporary notebook cell, then restart it:

   ```python
   %pip install -r ../requirements-jupyter.txt
   ```

   `%pip` targets the notebook kernel's environment. The requirements record
   the service versions used for verification; the full semantic-model build
   requirements are unnecessary for running this notebook.

## Direct workflow links

JupyterLab [supports heading fragments](https://jupyterlab.readthedocs.io/en/stable/user/urls.html#linking-notebook-sections).
The notebook has five unique headings; their exact fragments are stored in
`data/python-inspection-manifest.json`. Each workflow cell opens its heading in
this same executable notebook.

The links use JupyterHub's
[`/hub/user-redirect/` route](https://jupyterhub.readthedocs.io/en/stable/faq/faq.html#how-do-i-share-links-to-notebooks),
which opens the visitor's own workspace. Each visitor must first clone the
repository at the path above. Making the repository public does not grant
access to somebody else's Jupyter server. The tested service does not have
nbgitpuller installed, so the links do not automatically clone a repository.

Section links use JupyterLab's documented `notebook.ipynb?#heading` format,
including the empty query before the fragment. They open the dedicated
`kaibab-inspection` workspace in the same browser tab. Use browser Back to
return to the workflow. Opening duplicate Jupyter tabs can trigger automatic
workspace cloning, which drops section targets on this service. Recheck all five destinations
when upgrading the service or changing the notebook headings.

`jupyter.json` records the verified shareable notebook URL and the source
notebook checksum. `tools/jupyter_service.py` derives all five heading URLs
from the same destination. The notebook node, all five cell nodes and the
primary workflow action open JupyterLab. **Read saved notebook** remains an
account-free local reading option. The RDF and browser projection record the
active destination; commit-pinned GitHub sources retain their provenance role.

## Updating the notebook destination

After changing the notebook, update the Hub clone and verify execution and
all five heading links. Record the confirmed shareable URL (without a query
or fragment) and the SHA-256 of the source notebook in `jupyter.json`, then
rebuild:

```sh
python docs/semantic/tools/build_model.py
python docs/semantic/tools/build_graphs.py
python docs/semantic/tools/validate_model.py
```

`verifiedNotebookSha256` identifies the repository notebook that was tested;
executing it on the Hub may change saved outputs and metadata in that workspace.
Changed repository notebook bytes invalidate the deployment checksum. Setting
`notebookUrl` to `null` restores the saved-view links.
