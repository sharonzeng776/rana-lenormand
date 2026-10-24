import runtime_config as rc
import argparse,json,sys
from pathlib import Path
from core import *
from session_store import Store
from sources import context
from render import render
def legacy_run(a,db):
    op=a.pop('op')
    if op=='review':return review_question(**a)
    if op=='catalog':return json.loads((Path(__file__).resolve().parents[1]/'references/catalog.json').read_text(encoding='utf-8'))
    if op=='recommend':
        review=review_question(**a)
        if review['status']!='recommend':return review
        return {'preferred':{'spread':'gt40','variant':'flat','profile':'career' if a['topic']=='career' else 'relationship' if a['topic']=='relationship' else 'general','count':40,'reason':'完整状态与影响因素；由用户选择后才能抽牌'},'alternatives':[{'spread':'box.random','count':9,'availability':'disabled_future_stage','reason':'较短的状态概览；当前仅可说明方法，不能新抽'}],'question':review['effective_question']}
    if op=='source':return context(**a)
    if op=='capability':
        if a.get('branch') in {'near_edge','mirror','facing'}:return {'status':'hold','code':'RULE_UNVERIFIED'}
        import capabilities
        return {'status':'ready' if (a.get('spread'),a.get('variant'),a.get('branch','standard'))==('gt40','flat','standard') and capabilities.ready('gt40','flat') else 'hold'}
    s=Store(db)
    try:
        if op=='configure':return s.configure(**a)
        if op=='new':return s.new(**a)
        if op=='replay':return s.replay(**a)
        if op=='import':return s.import_order(**a)
        if op=='relationship':return s.mark_relationship(**a)
        if op in {'geometry','render','steps'}:
            request=a.pop('request');view=s.replay(request)
            inquiry=s.db.execute('SELECT inquiry FROM draws WHERE request=?',(request,)).fetchone()[0]
            plan=json.loads(s.db.execute('SELECT body FROM plans WHERE id=?',(inquiry,)).fetchone()[0])
            if op=='geometry':return {'geometry':geometry(view['facts'],plan['primary_reference']),'timing':timing(plan)}
            if op=='steps':return reading_steps(plan)
            return render(view['facts'],view['reveal_state'],**a)
        raise Error('CAPABILITY_DISABLED')
    finally:s.db.close()
def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--db',type=Path,required=True);p.add_argument('--output',type=Path);args=p.parse_args()
    try:r=run(json.loads(args.input.read_text(encoding='utf-8-sig')),args.db)
    except (Error,KeyError,TypeError,ValueError,OSError) as e:print(json.dumps({'error':str(e)},ensure_ascii=False));return 2
    text=json.dumps(r,ensure_ascii=False,indent=2)
    if args.output:args.output.write_text(text,encoding='utf-8')
    else:print(text)
    return 0
def stage3_run(a,db):
    import small
    import capabilities
    from small_render import output
    op=a.get('op')
    if op=='ready':return [{'spread':'small','variant':v,'source':spec[0],'algorithm':spec[2],'availability':'ready'} for v,spec in small.SPECS.items() if capabilities.ready('small',v,spec[0],spec[2])]+([{'spread':'gt40','variant':'flat','availability':'ready'}] if capabilities.ready('gt40','flat') else [])
    if op=='recommend':
        q=review_question(a['question'],a['intent'],a['topic'],a.get('options'))
        if q['status']!='recommend':return q
        v='decision.book' if a['intent']=='comparison' and len(a.get('options',[]))==2 else 'decision.descriptive' if a['intent']=='comparison' else 'box.advice' if a['intent']=='advice' else 'box.state' if a['intent']=='state' else 'box.process' if a['intent'] in {'process','process_and_outcome'} else 'answer.random'
        names=list(dict.fromkeys([v,'box.random','answer.random']))
        choices=[{'spread':'small','variant':x,'availability':'ready','count':3*len(a.get('options',[])) if x.startswith('decision.') else small.SPECS[x][1],'reason':{'answer.random':'聚焦结果与发展；先读中央再揭示全线','box.process':'三阶段过程及各阶段影响因素','box.advice':'区分不建议投入、当前状态及可控行动','box.state':'当前状态与影响因素','decision.book':'分别比较两个选项的三牌组合','decision.descriptive':'按选项分组描述，关闭数值评分'}.get(x,'较完整的九宫状态与组合概览')} for x in names if capabilities.ready('small',x,small.SPECS[x][0],small.SPECS[x][2])]
        return {'question':a['question'],'preferred':choices[0],'alternatives':choices[1:2]} if choices else {'status':'hold','code':'NO_ACCEPTED_VARIANT'}
    if op=='capability' and a.get('spread')=='small':return {'status':'ready' if a.get('variant') in small.SPECS and capabilities.ready('small',a['variant']) and a.get('branch','standard') in ({'standard','interior','first4','last_retry1'} if a.get('variant')=='answer.focus' else {'standard'}) else 'hold'}
    if op=='configure' and a.get('plan',{}).get('spread')=='small':
        s=Store(db)
        try:return small.configure(s,a['inquiry'],a['plan'])
        finally:s.db.close()
    if op in {'new','replay','reveal','steps','render','trace','import'}:
        s=Store(db)
        try:
            row=s.db.execute('SELECT body FROM plans WHERE id=?',(a.get('inquiry'),)).fetchone() if op in {'new','import'} else s.db.execute('SELECT plans.body FROM plans JOIN draws ON plans.id=draws.inquiry WHERE draws.request=?',(a.get('request'),)).fetchone()
            if row and json.loads(row[0]).get('spread')=='small':
                p=json.loads(row[0]);kw={k:v for k,v in a.items() if k!='op'}
                if op=='import':raise Error('SMALL_IMPORT_UNSUPPORTED: use new; legacy import is GT/nine/line only')
                if op=='new':return small.new(s,**kw)
                if op=='replay':return small.view(s,a['request'])
                if op=='reveal':return small.reveal(s,**kw)
                if op=='trace':return [json.loads(r[0]) for r in s.db.execute("SELECT body FROM events WHERE kind='deal_audit'") if json.loads(r[0])['request']==a['request']]
                data=json.loads(s.db.execute('SELECT body FROM draws WHERE request=?',(a['request'],)).fetchone()[0]);require('facts' in data,'BOUNDARY_HOLD');f=data['facts'];r=small.view(s,a['request'])['reveal_state']
                if op=='render':return output(f,r,a['output'])
                require(len(r['visible_slots'])==len(f['order']),'REVEAL_REQUIRED');return small.steps(p,f,a.get('technique'))
        finally:s.db.close()
    return legacy_run(a,db)
def stage4_run(a,db):
    import stage4 as m
    import capabilities
    import stage4_view as v
    op=a.get('op');kw={k:x for k,x in a.items() if k!='op'}
    if op=='ready':return stage3_run(a,db)+[{'spread':'series','variant':name,'source':src,'availability':'ready'} for name,src in m.SERIES.items() if capabilities.ready('series',name,src,m.ALGORITHM)]
    if op=='capability' and a.get('spread')=='series':return {'status':'ready' if a.get('variant') in m.SERIES and capabilities.ready('series',a['variant']) and a.get('branch','standard')=='standard' else 'hold'}
    if op=='configure' and a.get('plan',{}).get('spread')=='series':
        s=Store(db)
        try:return m.configure(s,**kw)
        finally:s.db.close()
    if op in {'clarifier.prepare','clarifier.draw','reserve.allocate','reading.complete','audit.export','new','replay','steps','render','trace','reveal','import','geometry'}:
        s=Store(db);m.init(s)
        try:
            if op=='clarifier.prepare':return m.prepare(s,**kw)
            if op=='clarifier.draw':return m.draw_clarifier(s,**kw)
            if op=='reserve.allocate':return m.allocate(s,**kw)
            if op=='reading.complete':return m.acknowledge(s,**kw)
            isjob=s.db.execute('SELECT 1 FROM jobs WHERE id=?',(a.get('request'),)).fetchone()
            if op=='audit.export':return m.audit(s,**kw)
            row=s.db.execute('SELECT body FROM plans WHERE id=?',(a.get('inquiry'),)).fetchone()
            series=row and json.loads(row[0]).get('spread')=='series'
            if op=='import' and series:raise Error('SERIES_IMPORT_DISABLED')
            if op=='new' and series:return m.new(s,**kw)
            if isjob:
                if op=='replay':return m.public_view(s,a['request'])
                if op=='render':return v.render(s,**kw)
                if op=='steps':return v.steps(s,**kw)
                if op in {'trace','reveal'}:raise Error('USE_ALLOCATION_OR_EXPLICIT_AUDIT')
                raise Error('CAPABILITY_DISABLED')
        finally:s.db.close()
    return stage3_run(a,db)
def run(a,db):
    rc.external(db,'database')
    for field in ('cache','output'):
        if field in a:rc.external(a[field],field)
    op=a.get('op');kw={k:v for k,v in a.items() if k!='op'}
    if op in {'reading.plan','reading.validate','reading.save','source.bundle','source.index','course.search','render.all'}:
        import reading,evidence,visual
        s=Store(db)
        try:
            reading.init(s)
            if op=='reading.plan':return reading.plan(s,**kw)
            if op=='reading.validate':return reading.validate(s,**kw)
            if op=='reading.save':return reading.save(s,**kw)
            if op=='source.bundle':return reading.bundle(s,**kw)
            if op=='source.index':return evidence.index(**kw)[1]
            if op=='course.search':return reading.course_bundle(s,**kw)
            return visual.render(s,**kw)
        finally:s.db.close()
    return stage4_run(a,db)
if __name__=='__main__':sys.exit(main())
