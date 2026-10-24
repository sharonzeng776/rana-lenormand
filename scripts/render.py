from pathlib import Path
from core import *
from legacy_render import render as svg_render
def render(facts,reveal,output):
    validate_facts(facts)
    require(sorted(reveal['visible_slots'])==list(range(1,len(facts['order'])+1)),'PARTIAL_RENDER_NOT_ENABLED')
    root=Path(__file__).resolve().parents[1];cards=json.loads((root/'references/cards.json').read_text(encoding='utf-8'));by={int(c['id']):c for c in cards}
    adapted={'normalized':{'profile':'muree40'},'cards':[by[x] for x in facts['order']],
      'positions':[dict(p,layers=[str(p['card_id'])],active_card_id=str(p['card_id'])) for p in facts['placements']], 'audit':{'reading_sha256':facts['facts_hash']}}
    text='\n'.join(' | '.join(f'{p["position"]}:{p["card_id"]} {by[p["card_id"]]["zh"]}' for p in facts['placements'] if p['row']==r) for r in sorted({p['row'] for p in facts['placements']}))
    try:manifest=svg_render(adapted,Path(output))
    except (ValueError,KeyError,OSError) as e:return {'text':text,'image_error':str(e),'facts_hash':facts['facts_hash']}
    manifest['facts_hash']=facts['facts_hash'];manifest['reveal_revision']=reveal['revision'];Path(output).with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'text':text,'image':manifest['image'],'facts_hash':facts['facts_hash']}
