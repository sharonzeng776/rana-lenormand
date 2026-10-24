import runtime_config as rc
import json
from pathlib import Path
from core import *
from session_store import Store
import stage4,stage4_view,small,evidence
def init(s):
 stage4.init(s);s.db.executescript('CREATE TABLE IF NOT EXISTS evidence_refs(id TEXT PRIMARY KEY,body TEXT);CREATE TABLE IF NOT EXISTS reports(id TEXT,revision INTEGER,body TEXT,PRIMARY KEY(id,revision));')
def state(s,request):
 init(s);f,kind=stage4.raw(s,request);rev,slots=s.db.execute('SELECT revision,slots FROM reveal WHERE request=?',(request,)).fetchone();visible=json.loads(slots);row=s.db.execute('SELECT plans.body FROM plans JOIN draws ON plans.id=draws.inquiry WHERE draws.request=?',(request,)).fetchone();p=json.loads(row[0]) if row else None
 public=stage4.public_view(s,request) if s.db.execute('SELECT 1 FROM jobs WHERE id=?',(request,)).fetchone() else {'commitment':digest({'draw':request,'reveal':rev,'visible':[(x['position'],x['card_id']) for x in f['placements'] if x['position'] in visible]})}
 return f,p,rev,visible,public['commitment']
def plan(s,request):
 f,p,rev,visible,commit=state(s,request);steps=[];by={x['card_id']:x['position'] for x in f['placements']}
 def add(key,positions,status='required',source='B55:832-851',reason=None,meaning=None):
  positions=list(dict.fromkeys(x for x in positions if x is not None and x in visible));steps.append({'id':key,'meaning':meaning or key,'status':status,'reason':reason,'facts':[{'position':i,'card_id':f['order'][i-1]} for i in positions],'source_locator':source})
 if p and p['spread']=='gt40':
  g=geometry(f,p['primary_reference']);a=p['primary_reference'];focus=g['focuses'][a]
  add('opening',[1,2,3]);add('primary_position',[by[a]]);add('primary_row_column_box',focus['row']+focus['column']+[x for row in focus['box'] for x in row]);add('primary_chain',[by[x['card_id']] for x in focus['chain']],source='B55:618-629')
  q=next(r['card_id'] for r in p['roles'] if r['entity_id']=='querent');add('querent_position_box',[by[q]]+g['focuses'][q]['row']+g['focuses'][q]['column']+[x for row in g['focuses'][q]['box'] for x in row],reason='querent position, house, entire row/column and box; one global primary time axis');add('center12',g['center']);add('negative3',[by[c] for c in [6,8,36]]+[x for c in [6,8,36] for row in g['focuses'][c]['box'] for x in row],source='B55:561-562');add('positive3',[by[c] for c in [33,31,2]]+[x for c in [33,31,2] for row in g['focuses'][c]['box'] for x in row],source='B55:561-562')
  themes=[40,15,34] if p['profile']=='career' else [24,5]+([25] if p['context'].get('married') else []) if p['profile']=='relationship' else [a]
  if p['profile']=='career':
   add('business_tree',[by[5]]+[x for row in g['focuses'][5]['box'] for x in row],'required' if p['context'].get('owns_business') else 'not_applicable',source='B55:1234',reason='ownership/stake condition')
   partner=p['context'].get('business_partner');partner_card=next((r['card_id'] for r in p['roles'] if r['entity_id']==partner),None)
   add('partner_connection',[by[q]]+([by[partner_card]] if partner_card else []),'required' if partner_card else 'not_applicable',source='B55:1228-1229',reason='only a preassigned business partner')
  if p['profile']=='relationship':
   add('bed',[by[39]]+[x for row in g['focuses'][39]['box'] for x in row],'required' if p['context'].get('intimacy_relevant') else 'not_applicable',source='B55:1081',reason='question relevance')
  for c in themes:add('theme_'+str(c),g['focuses'][c]['row']+g['focuses'][c]['column']+[x for row in g['focuses'][c]['box'] for x in row],source='B55:1220-1261' if p['profile']=='career' else 'B55:1060-1115')
  for key,positions in [('last_column',g['last_column']),('final_four',g['final_four']),('corners',g['corners'])]:add(key,positions)
  points=meeting(f,a,q);add('meeting_points',points.get('positions',[]),status='required' if points['status']=='applicable' else 'not_applicable',source='B55:660-673',reason='primary/querent relevant pair; direct alignment needs no rectangle');add('knights',[],status='optional',source='B55:558-560');axis=g['axis']
 elif p and p['spread']=='small':
  if len(visible)<len(f['order']):
   add('central_first',visible,source='B55:144-155',reason='read central card, then explicitly reveal the remainder')
  else:
   for i,group in enumerate(small.steps(p,f)):add('small_'+str(i),group['positions'],source=group['source'],meaning=group['meaning'])
  axis=None
 else:
  for i,group in enumerate(stage4_view.steps(s,request)['groups']):add('group_'+str(i),[x['position'] for x in group['cards']],source=group['source'],meaning=group['meaning'])
  axis=None
 add('direct_answer',visible,source='product_consultation_policy')
 return {'request':request,'reveal_revision':rev,'commitment':commit,'await_reveal':bool(p and p['spread']=='small' and len(visible)<len(f['order'])),'locked_plan':p,'timing':timing(p) if p and p['spread']=='gt40' else None,'question':p['question'] if p else '解释目标牌','roles':p.get('roles',[]) if p else [],'axis':axis,'steps':steps,'instruction':'Current model supplies contextual interpretation, material counterevidence, direct answer, bounded timing and recommendations; inspect calibration candidates separately, never silently merge conflicting timing. Structural checks do not prove meaning.'}
def bundle(s,cache,**kwargs):
 init(s);r=evidence.retrieve(cache,**kwargs);old=s.db.execute('SELECT body FROM evidence_refs WHERE id=?',(r['source_id'],)).fetchone();windows=json.loads(old[0]).get('_windows',[]) if old else [];windows.append([r['offset'],min(r['total_chars'],r['offset']+len(r['text_window']))]);windows.sort();end=0
 for a,b in windows:
  if a<=end:end=max(end,b)
 record={**r,'_cache':cache,'_windows':windows,'_complete':end>=r['total_chars']};s.db.execute('INSERT OR REPLACE INTO evidence_refs VALUES (?,?)',(r['source_id'],canonical(record).decode()));return r
def course_bundle(s,cache,query):
 init(s);r=evidence.course(cache,query)
 for match in r['matches']:
  sid='C:'+digest({'sha':match['sha'],'file':match['file'],'node':match['node']});match['source_id']=sid;s.db.execute('INSERT OR REPLACE INTO evidence_refs VALUES (?,?)',(sid,canonical({**match,'missing':[],'truncated':False,'_complete':True}).decode()))
 return r
def validate(s,request,document):
 require(set(document)<= {'revision','claims','completed_steps','answer','review'},'INVALID_READING_FIELDS')
 p=plan(s,request);require(not p['await_reveal'],'REVEAL_REQUIRED_FOR_FINAL_READING');require(document.get('revision')==p['reveal_revision'],'STALE_READING');required={x['id'] for x in p['steps'] if x['status']=='required'};completed=document.get('completed_steps',{});require(required<=set(completed),'MISSING_STEPS');require(all(isinstance(completed[k],str) and completed[k].strip() for k in required),'EMPTY_STEP')
 f,locked,_,visible,_=state(s,request);rolemap={r['card_id']:r['entity_id'] for r in (locked or {}).get('roles',[])}
 require(document.get('answer') and document.get('claims'),'ANSWER_AND_CLAIMS_REQUIRED')
 for c in document['claims']:
  require(set(c)<= {'id','statement','facts','sources','counterevidence','alternatives','kind','step_ids'},'INVALID_CLAIM_FIELDS');require(c.get('statement') and c.get('facts') and c.get('sources') and 'counterevidence' in c,'CLAIM_INCOMPLETE')
  for ref in c['facts']:
   require(set(ref)<={'position','card_id','house','role','zone'},'INVALID_FACT_REF');i=ref['position'];require(type(i) is int and type(ref['card_id']) is int and i in visible and f['order'][i-1]==ref['card_id'],'INVALID_OR_HIDDEN_FACT')
   if 'house' in ref:require(ref['house']==f['placements'][i-1]['house'],'WRONG_HOUSE')
   if 'role' in ref:require(rolemap.get(ref['card_id'])==ref['role'],'WRONG_ROLE')
   if 'zone' in ref:require(p['axis'] and i in p['axis'].get(ref['zone'],[]),'WRONG_TIME_AXIS')
  for source in c['sources']:
   r=s.db.execute('SELECT body FROM evidence_refs WHERE id=?',(source,)).fetchone();require(r,'INVALID_SOURCE');record=json.loads(r[0]);require(not record['missing'] and record.get('_complete',False),'SOURCE_INCOMPLETE')
   if record.get('source_hash'):require(evidence.index(record['_cache'])[1]['sha']==record['source_hash'],'SOURCE_CHANGED')
   elif record.get('file'):
    import hashlib
    require(hashlib.sha256((rc.course_dir()/record['file']).read_bytes()).hexdigest()==record['sha'],'COURSE_CHANGED')
 return {'structural_valid':True,'semantic_status':'requires_model_review','review_supplied':bool(document.get('review')),'request':request,'reveal_revision':p['reveal_revision'],'commitment':p['commitment']}
def save(s,request,document,path,markdown,index_path=None,test_fixture=False):
 validation=validate(s,request,document);require(document.get('review'),'SEMANTIC_REVIEW_REQUIRED');target=Path(path).resolve();require(target.suffix=='.md','MARKDOWN_REQUIRED')
 if test_fixture:require('samples' in target.parts,'FIXTURE_MUST_STAY_IN_SAMPLES')
 else:require(target.is_relative_to((rc.vault()/'03-案例研究')),'VAULT_CASE_DIRECTORY_REQUIRED')
 ip=None
 if index_path and not test_fixture:
  ip=Path(index_path).resolve();require(ip.is_relative_to(rc.vault()) and '.obsidian' not in ip.parts and ip.is_file() and ip!=target,'INVALID_INDEX')
 body={'path':str(target),'document':document,'markdown':markdown,'validation':validation}
 # Commit the immutable revision before writing. Identical retries repair pending
 # filesystem writes rather than inventing a new reading revision.
 s.db.execute('BEGIN IMMEDIATE')
 try:
  rows=s.db.execute('SELECT revision,body FROM reports WHERE id=? ORDER BY revision DESC LIMIT 1',(request,)).fetchone()
  if rows:require(json.loads(rows[1])['path']==str(target),'ONE_MAIN_REPORT')
  elif target.exists():raise Error('EXISTING_FILE_NOT_OWNED')
  revision=rows[0] if rows and json.loads(rows[1])==body else rows[0]+1 if rows else 1
  if not rows or revision!=rows[0]:s.db.execute('INSERT INTO reports VALUES (?,?,?)',(request,revision,canonical(body).decode()))
  s.db.commit()
 except:s.db.rollback();raise
 # A second transaction serializes publication with later revisions. If a newer
 # revision was committed meanwhile, never replace it with this older body.
 s.db.execute('BEGIN IMMEDIATE')
 try:
  latest=s.db.execute('SELECT revision,body FROM reports WHERE id=? ORDER BY revision DESC LIMIT 1',(request,)).fetchone();published=json.loads(latest[1]);target.parent.mkdir(parents=True,exist_ok=True)
  tmp=target.with_name(target.name+'.rana.tmp');tmp.write_text(published['markdown']+f'\n\n<!-- reading revision {latest[0]}; {published["validation"]["commitment"]} -->\n',encoding='utf-8');tmp.replace(target)
  if ip:
   text=ip.read_text(encoding='utf-8');link='- [['+target.stem+']]'
   if link not in text:
    itmp=ip.with_name(ip.name+'.rana.tmp');itmp.write_text(text+'\n'+link+'\n',encoding='utf-8');itmp.replace(ip)
  s.db.commit()
 except:s.db.rollback();raise
 return {'path':str(target),'revision':revision,'validation':validation}
