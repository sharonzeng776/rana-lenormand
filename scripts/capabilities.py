"""Reviewed release allowlist, not an automatic proof of implementation quality."""
import json
from pathlib import Path

def manifest():
    return json.loads((Path(__file__).resolve().parents[1]/'references/capabilities.json').read_text(encoding='utf-8'))

def ready(spread,variant,source=None,algorithm=None):
    entry=next((x for x in manifest() if (x['spread'],x['variant'])==(spread,variant)),None)
    return bool(entry and all(entry.get('components',{}).get(k) is True for k in ['deal','layout','read','render','tests']) and (source is None or entry['source']==source) and (algorithm is None or entry['algorithm']==algorithm))
