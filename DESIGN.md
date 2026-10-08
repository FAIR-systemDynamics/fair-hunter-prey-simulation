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

A full-window pan-and-zoom canvas below a compact header. Four diagrams: Overview, Ecosystem, Files & runs, Scenarios. A small search opens an entity's direct relationships. Bottom legend and zoom buttons float over the canvas; no permanent detail sidebar. On mobile the header wraps into two rows. Fit reserves space for the legend and header. Dense neighborhoods explicitly state if connections are omitted; complete RDF remains downloadable.

## Elevation & Depth

Flat diagram with thin borders; only hover descriptions and search suggestions cast a small shadow. No decorative illustrations, gradients or animation.

## Shapes

Rounded rectangular ontology nodes, small rounded controls, arrowheads with readable relation labels. The Overview uses an editorial layout in tools/overview_layout.py: mathematics above, implementation and simulation below. Its arrows and nodes come from the same semantic dataset as the RDF. Other views and entity neighborhoods use deterministic Graphviz routing.

## Components

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Scrollbar | docs/semantic/style.css | DESIGN.md Colors | Search results only | Narrow viewport check |

app.js owns graph navigation, search, pan, zoom and the shared hover/focus description. build_graphs.py owns all node and arrow layouts. index.html owns header and legend. Anchors navigate; native buttons zoom or fit. File nodes and implementation variables open their sources in a new tab. Scientific quantities, formulas and collection nodes open their neighborhoods, even when their evidence includes source URLs. Literature and software nodes link to their sources. Each view generates its colour legend from its actual entity types. Search opens a local neighborhood without navigating to GitHub. Other nodes open their local neighborhood. No external rendering dependencies or network fonts.

Escape dismisses descriptions and search. Hover descriptions also appear on keyboard focus. Search supports keyboard traversal, Enter and an explicit clear button. The input is a transient local entity finder; committed entity selection, rather than the draft query, is stored in the URL. Arrow keys provide a non-drag pan alternative. Empty search results explain the state. A failed dataset load shows an explanation and the RDF download remains available. No remote mutations, publishing or simulation execution are offered.

## Do's and Don'ts

- Keep the graph primary and surrounding text minimal.
- Preserve actual ontology types and existing evidence-backed relationship directions.
- Keep source links and literature accessible directly from nodes.
- Do not copy ontology type names from the sample when the model uses a different verified type.
- Do not imply the documented runs were newly executed or draft identifiers are published.

The revised overview separates a MathModDB mathematical-model instance, governing formulas, scientific state quantities, parameter declarations, both native implementation files, software tools, a computational task, its setup plan, and requested outputs. It does not represent the generic task as a completed case-1 execution. Overview connections outside established ontology predicates are explicit review proposals in the local sd namespace.
