"""Rewrite each scouting page's `scout:` header from scouting-reports.xlsx.

Usage: python3 scripts/sync_scouting.py path/to/scouting-reports.xlsx [slug ...]

The sheet is the source of truth for report content. This script replaces only the
`scout:` block in scouting/<slug>/index.qmd and leaves everything else on the page
(title, subtitle, PDF link, form image) alone. Players marked Publish = N, or with no
page folder yet, are skipped and listed.
"""
import json
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent


def rows(ws):
    data = list(ws.iter_rows(values_only=True))
    head = [str(h).strip() if h else "" for h in data[0]]
    for r in data[1:]:
        rec = {h: ("" if v is None else str(v).strip()) for h, v in zip(head, r)}
        if rec.get("slug"):
            yield rec


def q(s):
    # json strings are valid YAML double-quoted strings, so quotes and inches are safe
    return json.dumps(s, ensure_ascii=False)


def split(s):
    return [p.strip() for p in re.split(r"[;\n]", s) if p.strip()]


def tag_list(s):
    return "[" + ", ".join(q(t) for t in split(s)) + "]"


def spin(s):
    # keep raw TrackMan numbers numeric so the shortcode can round them
    return s if re.fullmatch(r"\d+(\.\d+)?", s) else q(s)


def scout_block(p, grades, traits, data):
    out = ["scout:"]
    out.append(f"  role: {q(p['Role'])}")
    for key, col in [("bt", "B/T"), ("size", "Ht/Wt"), ("commit", "Commit"), ("team", "Travel team"),
                     ("ofp", "OFP"), ("follow", "Follow"), ("summary", "Summary"),
                     ("pbr_url", "PBR blog URL"), ("video", "Video file"), ("video_caption", "Video caption")]:
        out.append(f"  {key}: {q(p.get(col, ''))}")
    looks = split(p.get("Looks", ""))
    if looks:
        out.append("  looks:")
        out += [f"    - {q(l)}" for l in looks]
    if grades:
        out.append("  tools:")
        for g in grades:
            out.append(f"    - name: {q(g['Pitch / Tool'])}")
            out.append(f"      grade: {q(g['Grade'])}")
            for key, col in [("velo", "Velo"), ("shape", "Shape")]:
                if g.get(col):
                    out.append(f"      {key}: {q(g[col])}")
            if g.get("Spin"):
                out.append(f"      spin: {spin(g['Spin'])}")
            out.append(f"      tags: {tag_list(g.get('Form adjectives', ''))}")
            out.append(f"      notes: {q(g.get('Sentences', ''))}")
    if data:
        out.append("  data:")
        for d in data:
            out.append(f"    - measure: {q(d['Measure'])}")
            out.append(f"      value: {q(d['Value'])}")
            out.append(f"      source: {q(d['Source'])}")
    if traits:
        out.append("  traits:")
        for t in traits:
            out.append(f"    - name: {q(t['Group'])}")
            out.append(f"      tags: {tag_list(t.get('Form adjectives', ''))}")
            out.append(f"      notes: {q(t.get('Sentences', ''))}")
    return "\n".join(out) + "\n"


def replace_block(text, block):
    head_end = text.index("\n---", 3)
    header, body = text[:head_end + 1], text[head_end + 1:]
    # drop the old scout block and any comment lines that sat above it
    header = re.sub(r"\n(#[^\n]*\n|\s*\n)*scout:\n(?:[ #][^\n]*\n|\s*\n)*", "\n", header)
    return header.rstrip("\n") + "\n\n" + block + body


def one_screen(text, folder):
    """Full-width layout, and a body that is only the shortcode (form PDF and image ride in it)."""
    head_end = text.index("\n---", 3) + 4
    header, body = text[:head_end], text[head_end:]
    if "page-layout:" not in header:
        header = re.sub(r"(categories: \[[^\]]*\]\n)", r"\1page-layout: full\n", header, count=1)
    if "scout-report" not in body:
        pdfs = sorted(p.name for p in folder.glob("*.pdf"))
        args = f' pdf="{pdfs[0]}"' if pdfs else ""
        if (folder / "report.jpg").exists():
            args += ' image="report.jpg"'
        body = "\n\n{{< scout-report" + args + " >}}\n"
    return header + body


def main():
    wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
    only = set(sys.argv[2:])
    grades, traits, data = {}, {}, {}
    for src, dest in [("Grades", grades), ("Traits", traits), ("Data", data)]:
        for r in rows(wb[src]):
            dest.setdefault(r["slug"], []).append(r)
    for p in rows(wb["Players"]):
        slug = p["slug"]
        if only and slug not in only:
            continue
        page = ROOT / "scouting" / slug / "index.qmd"
        if p.get("Publish", "").upper() != "Y":
            print(f"skip {slug}: Publish is not Y")
            continue
        if not page.exists():
            print(f"skip {slug}: no page folder yet (needs PDF, report.jpg, thumb.jpg)")
            continue
        block = scout_block(p, grades.get(slug, []), traits.get(slug, []), data.get(slug, []))
        page.write_text(one_screen(replace_block(page.read_text(), block), page.parent))
        print(f"synced {slug}")


if __name__ == "__main__":
    main()
