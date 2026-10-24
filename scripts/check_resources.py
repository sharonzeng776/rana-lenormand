"""Read-only local installation preflight; no private content is bundled or printed."""
import sys,json,hashlib,importlib.util
from pathlib import Path
import runtime_config as rc

def check():
    issues=[];checks={}
    try:
        rc.config()
    except (OSError,ValueError) as e:
        return {'ready_for_local_full_output':False,'checks':checks,'issues':[str(e)],'python':sys.version.split()[0],'scope':'local filesystem workflow; not a hostile local-user sandbox'}
    try:
        source=rc.book(next(x for x in json.loads((rc.ROOT/'references/sources.json').read_text(encoding='utf-8'))['local'] if x['id']=='essential-2'))
        p=Path(source['path']);checks['book_sha_matches']=p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256']
        if not checks['book_sha_matches']:issues.append('BOOK_MISSING_OR_CHANGED: configure book_path; only the verified second edition is accepted')
    except (OSError,ValueError) as e:issues.append(str(e))
    try:checks['course_files']=len(list(rc.course_dir().glob('*.html')))
    except (OSError,ValueError) as e:issues.append(str(e))
    try:
        images=rc.images(json.loads((rc.ROOT/'references/card-images.json').read_text(encoding='utf-8')))
        bad=[]
        for i in range(1,41):
            entry=images['selected_assets'][str(i)];p=Path(entry['source'])
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:bad.append(i)
        checks['color_images_verified']=40-len(bad)
        if bad:issues.append('CARD_IMAGE_MISSING_OR_CHANGED: '+','.join(map(str,bad))+'; fix card_images_manifest, never redraw')
    except (OSError,ValueError,KeyError) as e:issues.append('CARD_MANIFEST: '+str(e))
    checks['font_exists']=Path(rc.font()).is_file()
    if not checks['font_exists']:issues.append('FONT_MISSING: configure font_path for PNG; text/SVG remain usable')
    checks['pillow_available']=importlib.util.find_spec('PIL') is not None
    if not checks['pillow_available']:issues.append('PILLOW_MISSING: use an existing Python with Pillow for PNG; no environment changed')
    return {'ready_for_local_full_output':not issues,'checks':checks,'issues':issues,'python':sys.version.split()[0],'scope':'local filesystem workflow; not a hostile local-user sandbox'}

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    result=check();print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['ready_for_local_full_output'] else 2)
