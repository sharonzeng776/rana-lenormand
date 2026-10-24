from pathlib import Path
import json,math,base64,hashlib
from html import escape
import stage4 as m
from core import require
from legacy_render import load_card_images
LABELS=['true_intentions','outer_mask','hidden_nature','emotional_core','behavior_outcome']
HOUSES=['self','finances','communication','home','creativity','responsibilities','partnership','joint_resources','education_travel','career_status','friends_hopes','unknown_fears']
def model(s,request):
 public=m.public_view(s,request);conf=json.loads(s.db.execute('SELECT config FROM jobs WHERE id=?',(request,)).fetchone()[0]);f,kind=m.raw(s,request);visible=public['reveal_state']['visible_slots'];v=conf.get('variant');vm=[]
 for p in f['placements']:
  i=p['position'];cid=p['card_id']
  if i not in visible:continue
  if kind=='clarifier':group=f'explain {conf["parent"]} position {conf["target"]}: {conf["ambiguity"]}';x=(i-1)*210+30;y=90;role='clarifier'
  elif v.startswith('identifier.'):
   n=1 if v.endswith('one') else 2;r=(i-1)//n;group=LABELS[r];x=(i-1)%n*210+30;y=r*350+90;role='main'
  elif i>36:
   if v=='yearly':group=public['allocation']['months'][i-37];x=conf['months'].index(group)*210+30;offset=sum(1 for j in range(37,i) if public['allocation']['months'][j-37]==group);y=1200+offset*350;role='month_supplement'
   else:group='global_attention';x=(i-37)*210+1700 if v=='astro.wheel' else (i-37)*210+30;y=2000 if v=='astro.wheel' else 1200;role='global_attention'
  else:
   g=(i-1)//3;k=(i-1)%3;group=conf['months'][g] if v=='yearly' else f'house{g+1}: {HOUSES[g]}';role='main'
   if v=='astro.wheel':
    angle=math.pi+math.pi/12+g*math.pi/6;x=2100+1700*math.cos(angle)+k*200-200;y=2100-1700*math.sin(angle)
   else:x=g*210+30;y=k*350+90
  vm.append({'position':i,'card_id':cid,'group':group,'role':role,'x':round(x,2),'y':round(y,2)})
 return public,vm
def steps(s,request):
 public,vm=model(s,request);conf=json.loads(s.db.execute('SELECT config FROM jobs WHERE id=?',(request,)).fetchone()[0]);groups={}
 for p in vm:groups.setdefault(p['group'],[]).append({'position':p['position'],'card_id':p['card_id'],'role':p['role']})
 return {'request':request,'groups':[{'meaning':g,'cards':ps,'source':'product_clarifier_policy' if public['kind']=='clarifier' else m.SERIES[conf['variant']]} for g,ps in groups.items()],'reserve_count':public.get('reserve_count',0),'commitment':public['commitment']}
def render(s,request,output):
 public,vm=model(s,request);root=Path(__file__).resolve().parents[1];cards={int(c['id']):c for c in json.loads((root/'references/cards.json').read_text(encoding='utf-8'))}
 text='\n'.join(f'{p["group"]} | position {p["position"]}: {p["card_id"]} {cards[p["card_id"]]["zh"]} ({p["role"]})' for p in vm)
 result={'text':text,'view_model':vm,'commitment':public['commitment']}
 try:art=load_card_images([str(p['card_id']) for p in vm],'user')
 except (OSError,ValueError,KeyError):return {**result,'image_error':'ASSET_UNAVAILABLE'}
 width=max(p['x'] for p in vm)+230;height=max(p['y'] for p in vm)+350
 body=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="#fffaf0"/>']
 placements=[]
 for p in vm:
  path,data,mime=art[str(p['card_id'])];x,y=p['x'],p['y'];label=escape(p['group']+f' / {p["position"]} / {p["card_id"]}')
  body.append(f'<text x="{x}" y="{y-8}" font-size="11">{label}</text><image data-position="{p["position"]}" data-card="{p["card_id"]}" x="{x}" y="{y}" width="180" height="280" preserveAspectRatio="xMidYMid meet" href="data:{mime};base64,{base64.b64encode(data).decode()}"/>')
  placements.append({**p,'source_sha256':hashlib.sha256(data).hexdigest()})
 body.append('</svg>');target=Path(output);target.parent.mkdir(parents=True,exist_ok=True);target.write_text('\n'.join(body),encoding='utf-8');manifest={'request':request,'commitment':public['commitment'],'reveal_revision':public['reveal_state']['revision'],'placements':placements};target.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 return {**result,'image':str(target)}
