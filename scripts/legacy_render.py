import runtime_config as rc
"""Arrange unchanged user color cards, or explicitly chosen EPUB art, in an SVG."""
import argparse
import base64
import hashlib
from html import escape
import json
import mimetypes
from pathlib import Path
import sys
import textwrap
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_card_images(cards, art_source):
    loaded = {}
    if art_source == 'user':
        config = rc.images(json.loads((ROOT/'references/card-images.json').read_text(encoding='utf-8')))
        if not config.get('render_ready') or config.get('missing_ids'):
            raise ValueError('User color card set is incomplete; show text and report missing assets')
        for cid in cards:
            entry = config['selected_assets'][cid]
            data = Path(entry['source']).read_bytes()
            if hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('User image changed; reverify card identity: '+cid)
            loaded[cid] = (entry['source'], data, mimetypes.guess_type(entry['source'])[0] or 'image/jpeg')
        return loaded
    if art_source != 'epub':
        raise ValueError('art source must be user or epub')
    sources = json.loads((ROOT/'references/sources.json').read_text(encoding='utf-8'))
    source = next(s for s in sources['local'] if s['id']=='essential-2')
    source = rc.book(source)
    path = Path(source['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
        raise ValueError('Source hash differs; reverify image locators')
    with zipfile.ZipFile(path) as z:
        for cid in cards:
            root = ET.fromstring(z.read(f'OEBPS/Section{int(cid)+11:04}.xhtml'))
            images = [e.attrib['src'] for e in root.iter() if e.tag.rsplit('}',1)[-1]=='img']
            if not images:
                raise ValueError('Card chapter lacks native image: '+cid)
            path = 'OEBPS/'+images[0]
            loaded[cid] = (path, z.read(path), mimetypes.guess_type(path)[0] or 'image/png')
    return loaded


def render(result, output, title=None, art_source='user'):
    if result['normalized']['profile'] != 'muree40':
        raise ValueError('This renderer uses only the user-selected 40-symbol deck')
    cards = {c['id']: c for c in result['cards']}
    positions = result['positions']
    if len(cards) != len(result['cards']) or len(positions) != len(cards):
        raise ValueError('Duplicate card identity or incompatible positions')
    if any(not str(i).isdigit() or not 1 <= int(i) <= 40 for i in cards):
        raise ValueError('Extra human cards are excluded')
    if any(p['layers'] != [p['active_card_id']] for p in positions):
        raise ValueError('Layered layouts are outside the selected 40-card image standard')
    if {p['active_card_id'] for p in positions} != set(cards):
        raise ValueError('Positions and drawn identities disagree')
    native_images=load_card_images(cards, art_source)
    cols=max(p['column'] for p in positions)
    rows=max(p['row'] for p in positions)
    card_w,card_h,gap,margin,heading,label=230,357,16,28,100,30
    cell_w,cell_h=card_w+gap,card_h+label+gap
    width=margin*2+cols*cell_w-gap
    text=title or 'Rana George 雷诺曼牌阵'
    art_label='用户提供彩色牌面' if art_source=='user' else '原书黑白牌面'
    subtitle=f'40种符号 · 无额外人物牌 · {art_label} · 按实际牌序排列'
    caption_lines=textwrap.wrap(subtitle,width=max(10,(width-margin*2)//15))
    heading=max(100,82+(len(caption_lines)-1)*18)
    height=heading+rows*cell_h+margin
    title_size=min(24,max(10,(width-margin*2)//max(len(text),1)))
    art=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<rect width="100%" height="100%" fill="#f5f1e9"/>',
         '<style>text{font-family:"Microsoft YaHei",sans-serif;fill:#302c28}</style>',
         f'<text x="{margin}" y="36" font-size="{title_size}">{escape(text)}</text>']
    art.extend(f'<text x="{margin}" y="{66+i*18}" font-size="15">{escape(line)}</text>' for i,line in enumerate(caption_lines))
    placement=[]
    if native_images:
        for p in positions:
            cid=p['active_card_id'];card=cards[cid]
            image_path,data,mime=native_images[cid]
            encoded=base64.b64encode(data).decode('ascii')
            x=margin+(p['column']-1)*cell_w
            y=heading+(p['row']-1)*cell_h
            art.append(f'<image id="card-{cid}" data-position="{p["position"]}" x="{x}" y="{y}" width="{card_w}" height="{card_h}" preserveAspectRatio="xMidYMid meet" href="data:{mime};base64,{encoded}"/>')
            art.append(f'<text x="{x+card_w/2}" y="{y+card_h+22}" text-anchor="middle" font-size="15">位置{p["position"]} · {card["number"]} {escape(card["zh"])}</text>')
            placement.append({'position':p['position'],'card_id':cid,'source_image':image_path,'source_image_sha256':hashlib.sha256(data).hexdigest()})
    art.append('</svg>')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('\n'.join(art)+'\n',encoding='utf-8')
    return {'image':str(output.resolve()),'format':'SVG','rows':rows,'columns':cols,
            'count':len(positions),'art':art_label,'art_source':art_source,
            'placements':placement,'reading_sha256':result['audit'].get('reading_sha256')}


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('reading',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--title')
    p.add_argument('--art',choices=('user','epub'),default='user',help='Default: verified user color images; epub is explicit only')
    args=p.parse_args()
    try:
        report=render(json.loads(args.reading.read_text(encoding='utf-8-sig')),args.output,args.title,args.art)
    except (ValueError,KeyError,OSError) as exc:
        p.exit(2,str(exc)+'\n')
    args.output.with_suffix('.manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='placements'},ensure_ascii=False))


if __name__=='__main__':main()
