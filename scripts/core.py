import hashlib,json,math

def canonical(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(x): return hashlib.sha256(canonical(x)).hexdigest()
class Error(ValueError): pass
def require(ok,code):
    if not ok: raise Error(code)
def geometry(facts,anchor):
    validate_facts(facts)
    ps=facts['placements']; by={p['card_id']:p for p in ps}; coords={(p['row'],p['column']):p['position'] for p in ps}
    require(len(ps)==40 and anchor in by,'INVALID_GEOMETRY')
    c=by[anchor]['column']; focuses={}
    for cid,p in by.items():
        r,k=p['row'],p['column']; chain=[]; seen=set(); cur=cid
        while cur not in seen:
            seen.add(cur); h=by[cur]['house'];chain.append({'card_id':cur,'house':h,'next_card_id':h});cur=h
        focuses[cid]={'position':p['position'],'house':p['house'],
          'box':[[coords.get((r+dr,k+dc)) for dc in (-1,0,1)] for dr in (-1,0,1)],
          'row':[q['position'] for q in ps if q['row']==r],
          'column':[q['position'] for q in ps if q['column']==k],
          'above_band':[q['position'] for q in ps if q['row']<r],
          'below_band':[q['position'] for q in ps if q['row']>r],
          'knights':sorted(q['position'] for q in ps if (abs(q['row']-r),abs(q['column']-k)) in {(1,2),(2,1)}),
          'chain':chain,'stop':{'reason':'cycle','card_id':cur}}
    return {'axis':{label:[p['position'] for p in ps if cond(p['column'])] for label,cond in [('past',lambda x:x<c),('present',lambda x:x==c),('future',lambda x:x>c)]},
      'focuses':focuses,'center':[11,12,13,14,19,20,21,22,27,28,29,30],
      'corners':[1,8,40,33],'last_column':[8,16,24,32,40],'final_four':[37,38,39,40]}
def meeting(facts,a,b):
    validate_facts(facts); by={p['card_id']:p for p in facts['placements']};x,y=by[a],by[b]
    if x['row']==y['row'] or x['column']==y['column']:return {'status':'not_applicable','reason':'direct_alignment'}
    return {'status':'applicable','positions':[(x['row']-1)*8+y['column'],(y['row']-1)*8+x['column']]}
def build_facts(order,plan_hash,draw_id,origin='test_fixture',spread='gt40'):
    require(all(type(i) is int and 1<=i<=40 for i in order) and len(set(order))==len(order),'INVALID_DECK')
    require(len(order)==({'gt40':40,'nine':9}.get(spread,len(order))),'INVALID_COUNT')
    cols=8 if spread=='gt40' else 3 if spread=='nine' else len(order)
    f={'schema_version':2,'origin':origin,'draw_id':draw_id,'plan_hash':plan_hash,'deck_id':'rana40-v1',
       'algorithm':'sha256-counter-rejection-pop-v1' if origin=='random' else 'import-order-v1',
       'order':order,'placements':[{'position':i+1,'row':i//cols+1,'column':i%cols+1,'house':i+1 if spread=='gt40' else None,'card_id':cid} for i,cid in enumerate(order)]}
    f['facts_hash']=digest(f);return f
def validate_facts(f):
    require(f['facts_hash']==digest({k:v for k,v in f.items() if k!='facts_hash'}),'FACTS_CHANGED')
    ps=f['placements'];require(len(ps)==len(f['order']) and [p['card_id'] for p in ps]==f['order'],'INVALID_GEOMETRY')
    require(len(set(f['order']))==len(ps) and all(type(x) is int and 1<=x<=40 for x in f['order']),'INVALID_DECK')
    require(len({(p['row'],p['column']) for p in ps})==len(ps),'INVALID_GEOMETRY')
    require([p['position'] for p in ps]==list(range(1,len(ps)+1)),'INVALID_GEOMETRY')
    if len(ps)==40 and f.get('algorithm')=='stage4-shuffle-pop-v1':
        require(all(p['row']==1 and p['column']==i+1 and p['house'] is None for i,p in enumerate(ps)),'INVALID_GEOMETRY')
    elif len(ps)==40:
        require(all(p['row']==i//8+1 and p['column']==i%8+1 and p['house']==i+1 for i,p in enumerate(ps)),'INVALID_GEOMETRY')
def relationship_key(entities):
    require(len(entities)==2 and len(set(entities))==2,'INVALID_RELATIONSHIP')
    return digest(sorted(entities))
def review_question(question,intent,topic,options=None):
    missing=[]
    if not isinstance(question,str) or not question.strip():missing.append('question')
    if intent not in {'outcome','yesno','process','process_and_outcome','state','advice','comparison','general_overview'}:missing.append('intent')
    if not topic:missing.append('topic')
    if intent=='comparison' and (not options or len(options)<2):missing.append('options')
    return {'status':'clarify' if missing else 'recommend','missing':missing,'effective_question':question}
def validate_plan(p):
    import capabilities
    require(capabilities.ready('gt40','flat'),'CAPABILITY_NOT_ACCEPTED')
    fields={'question','intent','topic','spread','variant','profile','roles','primary_reference','timeframe','context','acceptance'}
    require(set(p)==fields,'INVALID_PLAN_FIELDS')
    require(review_question(p['question'],p['intent'],p['topic'])['status']=='recommend','PLAN_NOT_READY')
    require(p['spread']=='gt40' and p['variant']=='flat' and p['profile'] in {'general','career','relationship'},'CAPABILITY_DISABLED')
    require(type(p['primary_reference']) is int and 1<=p['primary_reference']<=40,'INVALID_ANCHOR')
    require(p['acceptance'].get('question_ref') and p['acceptance'].get('spread_ref') and p['acceptance'].get('anchor_ref'),'PLAN_NOT_READY')
    require(p['acceptance'].get('rewrite_confirmed') if p['acceptance'].get('rewritten') else True,'REWRITE_NOT_CONFIRMED')
    require(isinstance(p['roles'],list) and any(r.get('entity_id')=='querent' for r in p['roles']),'PLAN_NOT_READY')
    require(all(type(r.get('card_id')) is int and 1<=r['card_id']<=40 and r.get('entity_id') for r in p['roles']),'INVALID_ROLES')
    require(len({r['card_id'] for r in p['roles']})==len(p['roles']) and len({r['entity_id'] for r in p['roles']})==len(p['roles']),'INVALID_ROLES')
    require(p['context'].get('final_four_intent') in {'advice','conclusion'},'PLAN_NOT_READY')
    t=p['timeframe'];require(t.get('unit') in {'month','week','day'} and type(t.get('value')) in {int,float} and math.isfinite(t['value']) and t['value']>0 and t.get('declared_ref'),'PLAN_NOT_READY')
    return digest(p)
def timing(p):
    t=p['timeframe'];v=t['value'];u=t['unit']
    if u=='month' and v==6:r={'range':[1,1.5],'unit':'month','source':'user_course_supplement'}
    elif u=='month' and v==3:r={'range':[2,3],'unit':'week','source':'user_course_supplement'}
    else:r={'range':[v/6,v/4],'unit':u,'source':'design_inference'}
    return {'horizon':t,'per_column':r,'approximate':True,'exact_dates':None,'calibration':p['context'].get('calibration',[])}
def reading_steps(p):
    steps=['opening','primary_position','primary_row_column_box','querent_position_box','primary_chain','center12','topics','negative3','positive3','last_column','final_four','corners','direct_answer']
    result=[{'step':s,'status':'required'} for s in steps]
    if p['profile']=='career':
        result += [{'step':s,'status':'required'} for s in ['market','bear','fish']]
        result.append({'step':'business_tree','status':'required' if p['context'].get('owns_business') else 'not_applicable','reason':'ownership_condition'})
        result.append({'step':'partner_connection','status':'required' if p['context'].get('business_partner') else 'not_applicable','reason':'partner_condition'})
    if p['profile']=='relationship':
        result += [{'step':s,'status':'required'} for s in ['heart','relationship_tree','charged_boxes']]
        result.append({'step':'marriage_ring','status':'required' if p['context'].get('married') else 'not_applicable','reason':'marriage_condition'})
        result.append({'step':'bed','status':'required' if p['context'].get('intimacy_relevant') else 'not_applicable','reason':'question_relevance'})
    result += [{'step':'meeting_points','status':'conditional','reason':'relevant_focus_and_distinct_rows_columns'}, {'step':'knights','status':'optional','reason':'specific_ambiguity'}, {'step':'mirror','status':'disabled','reason':'rule_unverified'}, {'step':'facing','status':'disabled','reason':'asset_direction_unverified'}]
    return result
