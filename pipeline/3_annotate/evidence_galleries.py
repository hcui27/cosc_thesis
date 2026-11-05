"""Galleries of what the common features look like on the VIBE-CODED pages: for every master-list attribute value, every site whose AI-built page has it, every element the observation cited. No LLM calls.
usage: python pipeline/3_annotate/evidence_galleries.py [--master data/master/master_list.json] [--out data/master/galleries] [--min-sites 2] [--families ...]
One sheet series per attribute value: one tile per cited element (the element's real box with context around it, outlined in red; boxes come from the numbered-element map in <render>/evidence/ made by element_map.py);
whole-page traits (no element cited) get one tile of the top of the page. Sites that have the value but cited nothing are listed in coverage.csv, not dropped silently.
Galleries are keyed by (attribute, value), so re-running build_master.py and then this script regroups them with no new LLM calls. (Originally written for the codebook coder's evidence; now reads the master list.)
"""
import sys, re, csv, json, textwrap, collections, pathlib
from PIL import Image, ImageDraw, ImageFont
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SRC, OUT = pathlib.Path(g("--master", "data/master/master_list.json")), pathlib.Path(g("--out", "data/master/galleries")); OUT.mkdir(parents=True, exist_ok=True)
VIS = set(g("--families", "layout,component,decoration,imagery,color,typography,copy").split(",")); MINS = int(g("--min-sites", 2))
TILE_W, TILE_H, LABEL_H, PER_SHEET = 360, 270, 24, 24
ML = json.load(open(SRC)); book, ev, rows, _vdef = {}, {}, [], {}
for fam, F in ML["families"].items():
    if fam not in VIS: continue
    for i, a in enumerate(F["attributes"]):
        if a["n_sites"] < MINS: continue
        aid = f"{fam[:3].upper()}{i + 1:03d}"; book[aid] = {"id": aid, "name": a["attribute"], "family": fam, "values": [{"value": v["value"], "definition": a["summary"]} for v in a["values"]]}
        for v in a["values"]:
            for s in v["generated_sites"]:
                rows.append({"site_id": s, "attribute_id": aid, "family": fam, "value": v["value"]}); els = v["elements"].get(s, [])
                ev[(s, aid, v["value"])] = {"element_ids": " ".join(els), "page_wide": "0" if els else "1"}
vdef = lambda aid, val: next((v.get("definition", "") for v in book[aid]["values"] if v["value"] == val), "")
def font(sz):
    for p in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F_T, F_S = font(20), font(14)
cache = {}
def page(s):
    if s not in cache:
        cache.clear(); d = pathlib.Path(f"data/{s}/generated_cli/r1/free/render/evidence"); cache[s] = (Image.open(d / "page.png").convert("RGB"), {e["id"]: e for e in json.load(open(d / "elements.json"))})
    return cache[s]
def crop(s, eid):
    im, els = page(s); x, y, w, h = els[eid]["rect"]; px, py = max(120, int(0.35 * w)), max(80, int(0.6 * h))
    box = (max(0, x - px), max(0, y - py), min(im.width, x + w + px), min(im.height, y + h + py))
    if box[2] - box[0] < 20 or box[3] - box[1] < 10: return None      # element lies (partly) outside the screenshot, e.g. an off-screen carousel item
    c = im.crop(box)
    ImageDraw.Draw(c).rectangle((x - box[0] - 2, y - box[1] - 2, x - box[0] + w + 1, y - box[1] + h + 1), outline=(230, 30, 30), width=3); return c
def wide(s): im, _ = page(s); return im.crop((0, 0, im.width, min(im.height, 1000)))
groups = collections.defaultdict(list)
for r in rows: groups[(r["attribute_id"], r["value"])].append(r["site_id"])
slug = lambda x: re.sub(r"[^a-z0-9]+", "-", x.lower()).strip("-")[:40]; cov, index = [], collections.defaultdict(list)
for (aid, val), pages in sorted(groups.items()):
    tiles, located, noev, pw = [], 0, [], 0
    for s in sorted(pages):
        e = ev.get((s, aid, val)); ids = e["element_ids"].split() if e else []
        if ids:
            got = [(s, c, i) for i in ids for c in [crop(s, i)] if c is not None]; tiles += got; located += bool(got)
            if not got: noev.append(s)
        elif e and e["page_wide"] == "1": tiles.append((s, wide(s), "page-wide")); located += 1; pw += 1
        else: noev.append(s)
    b = book[aid]; d = OUT / f"{aid}_{slug(b['name'])}"; d.mkdir(exist_ok=True); sheets = []
    for p in range(0, max(len(tiles), 1), PER_SHEET):
        chunk = tiles[p:p + PER_SHEET]
        if not chunk: break
        cols = 4 if len(chunk) > 3 else max(len(chunk), 1); nrows = -(-len(chunk) // cols); head = textwrap.wrap(f"{aid} {b['name']} = {val}", 70)
        title = head + textwrap.wrap(vdef(aid, val), 95)[:2]; th = 12 + 24 * len(title) + 22
        W, H = cols * (TILE_W + 10) + 10, th + nrows * (TILE_H + LABEL_H + 10) + 10; cv = Image.new("RGB", (W, H), (236, 238, 241)); dr = ImageDraw.Draw(cv)
        for i, line in enumerate(title): dr.text((10, 8 + 24 * i), line, fill=(20, 24, 31), font=F_T if i < len(head) else F_S)
        dr.text((10, th - 20), f"{len(pages)} pages coded with this value; evidence on {located} pages, {len(tiles)} instances; sheet {p // PER_SHEET + 1} of {-(-len(tiles) // PER_SHEET)}", fill=(90, 98, 110), font=F_S)
        for i, (s, c, lab) in enumerate(chunk):
            sc = min(TILE_W / c.width, TILE_H / c.height); c2 = c.resize((max(1, int(c.width * sc)), max(1, int(c.height * sc))), Image.LANCZOS); cx, cy = 10 + (i % cols) * (TILE_W + 10), th + (i // cols) * (TILE_H + LABEL_H + 10)
            dr.rectangle([cx, cy, cx + TILE_W, cy + TILE_H + LABEL_H], fill=(255, 255, 255)); cv.paste(c2, (cx + (TILE_W - c2.width) // 2, cy + (TILE_H - c2.height) // 2)); dr.text((cx + 4, cy + TILE_H + 4), f"{s[:34]} {lab}", fill=(60, 66, 77), font=F_S)
        name = f"{slug(val)}_p{p // PER_SHEET + 1}.jpg"; cv.save(d / name, quality=82); sheets.append(f"{d.name}/{name}")
    cov.append({"attribute_id": aid, "attribute": b["name"], "value": val, "family": b["family"], "pages_coded": len(pages), "pages_with_evidence": located, "instances": len(tiles), "pages_page_wide": pw, "pages_no_evidence": ";".join(noev), "sheets": len(sheets)})
    index[(b["family"], aid, b["name"])].append((val, len(pages), located, len(tiles), sheets))
with open(OUT / "coverage.csv", "w", newline="") as f: w = csv.DictWriter(f, list(cov[0])); w.writeheader(); w.writerows(cov)
md = ["# Galleries from coder-cited evidence (every page coded with a value, every cited element)\n", "Each crop is the real box of an element the coder cited when it assigned the value (red outline, context around it). Cited by the same model that made the claim, so not independent proof; pages with no cited element are listed in coverage.csv.\n"]
for (fam, aid, name), vs in sorted(index.items()):
    md.append(f"\n## {aid} {name} ({fam})\n| value | pages coded | pages with evidence | instances | sheets |\n|---|---|---|---|---|")
    for val, n, loc, ins, sh in vs: md.append(f"| {val} | {n} | {loc} | {ins} | " + ", ".join(f"[{i + 1}]({s})" for i, s in enumerate(sh)) + " |")
(OUT / "index.md").write_text("\n".join(md) + "\n")
tp, tl, ti = sum(c["pages_coded"] for c in cov), sum(c["pages_with_evidence"] for c in cov), sum(c["instances"] for c in cov)
print(f"{len(cov)} galleries; {tl} of {tp} (page, value) pairs with evidence ({100 * tl / tp:.0f}%); {ti} instance crops; sheets in {OUT}")
