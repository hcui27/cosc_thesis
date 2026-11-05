"""Pilot check for evidence-at-coding: (1) do the codes match the earlier evidence-free codes, (2) how many non-absence codes cite evidence, (3) a contact sheet of cited crops for one attribute.
usage: python pipeline/3_annotate/evidence_pilot_report.py --sites a,b,c [--attr A076] [--out data/analysis/codebook_evidence]
"""
import sys, csv, json, re, pathlib, collections
from PIL import Image, ImageDraw
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
OUT = pathlib.Path(g("--out", "data/analysis/codebook_evidence")); sites = g("--sites", "").split(","); ATTR = g("--attr", "A076")
ABS = re.compile(r"\b(none|absent|not present|not used|not applicable|missing|without|other|unclear)\b|\bno[ _][a-z]+|^no$", re.I)
old = {(r["site_id"], r["attribute_id"]): r["value"] for r in csv.DictReader(open("data/analysis/codebook/page_codes_long_generated.csv"))}
new = {(r["site_id"], r["attribute_id"]): r for r in csv.DictReader(open(OUT / "codes_long.csv"))}
ev = {(r["site_id"], r["attribute_id"]): r for r in csv.DictReader(open(OUT / "evidence.csv"))}
fam = collections.defaultdict(lambda: [0, 0, 0, 0, 0])      # agree, compared, real-valued, with evidence or page_wide, with nothing
for (s, a), r in new.items():
    if s not in sites: continue
    o = old.get((s, a)); f = r["family"]
    if o and o != "unclear" and r["value"] != "unclear": fam[f][1] += 1; fam[f][0] += o == r["value"]
    if not ABS.search(r["value"].replace("_", " ")):
        fam[f][2] += 1; e = ev[(s, a)]
        if e["element_ids"] or e["page_wide"] == "1": fam[f][3] += 1
        else: fam[f][4] += 1
print("family | agree with earlier codes | real-valued codes | cited evidence/page_wide | no evidence")
T = [0] * 5
for f, v in sorted(fam.items()):
    print(f"{f:11s} {v[0]}/{v[1]} = {100 * v[0] / max(v[1], 1):.0f}% | {v[2]} | {v[3]} ({100 * v[3] / max(v[2], 1):.0f}%) | {v[4]}"); T = [a + b for a, b in zip(T, v)]
print(f"ALL: agree {T[0]}/{T[1]} = {100 * T[0] / max(T[1], 1):.0f}%; real-valued {T[2]}, with evidence {T[3]} ({100 * T[3] / max(T[2], 1):.0f}%), none {T[4]}")
# contact sheet for ATTR
tiles = []
for s in sites:
    e = ev.get((s, ATTR)); r = new.get((s, ATTR))
    if not e or not e["element_ids"]: continue
    d = pathlib.Path(f"data/{s}/generated_cli/r1/free/render/evidence"); els = {x["id"]: x for x in json.load(open(d / "elements.json"))}; im = Image.open(d / "page.png").convert("RGB")
    for i in e["element_ids"].split():
        x, y, w, h = els[i]["rect"]; px, py = max(120, int(0.35 * w)), max(80, int(0.6 * h)); box = (max(0, x - px), max(0, y - py), min(im.width, x + w + px), min(im.height, y + h + py))
        c = im.crop(box); ImageDraw.Draw(c).rectangle((x - box[0] - 2, y - box[1] - 2, x - box[0] + w + 1, y - box[1] + h + 1), outline=(230, 30, 30), width=2)   # context around the element, the cited element outlined
        c.thumbnail((560, 330)); t = Image.new("RGB", (560, c.height + 24), "white"); t.paste(c, (0, 24)); ImageDraw.Draw(t).text((4, 4), f"{s[:18]} {i}: {r['value']}", fill="black"); tiles.append(t)
if tiles:
    cols = 2; rowsT = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]; hs = [max(t.height for t in r) + 10 for r in rowsT]; sheet = Image.new("RGB", (cols * 570, sum(hs)), "#ddd"); y = 0
    for r, h in zip(rowsT, hs):
        for k, t in enumerate(r): sheet.paste(t, (k * 570, y))
        y += h
    sheet.save(OUT / f"pilot_{ATTR}.jpg", quality=85); print("sheet", OUT / f"pilot_{ATTR}.jpg", len(tiles), "crops")
