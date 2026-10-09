---
version: alpha
name: Kaibab semantic atlas
description: A diagram-first semantic map connecting literature, variables and repository evidence.
colors:
  ink: "#182f3a"
  muted: "#546872"
  primary: "#245a8d"
  science: "#246952"
  literature: "#72568e"
  config: "#846114"
  warning: "#8b4c28"
  background: "#ffffff"
  surface: "#ffffff"
  border: "#d6e0e3"
  science-tint: "#edf5f0"
  code-tint: "#edf2f9"
  warning-tint: "#fcf2e7"
  scrollbar: "#93a5ae"
  scrollbar-track: "#f3f6f7"
  scrollbar-hover: "#738c99"
  scrollbar-active: "#546872"
typography:
  display:
    fontFamily: "Arial, Helvetica, sans-serif"
  body:
    fontFamily: "Arial, Helvetica, sans-serif"
  mono:
    fontFamily: "'SFMono-Regular', Consolas, monospace"
omitted:
  - section: spacing
    reason: Geometry is documented in Layout and implemented once in style.css.
  - section: rounded
    reason: Component-specific corner treatment is documented in Shapes.
  - section: components
    reason: Native HTML components share CSS classes described below.
---

# Kaibab semantic map

## Overview

The user's supplied ontology diagrams are the visual authority: a white canvas, pastel rounded boxes, labelled directional arrows, minimal surrounding text. The diagram is the interface. Literature understanding and concrete repository entities appear together. This replaces the earlier dashboard and permanent inspector after explicit user feedback.

## Colors

White background with dark readable labels. Category colours match the reference: lavender literature, coral concepts, blue model, white numerical variables, pale blue files, green processing steps, orange methods, yellow tools and configurations, purple bindings and fields. Each node also includes its actual ontology type; colour is never the only distinction. Graph-specific colours are owned by the palette in tools/build_graphs.py and mirrored in the HTML legend. Shared chrome palette and fonts are generated from this file into tokens.css.

## Typography

Local Arial/Helvetica sans serif, with 16px graph labels and 10px ontology captions at native graph scale. The whole graph scales together. Zoom restores legibility on small screens. Hover and keyboard focus descriptions use readable fixed-size text.

## Layout

A compact header has three navigation tabs: Semantic Model (the former Overview, retaining its #overview route), Workflows and NFDI4Ing Use Cases. These are native navigation links because the views are bookmarkable. Semantic Model and entity neighborhoods use a full-window pan-and-zoom canvas. Bottom legend and zoom buttons float over that canvas; no permanent detail sidebar. Workflows is a naturally scrolling document: a linked table of contents followed by all examples in order. Each example has a heading, evidence note, artifact links, inline diagram and local legend. A small search opens an entity's direct relationships. On mobile the header wraps into two rows. Dense neighborhoods explicitly state if connections are omitted; complete RDF remains available through its repository source link.

Workflows starts with Case 2, followed by Python / Jupyter inspection. Both examples have descriptive action-sentence titles and five numbered columns. The first runs from model declaration to figure. The second runs from saved CSVs to Python inspection, repository code, notebook cells and outputs. Only the CSV reader and notebook follow the inspection activity directly; notebook cells and their tables and SVG follow the code. Each of the five cell nodes links to its heading in the executable notebook on NFDI4Ing JupyterLab. The complete saved notebook remains available as a read-only view, preserving the executed cells, tables and figure in context. The notebook view has a linked contents list, visible heading anchors, a return link to the workflow, and a Git source link. Python source remains a separate explicit option. Numbers denote reading order; arrows retain actual RDF relationship directions. The diagrams distinguish reconstructed simulation provenance from locally executed plotting and inspection. Jupyter support is presented honestly: the reader and PySD runner existed; the executed notebook is new.

Contents links use #workflow-<slug>, scroll the selected heading below the sticky header, and focus it. Both workflows remain in the document. Each inline diagram keeps a readable minimum width and scrolls horizontally on narrow screens; wheel and arrow keys retain normal document/region scrolling. Explore diagram opens the shared canvas, with a Back to workflows link returning to the same section. The viewport constraints of the canvas never apply to the workflow document.

NFDI4Ing Use Cases is a naturally scrolling catalog at `#nfdi4ing`. Each service has a pale-blue service column and its linked workflow use cases beside it; the columns stack on phones. The introductory sentence uses the service name and the existing workflow title. `nfdi4ing-services.json` owns service metadata and workflow-slug references; `build_model.py` publishes that catalog and `app.js` renders it. Adding a service or another workflow reuses the same structure. Workflow links select Workflows and focus its existing heading; browser Back restores the service catalog. The shared navigation wraps into two rows below 1,320px, with all three labels visible.

The header identifies the repository as `FAIR-systemDynamics/fair-hunter-prey-simulation`, with a natural wrap opportunity after the slash. The notebook reading view uses the same identity. Below 680px, the full name, search and navigation occupy three rows. `--header-height` keeps document anchors and canvas offsets aligned with the shared header. Service panels may display their official marks, with intrinsic dimensions reserved and attribution retained in `assets/README.md`.

## Elevation & Depth

Flat diagram with thin borders; only hover descriptions and search suggestions cast a small shadow. No decorative illustrations, gradients or animation.

## Shapes

Rounded rectangular ontology nodes, small rounded controls, arrowheads with readable relation labels. Semantic Model uses an editorial layout in tools/overview_layout.py: mathematics above, implementation and simulation below. Workflows shares the sequence renderer in tools/workflow_layout.py; tools/inspection_layout.py supplies the Python layout. Both diagrams' arrows and nodes come from the same semantic dataset as the RDF. Entity neighborhoods use deterministic Graphviz routing.

## Components

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Scrollbar | docs/semantic/style.css | DESIGN.md Colors → build_tokens.py → tokens.css | Global baseline, inline diagrams use stable gutter | Document and diagram scroll checks |
| Notebook reading | docs/semantic/tools/notebook_view.py and style.css | Executed inspect_results.ipynb → nbconvert HTML; shared tokens.css | Whole notebook / heading fragment | Saved-output integrity and browser section landing |
| Notebook execution links | docs/semantic/tools/jupyter_service.py and app.js sourceFor | jupyter.json verified destination + notebook checksum; manifest heading anchors | Whole notebook / section in the visitor's NFDI4Ing workspace | Authenticated clone and execution, five section landings, graph validation |
| View navigation | docs/semantic/app.js and index.html | DESIGN.md Layout | Semantic Model / Workflows / NFDI4Ing Use Cases / entity neighborhood | Browser navigation and refresh |
| Service use cases | docs/semantic/nfdi4ing-services.json and app.js buildUseCases | Service metadata plus existing workflow titles | One service with one or more workflow use cases | Workflow navigation, Back, refresh, keyboard and narrow layout |
| Graph rendering | docs/semantic/tools/build_graphs.py | data/model.json and RDF | Overview / workflow / neighborhood | RDF edge integrity and browser rendering |

app.js owns graph navigation, the workflow contents and sections, search, pan, zoom and the shared hover/focus description. Its bindGraph helper supplies identical node behavior on the canvas and inline diagrams, with unique SVG IDs for each instance. build_graphs.py owns all node and arrow layouts. index.html owns the three-tab header and canvas chrome. Anchors navigate; native buttons zoom or fit. File nodes and implementation variables open their sources in a new tab. Scientific quantities, formulas and collection nodes open their neighborhoods, even when their evidence includes source URLs. Literature and software nodes link to their sources. Each view generates its colour legend from its actual entity types. Search opens a local neighborhood without navigating to GitHub. Notebook nodes open the configured, verified NFDI4Ing JupyterLab destination; the saved local view is the fallback when the destination is unset. Sections are fragments of the same notebook, not separate files. Explicit repository actions, tables and figures open commit-pinned sources in GitHub. The reader’s Git source link follows the current workflow branch. No artifact download controls are offered. No external rendering dependencies or network fonts.

Escape dismisses descriptions and search. Hover descriptions also appear on keyboard focus. Search supports keyboard traversal, Enter and an explicit clear button. The input is a transient local entity finder; committed entity selection, rather than the draft query, is stored in the URL. Arrow keys provide a non-drag pan alternative. Empty search results explain the state. A failed dataset load shows an explanation and the RDF source link remains available. No remote mutations, publishing or simulation execution are offered.

Entity links preserve their parent view in #overview/<entity> or #workflows/<entity>, including on refresh and browser Back. Workflow links carry ?from=<slug> within the fragment to preserve the section; full diagrams use #workflows/diagram/<slug>. Legacy entity URLs still open their neighborhood. Removed curated-view URLs fall back to Semantic Model. Each route sets a descriptive document title and keeps its owning navigation link selected. Generated artifacts and original inputs retain separate commit-pinned GitHub sources. The RDF header link points to the current workflow branch. The browser does not run simulations, notebooks or plotting commands. The notebook reading page uses the same three-tab header, fonts, colours and global scrollbar baseline, a 1,100px document column, code prompts and locally scrolling code/table regions. Saved plots reserve their aspect ratio; heading targets sit below the sticky header and receive a visible outline. At narrow widths, prompts move above code and tables scroll within their regions. NFDI4Ing launch controls require the tested destination and matching source notebook checksum in jupyter.json. The service was verified on 2026-10-08; it requires sign-in and a clone in each visitor’s persistent work folder.

## Do's and Don'ts

NFDI4Ing integration extends the existing notebook navigation: once the cloned
notebook and five section links are verified, the notebook and cell nodes use
their `launchUrl` through the same `sourceFor` helper on inline diagrams and
the full canvas. Until then, `previewUrl` opens the saved HTML. The workflow
offers **Open in NFDI4Ing JupyterLab** only when configured, alongside **Read
saved notebook**. Shared links use the visitor's own Hub workspace; nearby
text explains the one-time repository clone into the persistent work folder.
Jupyter links open in the same browser tab and a dedicated `kaibab-inspection`
workspace; browser Back returns to the workflow. This avoids automatic Jupyter
workspace cloning in duplicate tabs, which can discard section fragments.
These links use a right arrow; sources opening a new tab use an up-right arrow.
Repository source links, scientific
provenance, layout, typography and colors retain their existing roles.

- Keep the graph primary and surrounding text minimal.
- Preserve actual ontology types and existing evidence-backed relationship directions.
- Keep source links and literature accessible directly from nodes.
- Do not copy ontology type names from the sample when the model uses a different verified type.
- Do not imply the documented runs were newly executed or draft identifiers are published.

The revised overview separates a MathModDB mathematical-model instance, governing formulas, scientific state quantities, parameter declarations, both native implementation files, software tools, a computational task, its setup plan, and requested outputs. It does not represent the generic task as a completed case-1 execution. Overview connections outside established ontology predicates are explicit review proposals in the local sd namespace.

## Additional FAIR4RS lecture

The independent `/slides/` route faithfully adapts the 52-slide awesome-sim lecture at revision e354ef2e567223ab8ba6eaac3d572d589efb5ab8. Its original HTML is the immutable authoring baseline, and the original theme and slide styles own typography, dimensions, columns, code panels, cards, headers and footers. IBM Plex Sans/Mono weights and Reveal.js are bundled locally. The 1280 × 800 canvas, grouped agenda, fade navigation, speaker notes and printing are retained.

Five explicitly labelled case-study slides follow the original repository overview; six optional screenshot walkthroughs follow the original closing slide. The total is 57 core / 63 slides. `tools/fair/build_slides.py` applies recorded fragment-level substitutions rather than rewriting the lecture. The coverage register captures exact before/after fragments, retained blocks, layout families and adaptation reasons. `comparison.html` supplies side-by-side browser captures for every reference slide.

The original `title-slide` composition uses image3.jpg. All six original `divider` compositions use image4.jpg, the original gradient, large yellow number, logo, rule and FAIR badges. `hunter-prey.css` adds only the compact shared workflow in footer space, evidence-image sizing, responsive reading, focus states and print polish. It must not replace the reference backgrounds, general teaching text or layout system. The existing semantic site remains byte-identical.

The original grouped agenda appearance is retained with focus containment, Escape closing and restored focus. Under 680px, the active slide becomes a naturally scrolling single-column reading view. A capture query disables transitions only for deterministic review images. All slides carry notes that connect the current workflow stage to the scientific narrative and explain adaptations. No simulation, publication or remote mutation runs in the presentation.
