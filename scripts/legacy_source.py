import runtime_config as rc
"""Read bounded local book sections while retaining edition and physical locators."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def epub_units(path):
    with zipfile.ZipFile(path) as z:
        tree = ET.fromstring(z.read("META-INF/container.xml"))
        opf = next(e for e in tree.iter() if e.tag.endswith("rootfile")).attrib["full-path"]
        package = ET.fromstring(z.read(opf))
        prefix = Path(opf).parent.as_posix()
        items = {e.attrib["id"]: e.attrib for e in package.iter() if e.tag.endswith("}item")}
        spine = [e.attrib["idref"] for e in package.iter() if e.tag.endswith("}itemref")]
        for index, ref in enumerate(spine, 1):
            href = items[ref]["href"]
            full = prefix + "/" + href if prefix != "." else href
            body = ET.fromstring(z.read(full))
            parts = [" ".join("".join(e.itertext()).split()) for e in body.iter()
                     if e.tag.rsplit("}", 1)[-1] in {"h1", "h2", "h3", "h4", "p", "li"}]
            yield index, full, "\n".join(parts)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", default="essential-2")
    p.add_argument("--unit", type=int)
    p.add_argument("--card", type=int)
    p.add_argument("--page", type=int)
    p.add_argument("--find")
    p.add_argument("--section")
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int)
    p.add_argument("--max-chars", type=int, default=10000)
    p.add_argument("--image-dir", type=Path)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    if args.start < 1 or (args.end is not None and args.end < args.start):
        p.error("Paragraph range must be positive and ordered")
    sources = json.loads((ROOT / "references/sources.json").read_text(encoding="utf-8"))
    source = next((s for s in sources["local"] if s["id"] == args.source), None)
    if source is None:
        p.error("Unknown source ID")
    source = rc.book(source) if source["id"] == "essential-2" else source
    path = Path(source["path"])
    if not path.is_file():
        p.error("Original source unavailable: " + str(path))
    if args.verify:
        match = hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
        print(json.dumps({"source": source["id"], "sha256_matches": match}, ensure_ascii=False))
        return 0 if match else 1
    if args.card is not None:
        if source["id"] != "essential-2" or not 1 <= args.card <= 40:
            p.error("--card is a verified second-edition locator for cards 1..40")
        args.unit = args.card + 13
    if path.suffix.lower() == ".epub":
        if args.page or args.image_dir:
            p.error("EPUB has chapter locators, not verified printed page locators")
        units = list(epub_units(path))
        if args.unit:
            units = [u for u in units if u[0] == args.unit]
            if not units:
                p.error("EPUB unit outside file")
    else:
        try:
            from pypdf import PdfReader
        except ImportError:
            p.error("Use the existing workspace Python with pypdf; do not install or modify environments")
        if args.unit or args.card:
            p.error("Use --page for a PDF physical page")
        reader = PdfReader(path)
        if args.page and not 1 <= args.page <= len(reader.pages):
            p.error("PDF page outside file")
        if args.image_dir:
            if not args.page:
                p.error("Image extraction needs a single --page")
            args.image_dir.mkdir(parents=True, exist_ok=True)
            for i, image in enumerate(reader.pages[args.page - 1].images):
                out = args.image_dir / f"{source['id']}-p{args.page:04}-{i}{Path(image.name).suffix}"
                out.write_bytes(image.data)
                print(json.dumps({"image": str(out), "page_rotation": reader.pages[args.page - 1].rotation}))
            return 0
        indices = [args.page] if args.page else range(1, len(reader.pages) + 1)
        units = [(i, f"PDF-page-{i}", reader.pages[i - 1].extract_text() or "") for i in indices]
    if args.find:
        matches = []
        for n, locator, text in units:
            for line, paragraph in enumerate(text.splitlines(), 1):
                if args.find.casefold() in paragraph.casefold():
                    matches.append({"unit_or_page": n, "locator": locator,
                                    "paragraph": line, "preview": paragraph[:220]})
        print(json.dumps({"source": args.source, "total_matches": len(matches),
                          "matches": matches[:60]}, ensure_ascii=False, indent=2))
        return 0
    if len(units) != 1:
        p.error("Choose --unit/--card/--page, or search with --find")
    n, locator, text = units[0]
    lines = text.splitlines()
    if args.section:
        headings = {"Future", "Work", "Love", "Health, Body, and Spirit", "Health, Body,and Spirit", "Money",
                    "Time", "Timing", "Time or Timing", "Advice", "Advice or Action", "Objects and Areas", "Orientation",
                    "Nuance", "Nuances", "In the Grand Tableau", "Personal Story", "Attributes", "Contextual Meanings",
                    "When Using the Muree System", "Some Combinations and Examples"}
        aliases = {"time": "time or timing", "timing": "time or timing", "advice": "advice or action"}
        query = args.section.casefold()
        wanted = {query, aliases.get(query, query)}
        beginnings = [i for i, t in enumerate(lines) if t in headings and t.casefold() in wanted]
        if not beginnings:
            print(json.dumps({"source": args.source, "locator": locator, "section": args.section,
                              "status": "section_not_found"}, ensure_ascii=False))
            return 0
        start = beginnings[0]
        end = next((i for i in range(start + 1, len(lines)) if lines[i] in headings), len(lines))
        selected = list(enumerate(lines[start:end], start + 1))
    else:
        end = args.end or min(len(lines), args.start + 39)
        selected = list(enumerate(lines[args.start - 1:end], args.start))
    body = "\n".join(f"{i}: {line}" for i, line in selected)
    limit = min(max(args.max_chars, 100), 20000)
    print(json.dumps({"source": args.source, "unit_or_page": n, "locator": locator,
                      "status": "ok" if text.strip() else "scan_or_empty",
                      "truncated": len(body) > limit, "text": body[:limit]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
