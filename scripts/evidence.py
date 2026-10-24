"""Bounded, versioned EPUB/course retrieval; no draw state is read here."""
from pathlib import Path
import json,hashlib,os
from core import *
from legacy_source import epub_units
import runtime_config as rc
ROOT=Path(__file__).resolve().parents[1]
HEADS={'Future','Work','Love','Money','Health, Body, and Spirit','Health, Body,and Spirit','Time or Timing','Time','Timing','Advice or Action','Advice','Objects and Areas','Orientation','Nuance','Nuances','In the Grand Tableau','Personal Story','Personal Stories','Contextual Meanings','When Using the Muree System','Some Combinations and Examples'}
ALIASES={'career':'Work','relationship':'Love','advice':'Advice or Action','timing':'Time or Timing','money':'Money','health':'Health, Body, and Spirit','objects':'Objects and Areas','state':'Future'}
def write(path,data):
 tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8');tmp.replace(path)
def index(cache):
 src=next(s for s in json.loads((ROOT/'references/sources.json').read_text(encoding='utf-8'))['local'] if s['id']=='essential-2');src=rc.book(src);p=Path(src['path']);require(p.is_file(),'SOURCE_MISSING: configure book_path in RANA_CONFIG')
 dest=rc.external(cache,'cache')/src['sha256']/'extract-v2';dest.mkdir(parents=True,exist_ok=True);meta=dest/'index.json';stat=[p.stat().st_size,p.stat().st_mtime_ns]
 existing=json.loads(meta.read_text(encoding='utf-8')) if meta.exists() else None
 if not existing or existing['stat']!=stat:
  require(hashlib.sha256(p.read_bytes()).hexdigest()==src['sha256'],'SOURCE_CHANGED')
  cards={}
  for n,h,t in epub_units(p):
   lines=t.splitlines();write(dest/f'{n}.json',{'href':h,'paragraphs':lines})
   if 14<=n<=53:cards[n-13]={'unit':n,'href':h,'sections':[{'title':x,'start':i+1} for i,x in enumerate(lines) if x in HEADS]}
  write(meta,{'stat':stat,'sha':src['sha256'],'extractor':'epub-h-p-li-v2','cards':cards})
 return dest,json.loads(meta.read_text(encoding='utf-8'))
def retrieve(cache,card=None,topic='Work',unit=None,start=None,end=None,offset=0,limit=7000,course_query=None):
 dest,ix=index(cache);topic=ALIASES.get(topic,topic);require(type(offset) is int and offset>=0 and type(limit) is int and 100<=limit<=20000,'INVALID_WINDOW')
 if card is not None:require(type(card) is int and 1<=card<=40,'INVALID_CARD');unit=card+13
 require(type(unit) is int and 1<=unit<=71,'INVALID_UNIT')
 data=json.loads((dest/f'{unit}.json').read_text(encoding='utf-8'));ls=data['paragraphs'];ranges=[]
 if start is not None:
  require(type(start) is int and type(end) is int and 1<=start<=end<=len(ls),'INVALID_RANGE');ranges=[('technique',start,end)]
 else:
  for title in [topic,'When Using the Muree System']:
   for i,line in enumerate(ls):
    if line==title:ranges.append((title,i+1,next((j for j in range(i+1,len(ls)) if ls[j] in HEADS),len(ls))))
  first=next((i for i,l in enumerate(ls) if l in HEADS),min(12,len(ls)));ranges.insert(0,('general_context',1,max(1,first)))
 missing=[] if start is not None or any(t==topic for t,a,b in ranges) else [topic]
 result=[]
 for title,a,b in ranges:
  text='\n'.join(ls[a-1:b]);result.append({'title':title,'start':a,'end':b,'text':text})
 full=json.dumps(result,ensure_ascii=False);chunk=full[offset:offset+limit];ref='E:'+digest({'sha':ix['sha'],'unit':unit,'ranges':[(a,b) for t,a,b in ranges]})
 return {'source_id':ref,'source_kind':'book_explicit_or_examples_check_context','source_hash':ix['sha'],'unit':unit,'href':data['href'],'topic':topic,'missing':missing,'extractor':ix['extractor'],'sections':result if offset==0 and len(full)<=limit else None,'text_window':chunk,'offset':offset,'truncated':offset+limit<len(full),'next_offset':offset+limit if offset+limit<len(full) else None,'total_chars':len(full),'muree_policy':'Apply chapter Muree overrides; retain traditional limitations; examples are not universal rules.','course':course(cache,course_query) if course_query else None,'user_supplements':json.loads((ROOT/'references/user-supplements.json').read_text(encoding='utf-8')) if (ROOT/'references/user-supplements.json').exists() else None}
def course(cache,query):
 import re
 from course_outline import Outline
 dest=rc.external(cache,'cache')/'course-v2';dest.mkdir(parents=True,exist_ok=True);matches=[]
 for p in sorted(rc.course_dir().glob('*.html')):
  st=[p.stat().st_size,p.stat().st_mtime_ns];f=dest/(p.stem+'.json');old=json.loads(f.read_text(encoding='utf-8')) if f.exists() else None
  if not old or old['stat']!=st:
   raw=p.read_bytes();outline=Outline();outline.feed(raw.decode('utf-8-sig'));nodes=[]
   for n in outline.nodes:nodes.append({'id':n['id'],'depth':n['depth'],'text':re.sub(r'\s+',' ',''.join(n['text_parts'])).strip()})
   old={'stat':st,'sha':hashlib.sha256(raw).hexdigest(),'nodes':nodes};write(f,old)
  for i,n in enumerate(old['nodes']):
   if query.casefold() in n['text'].casefold():matches.append({'source_kind':'course_note_user_attributed','file':p.name,'sha':old['sha'],'node':n['id'],'context':old['nodes'][max(0,i-2):i+3]})
 return {'matches':matches[:20],'truncated':len(matches)>20,'total_matches':len(matches),'supplements':'User course supplements are distinct: GT default6months/3months scaling, retain first draw, H first relation essence; see rules.json.'}
