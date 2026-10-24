"""Stage3 strategies. No seed/order is accepted by the public new endpoint."""
import json,secrets,hashlib
import capabilities
from pathlib import Path
from core import canonical,digest,require,Error,validate_facts,relationship_key
from session_store import Store
from vendor.auditable_draw import _uniform_index

SPECS={
 'single':('B11:45-47',1,'sample-pop-v1'), 'pair':('B11:46-47',2,'sample-pop-v1'), 'three':('B55:105-125',3,'sample-pop-v1'),
 'answer.random':('B55:144-155',5,'remaining-shuffle-pick-v1'),
 'answer.focus':('B55:133-143',5,'shuffle-locate-window-v1'),
 'decision.book':('B55:258-268',6,'sample-pop-v1'),
 'decision.descriptive':('C第7集:035-049',6,'sample-pop-v1'),
 'box.random':('B55:296-343',9,'sample-pop-v1'),
 'box.center':('B55:329;D39选8',9,'preset-center-pop-v1'),
 'box.state':('C第9集:001-021',9,'sample-pop-v1'),
 'box.process':('C第10集:052-053',9,'sample-pop-v1'),
 'box.yesno':('C第10集:039-051',9,'sample-pop-v1'),
 'box.advice':('C第16集:034',9,'sample-pop-v1'),
 'cross':('B55:445-461',5,'sample-pop-v1'),
 'pyramid':('B55:431-441',9,'sample-pop-v1'),
 'h.once':('C第8集:001-014;U首次;D一次七张顺序',7,'sample-pop-v1')}
TECHNIQUES={'storyline','pairs','lotus','135-24','group'}
def validate_small(p):
 require(p.get('variant') in SPECS,'CAPABILITY_DISABLED');v=p['variant'];o=p.get('context',{});require(capabilities.ready('small',v,SPECS[v][0],SPECS[v][2]),'CAPABILITY_NOT_ACCEPTED')
 require(p.get('spread')=='small' and p.get('question') and p.get('intent') and p.get('topic'),'PLAN_NOT_READY')
 require(set(p)=={'question','intent','topic','spread','variant','profile','roles','primary_reference','timeframe','context','acceptance'},'INVALID_PLAN_FIELDS')
 require(all(p['acceptance'].get(k) for k in ['question_ref','spread_ref']),'PLAN_NOT_READY')
 require(not p['acceptance'].get('rewritten') or p['acceptance'].get('rewrite_confirmed'),'REWRITE_NOT_CONFIRMED')
 require(set(o)<= {'count','focus_card','boundary','techniques','options','topics','entities','reveal','period_ref'},'UNKNOWN_CONTEXT')
 require('count' not in o or v.startswith('answer.'),'COUNT_NOT_CONFIGURABLE')
 if v.startswith('answer.'):
  require(o.get('count') in (5,7) and set(o.get('techniques',['storyline']))<=TECHNIQUES,'INVALID_LINE_PLAN')
  require(o.get('techniques',['storyline']) and (o['count']==5 or set(o.get('techniques',['storyline']))<={'storyline','group'}),'FIVE_TECHNIQUES_REQUIRE_FIVE')
  if v=='answer.focus':require(type(o.get('focus_card')) is int and 1<=o['focus_card']<=40 and o.get('boundary')=='first4-last_retry1-near_hold','BOUNDARY_PLAN_REQUIRED')
 if v=='box.center':require(type(o.get('focus_card')) is int and 1<=o['focus_card']<=40,'FOCUS_REQUIRED')
 if v.startswith('decision.'):
  require(len(o.get('options',[]))>=2 and len(set(o['options']))==len(o['options']),'OPTIONS_REQUIRED')
  if v=='decision.book':require(len(o['options'])==2,'BOOK_TWO_OPTIONS')
  require(3*len(o['options'])<=40,'TOO_MANY_OPTIONS')
 if v=='pyramid':require(len(o.get('topics',[]))==3 and len(set(o['topics']))==3 and p.get('timeframe'),'THREE_TOPICS_AND_TIME_REQUIRED')
 if v=='h.once':relationship_key(o.get('entities',[]))
 canonical(p);return digest(p)
class Stream:
 def __init__(self,seed):self.seed=seed;self.counter=0;self.trace=[]
 def pick(self,pool):
  i,self.counter=_uniform_index(self.seed,b'stage3',self.counter,len(pool));return pool.pop(i)
 def shuffle(self,pool):
  work=list(pool);out=[]
  while work:out.append(self.pick(work))
  self.trace.append({'op':'shuffle','size':len(pool),'counter_after':self.counter});return out
def layout(v,n,o):
 if v.startswith('box.'):return [(chr(65+i),i//3+1,i%3+1,'box') for i in range(9)]
 if v=='cross':return [('A',2,1,'cause'),('B',2,2,'focus'),('C',2,3,'outcome'),('D',1,2,'driver'),('E',3,2,'undercurrent')]
 if v=='h.once':return [('A1',1,1,'A'),('A2',2,1,'A'),('A3',3,1,'A'),('B1',1,3,'B'),('B2',2,3,'B'),('B3',3,3,'B'),('C',2,2,'bond')]
 if v=='pyramid':return [(f'T{i//3+1}.{i%3+1}',1 if i<3 else 2,(i+3) if i<3 else i-2 if i<6 else i-1,o['topics'][i//3]) for i in range(9)]
 if v.startswith('decision.'):return [(f'O{i//3+1}.{i%3+1}',i%3+1,i//3+1,o['options'][i//3]) for i in range(n)]
 return [(str(i+1),1,i+1,'line') for i in range(n)]
def deal(p,seed):
 v=p['variant'];o=p['context'];s=Stream(seed);pool=list(range(1,41));n=o.get('count',SPECS[v][1]);attempts=[];status='ready'
 if v.startswith('decision.'):n=len(o['options'])*3
 if v=='answer.focus':
  for attempt in range(2):
   full=s.shuffle(pool);i=full.index(o['focus_card']);attempts.append({'attempt':attempt,'full_order':full,'focus_index':i,'reason':'initial' if attempt==0 else 'verified_last_card_boundary'})
   h=n//2
   if i==0:order=full[:4];break
   if h<=i<40-h:order=full[i-h:i+h+1];break
   if i==39 and attempt==0:continue
   order=[];status='BoundaryHold';break
 elif v=='answer.random':
  order=[]
  for i in range(n):
   pool=s.shuffle(pool);order.append(pool.pop(0));s.trace.append({'op':'pick_top','draw_index':i+1,'remaining':len(pool)})
 elif v=='box.center':
  pool.remove(o['focus_card']);order=[s.pick(pool) for _ in range(8)];order.insert(4,o['focus_card'])
 else:order=[s.pick(pool) for _ in range(n)]
 return order,{'strategy':SPECS[v][2],'trace':s.trace,'attempts':attempts,'status':status}
def facts_for(p,order,request,origin='random'):
 positions=[{'position':i+1,'row':r,'column':c,'house':None,'card_id':cid,'slot_id':sid,'group':g} for i,(cid,(sid,r,c,g)) in enumerate(zip(order,layout(p['variant'],len(order),p['context'])))]
 f={'schema_version':2,'origin':origin,'draw_id':request,'plan_hash':digest(p),'deck_id':'rana40-v1','algorithm':SPECS[p['variant']][2],'order':order,'placements':positions};f['facts_hash']=digest(f);return f
def view(s,request):
 row=s.db.execute('SELECT body,inquiry FROM draws WHERE request=?',(request,)).fetchone();require(row and row[0],'DRAW_NOT_READY')
 data=json.loads(row[0]);
 if data.get('status')=='BoundaryHold':return data
 r=s.db.execute('SELECT revision,slots FROM reveal WHERE request=?',(request,)).fetchone();f=data['facts'];validate_facts(f)
 visible=json.loads(r[1]);public=dict(f);public['order']=[p['card_id'] for p in f['placements'] if p['position'] in visible];public['placements']=[p for p in f['placements'] if p['position'] in visible]
 result={'facts_hash':f['facts_hash'],'visible_facts':public,'reveal_state':{'revision':r[0],'visible_slots':visible},'status':'ready','relationship_scope':data.get('relationship_scope')}
 parent=s.db.execute('SELECT parent FROM draws WHERE request=?',(request,)).fetchone()[0]
 if parent:
  result['redraw'] = next(json.loads(e[0]) for e in s.db.execute("SELECT body FROM events WHERE kind='small_redraw'") if json.loads(e[0])['request']==request)
 return result
def configure(s,inquiry,p):
 h=validate_small(p);s.db.execute('BEGIN IMMEDIATE')
 try:
  if p['variant']=='h.once':
   key=relationship_key(p['context']['entities']);first=not s.db.execute('SELECT 1 FROM relations WHERE key=?',(key,)).fetchone()
   require(first or p['context'].get('period_ref'),'FOLLOWUP_PERIOD_REQUIRED')
  require(not s.db.execute('SELECT 1 FROM plans WHERE id=?',(inquiry,)).fetchone(),'PLAN_LOCKED')
  s.db.execute('INSERT INTO plans VALUES (?,?,?,0)',(inquiry,canonical(p).decode(),h));s.event('configured_small',{'inquiry':inquiry,'plan_hash':h});s.db.commit()
 except:s.db.rollback();raise
 return {'inquiry_id':inquiry,'plan_hash':h,'revision':0}
def new(s,inquiry,request,revision,reason=None,parent=None,**unknown):
 require(not unknown,'FORBIDDEN_DRAW_FIELDS');s.db.execute('BEGIN IMMEDIATE')
 try:
  pbody,ph,rev=s.db.execute('SELECT body,hash,revision FROM plans WHERE id=?',(inquiry,)).fetchone();p=json.loads(pbody);validate_small(p)
  old=s.db.execute('SELECT inquiry,seed,body FROM draws WHERE request=?',(request,)).fetchone()
  if parent or reason:
   require(parent and reason and reason.get('kind')=='explicit_user' and reason.get('message_ref') and s.db.execute('SELECT 1 FROM draws WHERE request=? AND body IS NOT NULL',(parent,)).fetchone(),'REDRAW_NOT_AUTHORIZED')
  if old:
   require(old[0]==inquiry,'REQUEST_CONFLICT')
   stored_parent=s.db.execute('SELECT parent FROM draws WHERE request=?',(request,)).fetchone()[0];require(stored_parent==parent,'REQUEST_CONFLICT')
   if parent:require(any(json.loads(e[0])=={'request':request,'parent':parent,'reason':reason} for e in s.db.execute("SELECT body FROM events WHERE kind='small_redraw'")),'REQUEST_CONFLICT')
   if old[2]:s.db.commit();return view(s,request)
   seed=bytes.fromhex(old[1])
  else:
   require(rev==revision,'STALE_REVISION');require(not s.db.execute('SELECT 1 FROM draws WHERE inquiry=?',(inquiry,)).fetchone(),'FIRST_DRAW_RETAINED')
   scope=None
   if p['variant']=='h.once':
    key=relationship_key(p['context']['entities']);first=not s.db.execute('SELECT 1 FROM relations WHERE key=?',(key,)).fetchone();require(first or p['context'].get('period_ref'),'FOLLOWUP_PERIOD_REQUIRED');scope='essence' if first else 'specified_period';s.db.execute('INSERT OR IGNORE INTO relations VALUES (?)',(key,));s.event('h_scope',{'request':request,'scope':scope})
   seed=secrets.token_bytes(32);s.db.execute('INSERT INTO draws VALUES (?,?,?,NULL,?,?)',(request,inquiry,seed.hex(),'small',parent));s.db.execute('UPDATE plans SET revision=revision+1 WHERE id=?',(inquiry,));s.event('seed_prepared',{'request':request,'commitment':digest(seed.hex())})
   if parent:s.event('small_redraw',{'request':request,'parent':parent,'reason':reason})
  s.db.commit()
 except:s.db.rollback();raise
 order,audit=deal(p,seed)
 data={'status':'BoundaryHold','reason':'unverified_near_edge_or_retry_limit'} if audit['status']=='BoundaryHold' else {'facts':facts_for(p,order,request)}
 if p['variant']=='h.once':
  events=s.db.execute("SELECT body FROM events WHERE kind='h_scope'").fetchall();data['relationship_scope']=next(json.loads(e[0])['scope'] for e in events if json.loads(e[0])['request']==request)
 s.db.execute('BEGIN IMMEDIATE')
 try:
  if s.db.execute('SELECT body FROM draws WHERE request=?',(request,)).fetchone()[0] is None:
   s.db.execute('UPDATE draws SET body=? WHERE request=?',(canonical(data).decode(),request));visible=[] if not order else [len(order)//2+1] if p['variant']=='answer.random' else list(range(1,len(order)+1));s.db.execute('INSERT INTO reveal VALUES (?,0,?)',(request,json.dumps(visible)));s.event('deal_audit',{'request':request,**audit})
  s.db.commit()
 except:s.db.rollback();raise
 return view(s,request)
def reveal(s,request,revision):
 s.db.execute('BEGIN IMMEDIATE')
 try:
  row=s.db.execute('SELECT body FROM draws WHERE request=?',(request,)).fetchone();require(row,'DRAW_NOT_READY');d=json.loads(row[0]);require('facts' in d,'BOUNDARY_HOLD')
  r=s.db.execute('SELECT revision,slots FROM reveal WHERE request=?',(request,)).fetchone();allslots=list(range(1,len(d['facts']['order'])+1))
  if json.loads(r[1])!=allslots:require(r[0]==revision,'STALE_REVISION');s.db.execute('UPDATE reveal SET revision=revision+1,slots=? WHERE request=?',(json.dumps(allslots),request));s.event('revealed',{'request':request})
  s.db.commit()
 except:s.db.rollback();raise
 return view(s,request)
def steps(p,f,technique=None):
 v=p['variant'];o=p['context'];n=len(f['order']);src=SPECS[v][0]
 if n==5 and v.startswith('answer.'):src+=';B55:181-195'
 def group(name,slots):return {'meaning':name,'positions':slots,'cards':[f['order'][i-1] for i in slots],'source':src}
 if v=='cross':groups=[('cause_driver',[1,4]),('cause_current',[1,5]),('development',[4,3]),('development',[5,3]),('focus',[4,2,5]),('summary',[1,2,3])]
 elif v.startswith('box.'):
  labels={'box.process':['stage1','stage2','stage3'],'box.yesno':['past_context','state','future_context']}.get(v,['past','present','future'])
  groups=list(zip(labels,[[1,4,7],[2,5,8],[3,6,9]]))+list(zip(['not_recommended' if v=='box.advice' else 'uncontrolled' if v!='box.random' and v!='box.center' else 'concern','situation','controlled' if v not in {'box.random','box.center'} else 'undercurrent'],[[1,2,3],[4,5,6],[7,8,9]]))
  if v=='box.yesno':groups=groups[3:] # Course yes/no prioritizes controllability; do not impose temporal columns.
  groups += [('indirect',[1,5,9]),('indirect',[3,5,7]),('direct',[2,5,8]),('direct',[4,5,6]),('diamond',[2,4,8,6])]
 elif v=='h.once':groups=[('bond',[7]),('detail_bond',[2,7,5]),('A',[1,2,3]),('B',[4,5,6])]
 elif v=='pyramid' or v.startswith('decision.'):
  labels=o.get('topics',o.get('options'));groups=[(label,list(range(i*3+1,i*3+4))) for i,label in enumerate(labels)]
  if v=='decision.book':groups=[('compare_polarity_before_interpretation',list(range(1,n+1)))]+groups
 elif v=='three':groups=[('theme',[2]),('sentence',[1,2,3]),('evolution',[3])]
 else:
  technique=technique or o.get('techniques',['storyline'])[0];require(technique in o.get('techniques',['storyline']),'TECHNIQUE_NOT_PLANNED')
  if v=='answer.focus' and n==4:
   require(technique=='storyline','FOUR_CARD_BOUNDARY_TECHNIQUE_UNVERIFIED')
   return [group('focus',[1]),group('development',[2,3,4]),group('storyline',[1,2,3,4])]
  if n==5 and technique=='pairs':groups=[('pairs',[i,i+1]) for i in range(1,5)]
  elif n==5 and technique=='lotus':groups=[('focus',[3]),('inner',[2,4]),('outer',[1,5])]
  elif n==5 and technique=='135-24':groups=[('main',[1,3,5]),('support',[2,4])]
  else:
   groups=[(technique,list(range(1,n+1)))]
   if v.startswith('answer.') and technique=='storyline':
    center=f['order'].index(o['focus_card'])+1 if v=='answer.focus' else n//2+1
    groups=[('focus_three',list(range(max(1,center-1),min(n,center+1)+1))),('leading',list(range(1,center))),('development',list(range(center+1,n+1)))]+groups
 return [group(label,slots) for label,slots in groups]
