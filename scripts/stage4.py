"""Persistent clarifiers and staged layouts. Raw facts never encode allocations."""
import json,secrets,math,re
import capabilities
from pathlib import Path
from core import *
from session_store import Store
from small import Stream

SERIES={'yearly':'B55:442-444','astro.wheel':'B55:376-401;image/141.jpg','astro.columns':'B55:376-401','identifier.one':'B66:230-237','identifier.two':'B66:230-237'}
ALGORITHM='stage4-shuffle-pop-v1'
def init(s):
 s.db.executescript('''CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY,parent TEXT,target INTEGER,body TEXT,UNIQUE(parent,target));
 CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,kind TEXT,config TEXT);
 CREATE TABLE IF NOT EXISTS allocations(id TEXT PRIMARY KEY,body TEXT);
 CREATE TABLE IF NOT EXISTS read_ack(id TEXT PRIMARY KEY,body TEXT);''')
def raw(s,request):
 r=s.db.execute('SELECT body,kind FROM draws WHERE request=?',(request,)).fetchone();require(r and r[0],'DRAW_NOT_READY');d=json.loads(r[0]);f=d.get('facts',d);require('placements' in f,'BOUNDARY_HOLD');validate_facts(f);return f,r[1]
def public_view(s,request):
 f,kind=raw(s,request);rev,slots=s.db.execute('SELECT revision,slots FROM reveal WHERE request=?',(request,)).fetchone();slots=json.loads(slots)
 conf=json.loads(s.db.execute('SELECT config FROM jobs WHERE id=?',(request,)).fetchone()[0]);seed=s.db.execute('SELECT seed FROM draws WHERE request=?',(request,)).fetchone()[0]
 out={'request':request,'kind':kind,'commitment':digest({'secret_nonce':seed,'facts_hash':f['facts_hash']}),'reveal_state':{'revision':rev,'visible_slots':slots},'cards':[{'position':p['position'],'card_id':p['card_id']} for p in f['placements'] if p['position'] in slots]}
 if len(slots)==len(f['order']):out['facts_hash']=f['facts_hash']
 if kind=='clarifier':out['target']={k:conf[k] for k in ['parent','target','ambiguity','count']}
 if conf.get('variant')=='yearly':out['reserve_count']=4;out['months']=conf['months']
 allocation=s.db.execute('SELECT body FROM allocations WHERE id=?',(request,)).fetchone()
 if allocation:out['allocation']=json.loads(allocation[0])
 return out
def prepare(s,ticket,parent,target,ambiguity,evidence,announcement,count):
 init(s);require(type(count) is int and 1<=count<=3 and type(target) is int,'INVALID_CLARIFIER')
 require(ambiguity and evidence and announcement,'PREPARE_INCOMPLETE')
 c={'parent':parent,'target':target,'ambiguity':ambiguity,'evidence':evidence,'announcement':announcement,'count':count}
 s.db.execute('BEGIN IMMEDIATE')
 try:
  old=s.db.execute('SELECT body FROM tickets WHERE id=?',(ticket,)).fetchone()
  if old:require(json.loads(old[0])==c,'TICKET_IMMUTABLE');s.db.commit();return {'ticket':ticket,'status':'prepared'}
  f,kind=raw(s,parent);require(kind!='clarifier','NO_RECURSION')
  visible=json.loads(s.db.execute('SELECT slots FROM reveal WHERE request=?',(parent,)).fetchone()[0]);require(target in visible,'TARGET_NOT_REVEALED')
  require(not s.db.execute('SELECT 1 FROM tickets WHERE parent=? AND target=?',(parent,target)).fetchone(),'CLARIFIER_LIMIT')
  job=s.db.execute('SELECT config FROM jobs WHERE id=?',(parent,)).fetchone()
  if job and json.loads(job[0]).get('variant')=='yearly':require(target<=36,'TARGET_NOT_MAIN')
  s.db.execute('INSERT INTO tickets VALUES (?,?,?,?)',(ticket,parent,target,canonical(c).decode()));s.event('clarifier_prepared',{'ticket':ticket,**c});s.db.commit()
 except:s.db.rollback();raise
 return {'ticket':ticket,'status':'prepared'}
def months(start):
 require(isinstance(start,str) and re.fullmatch(r'\d{4}-\d{2}',start),'INVALID_MONTH');y,m=map(int,start.split('-'));require(1<=m<=12,'INVALID_MONTH')
 return [f'{y+(m-1+i)//12:04d}-{(m-1+i)%12+1:02d}' for i in range(12)]
def configure(s,inquiry,plan):
 init(s);require(set(plan)=={'question','intent','topic','spread','variant','profile','roles','primary_reference','timeframe','context','acceptance'},'INVALID_PLAN_FIELDS')
 v=plan['variant'];require(plan['spread']=='series' and v in SERIES,'CAPABILITY_DISABLED');require(capabilities.ready('series',v,SERIES[v],ALGORITHM),'CAPABILITY_NOT_ACCEPTED');require(plan['question'] and plan['acceptance'].get('question_ref') and plan['acceptance'].get('spread_ref'),'PLAN_NOT_READY')
 require(not plan['acceptance'].get('rewritten') or plan['acceptance'].get('rewrite_confirmed'),'REWRITE_NOT_CONFIRMED')
 require(set(plan['context'])<=({'start_month'} if v=='yearly' else set()),'INVALID_CONTEXT')
 if v=='yearly':months(plan['context'].get('start_month'))
 s.db.execute('BEGIN IMMEDIATE')
 try:
  require(not s.db.execute('SELECT 1 FROM plans WHERE id=?',(inquiry,)).fetchone(),'PLAN_LOCKED');s.db.execute('INSERT INTO plans VALUES (?,?,?,0)',(inquiry,canonical(plan).decode(),digest(plan)));s.db.commit()
 except:s.db.rollback();raise
 return {'inquiry_id':inquiry,'revision':0,'plan_hash':digest(plan)}
def make_facts(order,ph,request):
 f={'schema_version':2,'origin':'random','draw_id':request,'plan_hash':ph,'deck_id':'rana40-v1','algorithm':ALGORITHM,'order':order,'placements':[{'position':i+1,'card_id':cid,'row':1,'column':i+1,'house':None} for i,cid in enumerate(order)]};f['facts_hash']=digest(f);return f
def job(s,request,kind,conf,ph,inquiry):
 # Caller holds the writer transaction. Persist entropy before pure computation.
 old=s.db.execute('SELECT inquiry,seed,body,kind FROM draws WHERE request=?',(request,)).fetchone()
 if old:
  require(old[0]==inquiry and old[3]==kind,'REQUEST_CONFLICT');existing=json.loads(s.db.execute('SELECT config FROM jobs WHERE id=?',(request,)).fetchone()[0]);require(existing==conf,'REQUEST_CONFLICT');return bytes.fromhex(old[1]),bool(old[2])
 seed=secrets.token_bytes(32);s.db.execute('INSERT INTO draws VALUES (?,?,?,NULL,?,?)',(request,inquiry,seed.hex(),kind,conf.get('parent')));s.db.execute('INSERT INTO jobs VALUES (?,?,?)',(request,kind,canonical(conf).decode()));s.event('stage4_seed_prepared',{'request':request,'kind':kind});return seed,False
def finish(s,request,seed,n,ph,visible):
 order=Stream(seed).shuffle(list(range(1,41)))[:n];f=make_facts(order,ph,request);validate_facts(f)
 s.db.execute('BEGIN IMMEDIATE')
 try:
  if s.db.execute('SELECT body FROM draws WHERE request=?',(request,)).fetchone()[0] is None:
   s.db.execute('UPDATE draws SET body=? WHERE request=?',(canonical(f).decode(),request));s.db.execute('INSERT INTO reveal VALUES (?,0,?)',(request,json.dumps(list(range(1,visible+1)))));s.event('stage4_completed',{'request':request})
  s.db.commit()
 except:s.db.rollback();raise
 return public_view(s,request)
def draw_clarifier(s,ticket,request,**unknown):
 require(not unknown,'TICKET_IMMUTABLE');init(s);s.db.execute('BEGIN IMMEDIATE')
 try:
  r=s.db.execute('SELECT body FROM tickets WHERE id=?',(ticket,)).fetchone();require(r,'TICKET_REQUIRED');c=json.loads(r[0]);prior=s.db.execute("SELECT id FROM jobs WHERE kind='clarifier' AND config=?",(canonical(c).decode(),)).fetchone();require(not prior or prior[0]==request,'CLARIFIER_LIMIT')
  seed,done=job(s,request,'clarifier',c,digest(c),'clarifier:'+ticket);s.db.commit()
 except:s.db.rollback();raise
 if done:return public_view(s,request)
 return finish(s,request,seed,c['count'],digest(c),c['count'])
def new(s,inquiry,request,revision,reason=None,parent=None,**unknown):
 init(s);require(not unknown,'FORBIDDEN_DRAW_FIELDS');s.db.execute('BEGIN IMMEDIATE')
 try:
  row=s.db.execute('SELECT body,hash,revision FROM plans WHERE id=?',(inquiry,)).fetchone();require(row,'PLAN_NOT_READY');p=json.loads(row[0]);v=p['variant'];require(v in SERIES,'CAPABILITY_DISABLED');require(capabilities.ready('series',v,SERIES[v],ALGORITHM),'CAPABILITY_NOT_ACCEPTED')
  c={'variant':v}
  if parent or reason:
   require(parent and reason and reason.get('kind')=='explicit_user' and reason.get('message_ref') and s.db.execute('SELECT 1 FROM draws WHERE request=? AND inquiry=? AND body IS NOT NULL',(parent,inquiry)).fetchone(),'REDRAW_NOT_AUTHORIZED');c.update(parent=parent,reason=reason)
  if v=='yearly':c['months']=months(p['context']['start_month'])
  old=s.db.execute('SELECT 1 FROM draws WHERE request=?',(request,)).fetchone()
  if not old:require(row[2]==revision,'STALE_REVISION');require(parent or not s.db.execute('SELECT 1 FROM draws WHERE inquiry=?',(inquiry,)).fetchone(),'FIRST_DRAW_RETAINED');s.db.execute('UPDATE plans SET revision=revision+1 WHERE id=?',(inquiry,))
  seed,done=job(s,request,'series',c,row[1],inquiry);s.db.commit()
 except:s.db.rollback();raise
 if done:return public_view(s,request)
 n=5 if v=='identifier.one' else 10 if v=='identifier.two' else 40
 return finish(s,request,seed,n,row[1],36 if v=='yearly' else n)
def acknowledge(s,request,reading_ref):
 init(s);require(reading_ref,'READING_REQUIRED');f,_=raw(s,request);c=json.loads(s.db.execute('SELECT config FROM jobs WHERE id=?',(request,)).fetchone()[0]);require(c['variant']=='yearly','NOT_YEARLY')
 s.db.execute('INSERT OR IGNORE INTO read_ack VALUES (?,?)',(request,canonical({'reading_ref':reading_ref}).decode()));return {'request':request,'reading_recorded':True}
def allocate(s,request,months_in_order,revision,message_ref):
 init(s);s.db.execute('BEGIN IMMEDIATE')
 try:
  c=json.loads(s.db.execute('SELECT config FROM jobs WHERE id=?',(request,)).fetchone()[0]);require(c.get('variant')=='yearly','NOT_YEARLY');require(len(months_in_order)==4 and all(m in c['months'] for m in months_in_order) and message_ref,'INVALID_ALLOCATION')
  allocation={'months':months_in_order,'message_ref':message_ref};old=s.db.execute('SELECT body FROM allocations WHERE id=?',(request,)).fetchone()
  if old:require(json.loads(old[0])==allocation,'ALLOCATION_LOCKED')
  else:
   require(s.db.execute('SELECT 1 FROM read_ack WHERE id=?',(request,)).fetchone(),'READ_MONTHS_FIRST');r=s.db.execute('SELECT revision FROM reveal WHERE request=?',(request,)).fetchone();require(r and r[0]==revision,'STALE_REVISION');s.db.execute('INSERT INTO allocations VALUES (?,?)',(request,canonical(allocation).decode()));s.event('allocation_committed',{'request':request,**allocation})
  s.db.commit()
 except:s.db.rollback();raise
 return reveal_allocated(s,request)
def reveal_allocated(s,request):
 # Allocation already committed: recovery finishes reveal without random calls.
 require(s.db.execute('SELECT 1 FROM allocations WHERE id=?',(request,)).fetchone(),'ALLOCATION_REQUIRED')
 s.db.execute('BEGIN IMMEDIATE')
 try:
  r=s.db.execute('SELECT slots FROM reveal WHERE request=?',(request,)).fetchone()
  if len(json.loads(r[0]))<40:s.db.execute('UPDATE reveal SET slots=?,revision=revision+1 WHERE request=?',(json.dumps(list(range(1,41))),request));s.event('allocation_revealed',{'request':request})
  s.db.commit()
 except:s.db.rollback();raise
 return public_view(s,request)
def audit(s,request,confirmed_ref):
 v=public_view(s,request);require(confirmed_ref and 'facts_hash' in v,'AUDIT_NOT_AVAILABLE');f,_=raw(s,request);return {'request':request,'facts':f,'algorithm':ALGORITHM,'seed_hex':s.db.execute('SELECT seed FROM draws WHERE request=?',(request,)).fetchone()[0]}
