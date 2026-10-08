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

A compact header has exactly two navigation tabs: Semantic Model (the former Overview, retaining its #overview route) and Workflows. These are native navigation links because the views are bookmarkable. Semantic Model and entity neighborhoods use a full-window pan-and-zoom canvas. Bottom legend and zoom buttons float over that canvas; no permanent detail sidebar. Workflows is a naturally scrolling document: a linked table of contents followed by all examples in order. Each example has a heading, evidence note, artifact links, inline diagram and local legend. A small search opens an entity's direct relationships. On mobile the header wraps into two rows. Dense neighborhoods explicitly state if connections are omitted; complete RDF remains available through its repository source link.

Workflows starts with Case 2, followed by Python / Jupyter inspection. Both examples have descriptive action-sentence titles and five numbered columns. The first runs from model declaration to figure. The second runs from saved CSVs to Python inspection, repository code, notebook cells and outputs. Only the CSV reader and notebook follow the inspection activity directly; notebook cells and their tables and SVG follow the code. Each of the five cell nodes links to a heading in one complete, read-only notebook view, preserving the executed cells, tables and figure in context. The notebook view has a linked contents list, visible heading anchors, a return link to the workflow, and a Git source link. Python source remains a separate explicit option. Numbers denote reading order; arrows retain actual RDF relationship directions. The diagrams distinguish reconstructed simulation provenance from locally executed plotting and inspection. Jupyter support is presented honestly: the reader and PySD runner existed; the executed notebook is new.

Contents links use #workflow-<slug>, scroll the selected heading below the sticky header, and focus it. Both workflows remain in the document. Each inline diagram keeps a readable minimum width and scrolls horizontally on narrow screens; wheel and arrow keys retain normal document/region scrolling. Explore diagram opens the shared canvas, with a Back to workflows link returning to the same section. The viewport constraints of the canvas never apply to the workflow document.

## Elevation & Depth

Flat diagram with thin borders; only hover descriptions and search suggestions cast a small shadow. No decorative illustrations, gradients or animation.

## Shapes

Rounded rectangular ontology nodes, small rounded controls, arrowheads with readable relation labels. Semantic Model uses an editorial layout in tools/overview_layout.py: mathematics above, implementation and simulation below. Workflows shares the sequence renderer in tools/workflow_layout.py; tools/inspection_layout.py supplies the Python layout. Both diagrams' arrows and nodes come from the same semantic dataset as the RDF. Entity neighborhoods use deterministic Graphviz routing.

## Components

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Scrollbar | docs/semantic/style.css | DESIGN.md Colors → build_tokens.py → tokens.css | Global baseline, inline diagrams use stable gutter | Document and diagram scroll checks |
| Notebook reading | docs/semantic/tools/notebook_view.py and style.css | Executed inspect_results.ipynb → nbconvert HTML; shared tokens.css | Whole notebook / heading fragment | Saved-output integrity and browser section landing |
| View navigation | docs/semantic/app.js and index.html | DESIGN.md Layout | Semantic Model / Workflows / entity neighborhood | Browser navigation and refresh |
| Graph rendering | docs/semantic/tools/build_graphs.py | data/model.json and RDF | Overview / workflow / neighborhood | RDF edge integrity and browser rendering |

app.js owns graph navigation, the workflow contents and sections, search, pan, zoom and the shared hover/focus description. Its bindGraph helper supplies identical node behavior on the canvas and inline diagrams, with unique SVG IDs for each instance. build_graphs.py owns all node and arrow layouts. index.html owns the two-tab header and canvas chrome. Anchors navigate; native buttons zoom or fit. File nodes and implementation variables open their sources in a new tab. Scientific quantities, formulas and collection nodes open their neighborhoods, even when their evidence includes source URLs. Literature and software nodes link to their sources. Each view generates its colour legend from its actual entity types. Search opens a local neighborhood without navigating to GitHub. Notebook nodes open a locally rendered view of the complete notebook; its sections are fragments of that same view, not separate files. Explicit repository actions, tables and figures open commit-pinned sources in GitHub. The reader’s Git source link follows the current workflow branch. No artifact download controls are offered. No external rendering dependencies or network fonts.

Escape dismisses descriptions and search. Hover descriptions also appear on keyboard focus. Search supports keyboard traversal, Enter and an explicit clear button. The input is a transient local entity finder; committed entity selection, rather than the draft query, is stored in the URL. Arrow keys provide a non-drag pan alternative. Empty search results explain the state. A failed dataset load shows an explanation and the RDF source link remains available. No remote mutations, publishing or simulation execution are offered.

Entity links preserve their parent view in #overview/<entity> or #workflows/<entity>, including on refresh and browser Back. Workflow links carry ?from=<slug> within the fragment to preserve the section; full diagrams use #workflows/diagram/<slug>. Legacy entity URLs still open their neighborhood. Removed curated-view URLs fall back to Semantic Model. Each route sets a descriptive document title and keeps its owning navigation link selected. Generated artifacts and original inputs retain separate commit-pinned GitHub sources. The RDF header link points to the current workflow branch. The browser does not run simulations, notebooks or plotting commands. The notebook reading page uses the same two-tab header, fonts, colours and global scrollbar baseline, a 1,100px document column, code prompts and locally scrolling code/table regions. Saved plots reserve their aspect ratio; heading targets sit below the sticky header and receive a visible outline. At narrow widths, prompts move above code and tables scroll within their regions. No NFDI4Ing launch control is shown until an authenticated launch path is tested.

## Do's and Don'ts

- Keep the graph primary and surrounding text minimal.
- Preserve actual ontology types and existing evidence-backed relationship directions.
- Keep source links and literature accessible directly from nodes.
- Do not copy ontology type names from the sample when the model uses a different verified type.
- Do not imply the documented runs were newly executed or draft identifiers are published.

The revised overview separates a MathModDB mathematical-model instance, governing formulas, scientific state quantities, parameter declarations, both native implementation files, software tools, a computational task, its setup plan, and requested outputs. It does not represent the generic task as a completed case-1 execution. Overview connections outside established ontology predicates are explicit review proposals in the local sd namespace.
