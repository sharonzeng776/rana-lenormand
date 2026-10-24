import sqlite3,json,secrets
from pathlib import Path
from core import *
from vendor.auditable_draw import _uniform_index

class Store:
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,timeout=30,isolation_level=None)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY, body TEXT, hash TEXT, revision INTEGER);
        CREATE TABLE IF NOT EXISTS draws(request TEXT PRIMARY KEY, inquiry TEXT, seed TEXT, body TEXT, kind TEXT, parent TEXT);
        CREATE TABLE IF NOT EXISTS reveal(request TEXT PRIMARY KEY, revision INTEGER, slots TEXT);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, kind TEXT, body TEXT);
        CREATE TABLE IF NOT EXISTS relations(key TEXT PRIMARY KEY);
        ''')
    def event(self,k,b):self.db.execute('INSERT INTO events(kind,body) VALUES (?,?)',(k,json.dumps(b,ensure_ascii=False)))
    def configure(self,inquiry,plan):
        h=validate_plan(plan)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            require(not self.db.execute('SELECT 1 FROM plans WHERE id=?',(inquiry,)).fetchone(),'PLAN_LOCKED')
            self.db.execute('INSERT INTO plans VALUES (?,?,?,0)',(inquiry,canonical(plan).decode(),h));self.event('configured',{'inquiry':inquiry,'plan_hash':h});self.db.commit()
        except: self.db.rollback();raise
        return {'inquiry_id':inquiry,'plan_hash':h,'revision':0}
    def new(self,inquiry,request,revision,reason=None,parent=None,**unknown):
        import capabilities
        require(capabilities.ready('gt40','flat'),'CAPABILITY_NOT_ACCEPTED')
        require(not unknown,'FORBIDDEN_DRAW_FIELDS')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old=self.db.execute('SELECT inquiry,seed,body FROM draws WHERE request=?',(request,)).fetchone()
            if old:
                require(old[0]==inquiry,'REQUEST_CONFLICT')
                if old[2]:self.db.commit();return self.replay(request)
                seed=bytes.fromhex(old[1])
            else:
                row=self.db.execute('SELECT body,hash,revision FROM plans WHERE id=?',(inquiry,)).fetchone();require(row,'PLAN_NOT_READY')
                require(row[2]==revision,'STALE_REVISION')
                exists=self.db.execute('SELECT request FROM draws WHERE inquiry=?',(inquiry,)).fetchone()
                if exists:require(reason and reason.get('kind')=='explicit_user' and reason.get('message_ref') and parent and self.db.execute('SELECT 1 FROM draws WHERE request=? AND inquiry=? AND body IS NOT NULL',(parent,inquiry)).fetchone(),'REDRAW_NOT_AUTHORIZED')
                else:require(not parent and not reason,'INVALID_PARENT')
                seed=secrets.token_bytes(32)
                self.db.execute('INSERT INTO draws VALUES (?,?,?,NULL,?,?)',(request,inquiry,seed.hex(),'redraw' if exists else 'main',parent))
                self.db.execute('UPDATE plans SET revision=revision+1 WHERE id=?',(inquiry,));self.event('seed_prepared',{'request':request,'parent':parent,'reason':reason,'commitment':digest(seed.hex())})
            self.db.commit()
        except:self.db.rollback();raise
        # Seed is committed before calculation. Recovery of same request never draws fresh entropy.
        remaining=list(range(1,41));order=[];counter=0
        while remaining:
            i,counter=_uniform_index(seed,b'item',counter,len(remaining));order.append(remaining.pop(i))
        p=self.db.execute('SELECT hash FROM plans WHERE id=?',(inquiry,)).fetchone()
        facts=build_facts(order,p[0],request,'random')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT body FROM draws WHERE request=?',(request,)).fetchone()
            if row[0] is None:
                self.db.execute('UPDATE draws SET body=? WHERE request=?',(canonical(facts).decode(),request));self.db.execute('INSERT INTO reveal VALUES (?,0,?)',(request,json.dumps(list(range(1,41)))));self.event('facts_committed',{'request':request,'facts_hash':facts['facts_hash']})
            self.db.commit()
        except:self.db.rollback();raise
        return self.replay(request)
    def replay(self,request):
        row=self.db.execute('SELECT body FROM draws WHERE request=?',(request,)).fetchone();require(row and row[0],'DRAW_NOT_READY')
        f=json.loads(row[0]);validate_facts(f)
        r=self.db.execute('SELECT revision,slots FROM reveal WHERE request=?',(request,)).fetchone()
        return {'facts':f,'reveal_state':{'revision':r[0],'visible_slots':json.loads(r[1])}}
    def import_order(self,inquiry,request,order,spread='gt40'):
        require(spread in {'gt40','nine','line'} and (spread!='line' or len(order) in {1,2,3,4,5,7}),'IMPORT_UNSUPPORTED')
        row=self.db.execute('SELECT hash FROM plans WHERE id=?',(inquiry,)).fetchone();require(row,'PLAN_NOT_READY')
        f=build_facts(order,row[0],request,'imported',spread)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            self.db.execute('INSERT INTO draws VALUES (?,?,NULL,?,?,NULL)',(request,inquiry,canonical(f).decode(),'imported'));self.db.execute('INSERT INTO reveal VALUES (?,0,?)',(request,json.dumps(list(range(1,len(order)+1)))));self.event('imported',{'request':request});self.db.commit()
        except:self.db.rollback();raise
        return self.replay(request)
    def mark_relationship(self,entities):
        key=relationship_key(entities);cur=self.db.execute('INSERT OR IGNORE INTO relations VALUES (?)',(key,));return {'key':key,'first':cur.rowcount==1}
