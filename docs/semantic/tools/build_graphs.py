"""Build dependency-free, routed SVG views from the semantic projection."""
import json, subprocess, textwrap
from overview_layout import render_overview
from workflow_layout import render_workflow
from inspection_layout import render_inspection
from pathlib import Path
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'data/model.json').read_text()); entities={e['id']:e for e in m['entities']}; ids=list(entities)
palette={'Ontology class':('#e9eef3','#8d9cab'),'Quantity':('#ffffff','#718894'),'Formula':('#d6e7ed','#6993a6'),'Task':('#f9ddd7','#bc6354'),'Collection':('#f6f6eb','#aaa580'),'Dataset':('#dce9ff','#7698c6'),'Literature':('#eee5f4','#9476ac'),'Concept':('#f9ddd7','#bc6354'),'Model':('#bfdeeb','#3f7f9e'),'File':('#dce9ff','#7698c6'),'Run':('#d8ead0','#80a865'),'Method':('#ffe8cc','#cd963f'),'Tool':('#fff2ce','#c9ac54'),'Configuration':('#ffffbd','#aaa354'),'Field':('#e4d7ec','#9c7ab1'),'Binding':('#e4d7ec','#9c7ab1'),'Unit':('#c6d7e0','#648295')}
palette.update({'Visualization':('#dce9ff','#7698c6'),'Assignment':('#e4d7ec','#9c7ab1'),'Notebook':('#eee5f4','#9476ac'),'Notebook section':('#eee5f4','#9476ac'),'Script':('#dce9ff','#7698c6')})
short={'literature':'System Dynamics\nLearning Guide','model':'Kaibab ecosystem\nmodel','run/case1':'Case 1 simulation','run/case2':'Case 2 simulation'}
def render(selected,edges, direction="TB"):
 lines=['digraph G { graph [rankdir='+direction+', bgcolor="transparent", pad="0.35", nodesep="0.48", ranksep="0.8", splines=polyline, outputorder=edgesfirst]; node [shape=box, style="rounded,filled", fontname="Arial", fontsize=16, margin="0.18,0.13", penwidth=1.5]; edge [fontname="Arial", fontsize=11, color="#4c565d", fontcolor="#46515a", arrowsize=0.65];']
 for id in sorted(selected):
  e=entities[id]; label=e.get('displayLabel') or short.get(id,e['path'].split('/')[-1] if e['kind']=='File' and 'path' in e else e['label']); label='\n'.join(textwrap.fill(x,28,break_long_words=False,break_on_hyphens=False) for x in label.split('\n')); typ=e.get('displayType') or ('m4i:NumericalVariable' if 'm4i:NumericalVariable' in e['types'] else (e['types'][0] if e['types'] else e['kind'])); color,border=palette.get(e['kind'],('#ffffff','#7f8a92'))
  lines.append(f'n{ids.index(id)} [id="entity-{ids.index(id)}", label={json.dumps(label+chr(10)+typ,ensure_ascii=False)}, fillcolor="{color}", color="{border}"];')
 for edge in edges:
  if edge['source'] in selected and edge['target'] in selected:
   lines.append(f'n{ids.index(edge["source"])} -> n{ids.index(edge["target"])} [label={json.dumps(edge["label"],ensure_ascii=False)}];')
 lines.append('}')
 svg=subprocess.check_output(['dot','-Tsvg'],input='\n'.join(lines).encode()).decode(); svg=svg[svg.index('<svg'):]; return svg
views={'overview':m['overview'],**{workflow['graphKey']:workflow for workflow in m['workflows']}}
graphs={}
for key,view in views.items():
 selected=view['entities']
 assert set(selected)<=entities.keys(), set(selected)-entities.keys()
 selected=set(selected); edges=view['edges']
 svg=render_overview(m,entities,ids,palette) if key=='overview' else render_workflow(m,entities,ids,palette) if view['slug']=='case2-parameter-to-figure' else render_inspection(m,entities,ids,palette)
 graphs[key]={'svg':svg,'count':len(selected),'total':len(selected),'legend':[{'label':k,'fill':palette.get(k,('#ffffff','#7f8a92'))[0]} for k in sorted({entities[i]['kind'] for i in selected})]}
for id in ids:
 edges=[e for e in m['edges'] if id in (e['source'],e['target'])]; neighbors=list(dict.fromkeys(e['target'] if e['source']==id else e['source'] for e in edges)); selected={id,*neighbors[:28]}; chosen=[e for e in edges if e['source'] in selected and e['target'] in selected]
 graphs[id]={'svg':render(selected,chosen),'count':len(selected),'total':len(neighbors)+1,'legend':[{'label':k,'fill':palette.get(k,('#ffffff','#7f8a92'))[0]} for k in sorted({entities[i]['kind'] for i in selected})]}
(root/'data/graphs.js').write_text('window.KAIBAB_GRAPHS = '+json.dumps(graphs)+';\n')
print(f'Built {len(graphs)} routed graphs')
