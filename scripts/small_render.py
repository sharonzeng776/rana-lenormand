from pathlib import Path
from core import *
from legacy_render import render as legacy
def output(f,reveal,path):
 validate_facts(f);ids=reveal['visible_slots'];ps=[p for p in f['placements'] if p['position'] in ids]
 cards=json.loads((Path(__file__).resolve().parents[1]/'references/cards.json').read_text(encoding='utf-8'));by={int(c['id']):c for c in cards}
 vm=[dict(p,name=by[p['card_id']]['zh']) for p in ps]
 maxr=max(p['row'] for p in f['placements']);maxc=max(p['column'] for p in f['placements']);lookup={(p['row'],p['column']):p for p in vm}
 text='\n'.join(' | '.join(f'{lookup[r,c]["slot_id"]}[{lookup[r,c]["group"]}] {lookup[r,c]["card_id"]} {lookup[r,c]["name"]}' if (r,c) in lookup else '·' for c in range(1,maxc+1)) for r in range(1,maxr+1))
 a={'normalized':{'profile':'muree40'},'cards':[by[p['card_id']] for p in vm],'positions':[dict(p,layers=[str(p['card_id'])],active_card_id=str(p['card_id'])) for p in vm],'audit':{'reading_sha256':f['facts_hash']}}
 try:
  manifest=legacy(a,Path(path),title='测试/咨询牌阵 · '+f['algorithm'])
  from html import escape
  import xml.etree.ElementTree as ET
  tree=ET.parse(path);coords={int(e.attrib['data-position']):(e.attrib['x'],float(e.attrib['y'])-4) for e in tree.iter() if e.tag.endswith('image')}
  extra=''.join(f'<text x="{coords[p["position"]][0]}" y="{coords[p["position"]][1]}" font-size="11">{escape(p["slot_id"]+" · "+p["group"])}</text>' for p in vm)
  target=Path(path);target.write_text(target.read_text(encoding='utf-8').replace('</svg>',extra+'</svg>'),encoding='utf-8')
  manifest.update(view_model=vm,facts_hash=f['facts_hash'],reveal_revision=reveal['revision'])
  target.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
  return {'text':text,'image':str(target),'view_model':vm,'facts_hash':f['facts_hash']}
 except (OSError,ValueError,KeyError) as e:return {'text':text,'image_error':str(e),'view_model':vm,'facts_hash':f['facts_hash']}
