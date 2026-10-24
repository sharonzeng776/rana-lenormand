"""Local resources are explicit data; this module never copies private content."""
import json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def config():
    name = os.environ.get('RANA_CONFIG')
    if not name:
        return {}
    path = Path(name)
    if not path.is_file():
        raise ValueError('CONFIG_MISSING: set RANA_CONFIG to an existing local JSON file')
    return json.loads(path.read_text(encoding='utf-8-sig'))

def book(default):
    return {**default, 'path': config().get('book_path', default['path'])}

def course_dir():
    name = config().get('course_dir')
    if not name:
        raise ValueError('COURSE_MISSING: configure course_dir in RANA_CONFIG (original HTML directory)')
    path = Path(name)
    if not path.is_dir() or not any(path.glob('*.html')):
        raise ValueError('COURSE_MISSING: configure course_dir in RANA_CONFIG (original HTML directory)')
    return path

def images(default):
    path = config().get('card_images_manifest')
    return json.loads(Path(path).read_text(encoding='utf-8-sig')) if path else default

def vault():
    name = config().get('vault_root')
    if not name:
        raise ValueError('VAULT_MISSING: configure vault_root in RANA_CONFIG before saving reports')
    return Path(name).resolve()

def font():
    return config().get('font_path', 'C:/Windows/Fonts/msyh.ttc')

def external(path, purpose):
    resolved = Path(path).resolve()
    if resolved.is_relative_to(ROOT):
        raise ValueError('RUNTIME_INSIDE_SKILL: '+purpose+' must be outside the skill directory')
    return resolved
