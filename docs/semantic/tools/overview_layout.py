"""Editorial layout for the review overview; content still comes from RDF projection."""
from html import escape
import textwrap

# x, y, width, height. Upper region: mathematics. Lower: implementation and task.
POSITIONS={
 'literature':(45,30,260,78), 'model':(625,30,260,78), 'class/mathematical-model':(1240,30,230,78),
 'overview/equations':(45,220,260,78), 'overview/parameters':(390,220,240,78),
 'quantity/deer':(750,220,210,78),'quantity/predators':(1000,220,220,78),'quantity/forage':(1260,220,210,78),
 'overview/lookups':(45,395,260,78),
 'file/models/kaibab_ecosystem_model.mdl':(390,395,310,86), 'file/models/kaibab_ecosystem_model.stmx':(775,395,310,86),
 'tool/vensim':(435,570,220,70),'tool/stella':(820,570,220,70),'tool/pysd':(1190,570,240,70),
 'task/simulate':(770,745,310,84),'overview/setup':(285,745,265,84),'overview/outputs':(1210,745,285,84),
 'overview/scenarios':(45,945,240,78),'overview/initial':(365,945,300,78),'overview/numerics':(750,945,280,78),
}
# Route points, label centre. All arrows retain the direction of the RDF assertion.
ROUTES={
 ('model','class/mathematical-model'):([(885,69),(1240,69)],(1060,57)),
 ('model','literature'):([(625,69),(305,69)],(463,57)),
 ('model','overview/equations'):([(665,108),(665,150),(175,150),(175,220)],(357,138)),
 ('model','overview/parameters'):([(710,108),(710,180),(510,180),(510,220)],(556,168)),
 ('model','quantity/deer'):([(790,108),(790,165),(855,165),(855,220)],(852,151)),
 ('model','quantity/predators'):([(835,108),(835,130),(1110,130),(1110,220)],(1068,118)),
 ('model','quantity/forage'):([(875,108),(875,155),(1365,155),(1365,220)],(1280,143)),
 ('overview/equations','overview/lookups'):([(175,298),(175,395)],(255,350)),
 ('file/models/kaibab_ecosystem_model.mdl','model'):([(590,395),(590,350),(732,350),(732,108)],(672,337)),
 ('file/models/kaibab_ecosystem_model.stmx','model'):([(995,395),(995,330),(742,330),(742,108)],(989,317)),
 ('file/models/kaibab_ecosystem_model.mdl','tool/vensim'):([(545,481),(545,570)],(618,529)),
 ('file/models/kaibab_ecosystem_model.stmx','tool/stella'):([(930,481),(930,570)],(1012,529)),
 ('tool/vensim','task/simulate'):([(545,640),(545,690),(840,690),(840,745)],(677,678)),
 ('tool/stella','task/simulate'):([(930,640),(930,745)],(975,695)),
 ('tool/pysd','task/simulate'):([(1310,640),(1310,690),(1010,690),(1010,745)],(1170,678)),
 ('task/simulate','model'):([(1080,762),(1115,762),(1115,720),(1560,720),(1560,120),(885,120),(885,100)],(1480,368)),
 ('task/simulate','overview/setup'):([(770,787),(550,787)],(660,775)),
 ('task/simulate','overview/outputs'):([(1080,809),(1210,809)],(1144,798)),
 ('overview/setup','overview/scenarios'):([(335,829),(335,883),(165,883),(165,945)],(199,871)),
 ('overview/setup','overview/initial'):([(417,829),(417,915),(515,915),(515,945)],(508,902)),
 ('overview/setup','overview/numerics'):([(500,829),(500,862),(890,862),(890,945)],(739,850)),
}

def render_overview(model,entities,ids,palette):
    selected=set(model['overview']['entities']);assert selected==set(POSITIONS)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1060"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 Z" fill="#56636c"/></marker></defs>']
    for edge in model['overview']['edges']:
        points,(lx,ly)=ROUTES[(edge['source'],edge['target'])]
        path='M'+' L'.join(f'{x},{y}' for x,y in points)
        parts.append(f'<g class="edge"><path d="{path}" fill="none" stroke="#657580" stroke-width="1.4" marker-end="url(#arrow)"/><text x="{lx}" y="{ly}" text-anchor="middle" font-size="13" fill="#46515a">{escape(edge["label"])}</text></g>')
    for key,(x,y,w,h) in POSITIONS.items():
        e=entities[key];fill,stroke=palette.get(e['kind'],('#ffffff','#7f8a92'))
        label=e.get('displayLabel',e['label']);lines=[]
        for line in label.split('\n'):lines+=textwrap.wrap(line,32,break_long_words=False,break_on_hyphens=False)
        caption=e.get('displayType',e['types'][0]); labely=y+(h-len(lines)*21-14)/2+17
        parts.append(f'<g class="node" id="entity-{ids.index(key)}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.7"/>')
        for n,line in enumerate(lines):
            size=14 if line.endswith(('.mdl','.stmx')) else 18
            parts.append(f'<text x="{x+w/2}" y="{labely+n*21}" text-anchor="middle" font-size="{size}">{escape(line)}</text>')
        parts.append(f'<text x="{x+w/2}" y="{y+h-13}" text-anchor="middle" font-size="11">{escape(caption)}</text></g>')
    parts.append('</svg>');return ''.join(parts)
