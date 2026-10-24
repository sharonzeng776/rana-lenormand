import runtime_config as rc
"""Text/SVG/PNG share one verified, visible-only model. No random calls."""
from pathlib import Path
from html import escape
import json,base64,hashlib,struct
from core import *
import reading,stage4_view
from legacy_render import load_card_images
FONT='C:/Windows/Fonts/msyh.ttc'
def glyph_ranges(path):
 data=Path(path).read_bytes();base=struct.unpack_from('>I',data,12)[0] if data[:4]==b'ttcf' else 0;n=struct.unpack_from('>H',data,base+4)[0];off=None
 for i in range(n):
  tag,_,start,size=struct.unpack_from('>4sIII',data,base+12+i*16)
  if tag==b'cmap':off=start
 require(off is not None,'FONT_CMAP_MISSING');count=struct.unpack_from('>H',data,off+2)[0];ranges=[]
 for i in range(count):
  platform,encoding,rel=struct.unpack_from('>HHI',data,off+4+i*8);p=off+rel;fmt=struct.unpack_from('>H',data,p)[0]
  if fmt==12:
   groups=struct.unpack_from('>I',data,p+12)[0]
   ranges.extend(struct.unpack_from('>III',data,p+16+j*12)[:2] for j in range(groups))
  elif fmt==4:
   seg=struct.unpack_from('>H',data,p+6)[0]//2;ends=struct.unpack_from('>'+str(seg)+'H',data,p+14);starts=struct.unpack_from('>'+str(seg)+'H',data,p+16+2*seg);ranges.extend(zip(starts,ends))
 return ranges
def model(s,request):
 f,p,rev,visible,commit=reading.state(s,request)
 if s.db.execute('SELECT 1 FROM jobs WHERE id=?',(request,)).fetchone():_,vm=stage4_view.model(s,request);vm=[dict(x) for x in vm]
 else:vm=[dict(x,x=30+(x['column']-1)*260,y=110+(x['row']-1)*440,group=x.get('group','宫'+str(x['house']) if x['house'] else '线阵'),role='main') for x in f['placements'] if x['position'] in visible]
 cards={int(c['id']):c['zh'] for c in json.loads((Path(__file__).resolve().parents[1]/'references/cards.json').read_text(encoding='utf-8'))}
 for x in vm:
  x['name']=cards[x['card_id']]
  if p and p['spread']=='small' and p['variant'].startswith('box.'):
   labels=['不建议投入','当下状态','可控行动'] if p['variant']=='box.advice' else ['担忧','状况','底流'] if p['variant'] in {'box.random','box.center'} else ['不可控','当下状态','可控']
   x['group']=labels[x['row']-1]+('·阶段'+str(x['column']) if p['variant']=='box.process' else '')
   if p['variant']=='box.center':
    x['preselected']=x['position']==5
    if x['preselected']:x['group']+='·预置焦点（非随机）'
 return {'request':request,'reveal_revision':rev,'commitment':commit,'placements':vm}
def render(s,request,output,font_path=None):
 font_path=font_path or rc.font()
 vm=model(s,request);ps=vm['placements'];details='\n'.join(f'{p["group"]} | 位置{p["position"]} · {p["card_id"]} {p["name"]}' for p in ps)
 # Match the sparse geometry rather than printing a cross or H as a line.
 xs=sorted({p['x'] for p in ps});ys=sorted({p['y'] for p in ps});cells={(p['x'],p['y']):p for p in ps}
 if len(xs)<=12:
  grid='\n'.join(' | '.join(f'{cells[x,y]["card_id"]:02} {cells[x,y]["name"]}' if (x,y) in cells else '　' for x in xs) for y in ys)
 else:grid='轮盘位置以PNG/SVG为准；下列按领域分组，宫序从九点起逆时针。'
 text=grid+'\n\n'+details;result={'text':text,'view_model':vm,'errors':[]}
 root=rc.external(output,'render output')
 if root.suffix.lower() in {'.png','.svg','.txt'}:root=root.with_suffix('')
 root.parent.mkdir(parents=True,exist_ok=True)
 def ext(suffix):return root.with_name(root.name+suffix)
 ext('.txt').write_text(text,encoding='utf-8')
 try:art=load_card_images([str(x['card_id']) for x in ps],'user')
 except (ValueError,KeyError,OSError) as e:return {**result,'errors':['ASSET_UNAVAILABLE: '+str(e)]}
 width=int(max(x['x'] for x in ps)+260);height=int(max(x['y'] for x in ps)+410);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="#fffaf0"/>'];manifest={**vm,'assets':[],'font':font_path}
 for p in ps:
  path,data,mime=art[str(p['card_id'])];x,y=p['x'],p['y'];label=f'位置{p["position"]} · {p["card_id"]} {p["name"]}';group='独立解释牌' if p.get('role')=='clarifier' else p['group']
  svg.append(f'<text x="{x}" y="{y-50}" font-size="14" font-family="Microsoft YaHei">{escape(group[:36])}</text><text x="{x}" y="{y-25}" font-size="17" font-family="Microsoft YaHei">{escape(label)}</text><image data-position="{p["position"]}" data-card="{p["card_id"]}" x="{x}" y="{y}" width="180" height="280" preserveAspectRatio="xMidYMid meet" href="data:{mime};base64,{base64.b64encode(data).decode()}"/>');manifest['assets'].append({'position':p['position'],'card_id':p['card_id'],'sha256':hashlib.sha256(data).hexdigest()})
 svg.append('</svg>');svgpath=ext('.svg');svgpath.write_text('\n'.join(svg),encoding='utf-8');result['svg']=str(svgpath)
 try:
  from PIL import Image,ImageDraw,ImageFont
  require(Path(font_path).is_file(),'FONT_MISSING');ranges=glyph_ranges(font_path);labels=''.join(p['group']+p['name'] for p in ps)+'位置'
  missing=sorted({ord(c) for c in labels if not any(a<=ord(c)<=b for a,b in ranges) and not c.isspace()});require(not missing,'FONT_GLYPH_MISSING:'+','.join(hex(x) for x in missing))
  font=ImageFont.truetype(font_path,17);small=ImageFont.truetype(font_path,14);im=Image.new('RGB',(width,height),'#fffaf0');d=ImageDraw.Draw(im)
  for p in ps:
   x,y=int(p['x']),int(p['y']);a=Image.open(art[str(p['card_id'])][0]).convert('RGB');a.thumbnail((180,280));im.paste(a,(x+(180-a.width)//2,y+(280-a.height)//2));group='独立解释牌' if p.get('role')=='clarifier' else p['group'];d.text((x,y-65),group[:36],font=small,fill='black');d.text((x,y-40),f'位置{p["position"]} · {p["card_id"]} {p["name"]}',font=font,fill='black')
  png=ext('.png');im.save(png);result['png']=str(png)
 except (OSError,ValueError,ImportError,Error,struct.error) as e:result['errors'].append('PNG_FAILED: '+str(e))
 ext('.txt').write_text(text,encoding='utf-8');ext('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');return result
