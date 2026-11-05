"""EXHAUSTIVE galleries: for every attribute value in the codebook, show EVERY page coded with it and EVERY visible instance on each page.
usage: python pipeline/3_annotate/attribute_galleries.py [--families layout,component,decoration,imagery,color,typography,copy] [--sites a,b] [--max-instances 6] [--batch 50]
                                                      [--out data/analysis/galleries] [--model claude-sonnet-5-5] [--workers 3] [--only-attrs A046,A083] [--build-only]
Unlike feature_collages.py (one crop per site, only sites a judge happened to mention) this starts from the complete coded matrix (code_pages.py): the pages in a gallery are exactly the pages coded with that value.
Step 1, locate: per page, one vision call per batch of attribute-value items (cached in <out>/boxes/): the model returns ALL instances it can see (up to --max-instances) as boxes in fractions of a screenshot slice,
        or one representative region flagged page_wide for page-level properties (type scale, palette, overall layout), or nothing when it cannot see the value. Boxes are NOT verified.
Step 2, galleries: crops are tiled into paginated contact sheets (JPEG, 24 tiles per sheet), grouped by attribute and value; page-wide tiles are marked. Absence values (none / not present / other / not_applicable) and 'unclear' have no gallery.
Writes <out>/<A###_attribute>/<value>_p<k>.jpg, <out>/index.md (coverage per gallery), <out>/coverage.csv (pages coded, pages located, instances, page-wide, unlocated pages).
"""
import sys, os, re, csv, json, textwrap, collections, pathlib, tempfile, concurrent.futures as cf
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
from PIL import Image, ImageDraw, ImageFont
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
VIS = set(g("--families", "layout,component,decoration,imagery,color,typography,copy").split(",")); MAXI, BATCH, MODEL, WORKERS = int(g("--max-instances", 6)), int(g("--batch", 50)), g("--model", "claude-sonnet-5-5"), int(g("--workers", 3))
OUT = pathlib.Path(g("--out", "data/analysis/galleries")); BD = OUT / "boxes"; OUT.mkdir(parents=True, exist_ok=True); BD.mkdir(exist_ok=True)
CD = pathlib.Path("data/analysis/codebook"); SLICE_H, TILE_W, TILE_H, LABEL_H, PAD, PER_SHEET = 1300, 360, 270, 24, 14, 24
ABSENCE = re.compile(r"\b(none|absent|not present|not used|not applicable|missing|without|other|unclear)\b|\bno[ _][a-z]+|^no$", re.I)
book = {b["id"]: b for b in json.load(open(CD / "codebook.json"))}
shot = lambda s: pathlib.Path(f"data/{s}/generated_cli/r1/free/render/desktop.png")
rows = [r for r in csv.DictReader(open(CD / "page_codes_long_generated.csv")) if r["family"] in VIS and not ABSENCE.search(r["value"].replace("_", " "))]
if g("--only-attrs", ""): only = set(g("--only-attrs", "").split(",")); rows = [r for r in rows if r["attribute_id"] in only]
sites = [s for s in g("--sites", "").split(",") if s] or sorted({r["site_id"] for r in rows}); rows = [r for r in rows if r["site_id"] in sites]
vdef = lambda aid, val: next((v.get("definition", "") for v in book[aid]["values"] if v["value"] == val), "")
by_site = collections.defaultdict(list)
for r in rows: by_site[r["site_id"]].append({"aid": r["attribute_id"], "value": r["value"]})

def valid(b, ns):
    try: return 0 <= int(b["slice"]) < ns and all(0 <= v <= 1 for v in b["box"]) and b["box"][2] - b["box"][0] > 0.04 and b["box"][3] - b["box"][1] > 0.02
    except Exception: return False

def locate(site, k, items):
    fp = BD / f"{site}_{k}.json"
    if fp.exists(): return
    from llm import ask_json_with_files
    im = Image.open(shot(site)); n = -(-im.height // SLICE_H)
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); files = []
        for i in range(n):
            f = t / f"slice_{i:02d}.png"; im.convert("RGB").crop((0, i * SLICE_H, im.width, min((i + 1) * SLICE_H, im.height))).save(f); files.append(f)
        q = [{"id": f"i{j}", "attribute": book[it["aid"]]["name"], "attribute_definition": book[it["aid"]]["definition"][:160], "value_on_this_page": it["value"], "value_definition": vdef(it["aid"], it["value"])[:160]} for j, it in enumerate(items)]
        prompt = (f"You are locating examples of coded design features on ONE web page. Its screenshot is cut into {n} consecutive slices: slice_00.png ... slice_{n - 1:02d}.png (each 1440 px wide, up to 1300 px tall). Read EVERY slice. "
                  "For each item, this page was coded with the given value for the attribute. Find EVERY visible instance of that value on the page (for example every card, every label, every button group), up to "
                  f"{MAXI} instances, and give each as a TIGHT bounding box [x0, y0, x1, y1] in fractions (0-1) of the width and height of ONE slice, plus that slice's index. Keep each box inside one slice (split an instance that crosses slices into its best part). "
                  "If the item describes the page as a whole (type scale, overall palette, overall layout, spacing), return ONE box around a representative region (usually the header plus hero) and set page_wide to true. "
                  "If you cannot see the value anywhere, return an empty boxes list. Do not invent boxes.\n"
                  'Final answer ONLY a JSON object: {"i0": {"page_wide": false, "boxes": [{"slice": 0, "box": [0.1, 0.2, 0.9, 0.4]}]}, ...} with one entry per item id.\n\nITEMS:\n' + json.dumps(q, ensure_ascii=False))
        res = ask_json_with_files(prompt, MODEL, "gallery_locate", files, site=site, n_items=len(items))
    out = {}
    for j, it in enumerate(items):
        e = res.get(f"i{j}") or {}; bx = [{"slice": int(b["slice"]), "box": [float(v) for v in b["box"]]} for b in (e.get("boxes") or []) if valid(b, n)][:MAXI]
        out[f"{it['aid']}|{it['value']}"] = {"page_wide": bool(e.get("page_wide")), "boxes": bx}
    json.dump(out, open(fp, "w"))

todo = []
for s in sites:
    its = by_site[s]
    for k in range(0, len(its), BATCH):
        if not (BD / f"{s}_{k // BATCH}.json").exists(): todo.append((s, k // BATCH, its[k:k + BATCH]))
if "--build-only" not in sys.argv:
    print(f"{len(rows)} page-level items ({len({(r['attribute_id'], r['value']) for r in rows})} attribute-value galleries) on {len(sites)} pages; {len(todo)} locator calls to run", flush=True)
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = [(s, k, ex.submit(locate, s, k, it)) for s, k, it in todo]
        for s, k, f in futs:
            try: f.result(); print("  located", s, k, flush=True)
            except Exception as e: print("  FAILED", s, k, type(e).__name__, str(e)[:120], flush=True)

# ---- galleries
def font(sz):
    for p in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F_T, F_S = font(20), font(14)
boxes = {}                                                              # (site, aid|value) -> {page_wide, boxes}
for fp in BD.glob("*.json"):
    s = re.sub(r"_\d+\.json$", "", fp.name)
    for k, v in json.load(open(fp)).items(): boxes[(s, k)] = v
img_cache = {}
def crop(s, b):
    if s not in img_cache: img_cache.clear(); img_cache[s] = Image.open(shot(s)).convert("RGB")
    im = img_cache[s]; y0s = b["slice"] * SLICE_H; sh = min(SLICE_H, im.height - y0s); x0, y0, x1, y1 = b["box"]
    L, T, R, B_ = max(0, int(x0 * im.width) - PAD), max(0, y0s + int(y0 * sh) - PAD), min(im.width, int(x1 * im.width) + PAD), min(im.height, y0s + int(y1 * sh) + PAD)
    return im.crop((L, T, R, min(B_, T + 800))) if R - L >= 60 and B_ - T >= 30 else None
groups = collections.defaultdict(list)                                  # (aid, value) -> pages coded
for r in rows: groups[(r["attribute_id"], r["value"])].append(r["site_id"])
cov, index = [], collections.defaultdict(list); slug = lambda x: re.sub(r"[^a-z0-9]+", "-", x.lower()).strip("-")[:40]
for (aid, val), pages in sorted(groups.items()):
    tiles, located, unloc, wide = [], 0, [], 0
    for s in sorted(pages):
        e = boxes.get((s, f"{aid}|{val}"))
        if not e: unloc.append(s); continue
        got = 0
        for i, b in enumerate(e["boxes"]):
            c = crop(s, b)
            if c is not None: tiles.append((s, c, f"#{i + 1}" + (" page-wide" if e["page_wide"] else ""))); got += 1
        located += got > 0; wide += (got > 0 and e["page_wide"])
        if not got: unloc.append(s)
    b = book[aid]; d = OUT / f"{aid}_{slug(b['name'])}"; d.mkdir(exist_ok=True); sheets = []
    for p in range(0, max(len(tiles), 1), PER_SHEET):
        chunk = tiles[p:p + PER_SHEET]
        if not chunk: break
        cols = 4 if len(chunk) > 3 else max(len(chunk), 1); nrows = -(-len(chunk) // cols)
        title = textwrap.wrap(f"{aid} {b['name']} = {val}", 70) + textwrap.wrap(vdef(aid, val), 95)[:2]; th = 12 + 24 * len(title) + 22
        W, H = cols * (TILE_W + 10) + 10, th + nrows * (TILE_H + LABEL_H + 10) + 10; cv = Image.new("RGB", (W, H), (236, 238, 241)); dr = ImageDraw.Draw(cv)
        for i, line in enumerate(title): dr.text((10, 8 + 24 * i), line, fill=(20, 24, 31), font=F_T if i < len(textwrap.wrap(f"{aid} {b['name']} = {val}", 70)) else F_S)
        dr.text((10, th - 20), f"{len(pages)} pages coded with this value; located on {located} pages, {len(tiles)} instances; sheet {p // PER_SHEET + 1} of {-(-len(tiles) // PER_SHEET)}", fill=(90, 98, 110), font=F_S)
        for i, (s, c, lab) in enumerate(chunk):
            sc = min(TILE_W / c.width, TILE_H / c.height); c2 = c.resize((max(1, int(c.width * sc)), max(1, int(c.height * sc))), Image.LANCZOS); cx, cy = 10 + (i % cols) * (TILE_W + 10), th + (i // cols) * (TILE_H + LABEL_H + 10)
            dr.rectangle([cx, cy, cx + TILE_W, cy + TILE_H + LABEL_H], fill=(255, 255, 255)); cv.paste(c2, (cx + (TILE_W - c2.width) // 2, cy + (TILE_H - c2.height) // 2)); dr.text((cx + 4, cy + TILE_H + 4), f"{s[:34]} {lab}", fill=(60, 66, 77), font=F_S)
        name = f"{slug(val)}_p{p // PER_SHEET + 1}.jpg"; cv.save(d / name, quality=82); sheets.append(f"{d.name}/{name}")
    cov.append({"attribute_id": aid, "attribute": b["name"], "value": val, "family": b["family"], "pages_coded": len(pages), "pages_located": located, "instances": len(tiles), "pages_page_wide": wide, "pages_unlocated": ";".join(unloc), "sheets": len(sheets)})
    index[(b["family"], aid, b["name"])].append((val, len(pages), located, len(tiles), sheets))
with open(OUT / "coverage.csv", "w", newline="") as f: w = csv.DictWriter(f, list(cov[0])); w.writeheader(); w.writerows(cov)
md = ["# Exhaustive galleries (every page coded with a value, every located instance)\n", "Pages come from the complete coded matrix (code_pages.py), not from judge mentions. Boxes are located by a vision model and are NOT verified; `unlocated` pages were coded with the value but no region was found.\n"]
for (fam, aid, name), vs in sorted(index.items()):
    md.append(f"\n## {aid} {name} ({fam})\n| value | pages coded | pages located | instances | sheets |\n|---|---|---|---|---|")
    for val, n, loc, ins, sh in vs: md.append(f"| {val} | {n} | {loc} | {ins} | " + ", ".join(f"[{i + 1}]({s})" for i, s in enumerate(sh)) + " |")
(OUT / "index.md").write_text("\n".join(md) + "\n")
tp, tl, ti = sum(c["pages_coded"] for c in cov), sum(c["pages_located"] for c in cov), sum(c["instances"] for c in cov)
print(f"{len(cov)} galleries; {tl} of {tp} (page, value) pairs located ({100 * tl / tp:.0f}%); {ti} instance crops; sheets written to {OUT}")
