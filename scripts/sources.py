import runtime_config as rc
from pathlib import Path
import json,hashlib
from core import require
from legacy_source import epub_units
ROOT=Path(__file__).resolve().parents[1]
HEADS={'Future','Work','Love','Health, Body, and Spirit','Money','Time','Timing','Time or Timing','Advice','Advice or Action','Objects and Areas','Orientation','Nuance','Nuances','In the Grand Tableau','Personal Story','Contextual Meanings','When Using the Muree System','Some Combinations and Examples'}
def context(card,topic,cache):
    require(type(card) is int and 1<=card<=40,'INVALID_CARD')
    src=next(s for s in json.loads((ROOT/'references/sources.json').read_text(encoding='utf-8'))['local'] if s['id']=='essential-2')
    src=rc.book(src);path=Path(src['path']);require(path.is_file(),'SOURCE_MISSING')
    sha=hashlib.sha256(path.read_bytes()).hexdigest();require(sha==src['sha256'],'SOURCE_CHANGED')
    dest=Path(cache)/sha;dest.mkdir(parents=True,exist_ok=True);file=dest/'extract-v1.json'
    if not file.exists():
        data={str(n):{'href':h,'paragraphs':t.splitlines()} for n,h,t in epub_units(path)}
        tmp=file.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8');tmp.replace(file)
    unit=json.loads(file.read_text(encoding='utf-8'))[str(card+13)];lines=unit['paragraphs'];sections=[]
    for title in [topic,'When Using the Muree System']:
        hits=[i for i,t in enumerate(lines) if t==title]
        for i in hits:
            end=next((j for j in range(i+1,len(lines)) if lines[j] in HEADS),len(lines))
            sections.append({'title':title,'start':i+1,'end':end,'text':'\n'.join(lines[i:end])})
    require(any(s['title']==topic for s in sections),'SECTION_MISSING')
    return {'card_id':card,'source_hash':sha,'href':unit['href'],'sections':sections,'truncated':False,'profile':'muree40','notice':'Apply Muree overrides; traditional topic entries alone are insufficient.'}
