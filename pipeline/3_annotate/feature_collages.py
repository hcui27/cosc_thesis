"""Collages: for every shared (key) observation, crop the region of each relevant website's page that shows it and tile the crops into one image.
usage: python pipeline/3_annotate/feature_collages.py [--min-sites 3] [--families layout,component,decoration,imagery,color,typography,copy] [--sites a,b] [--max-features N]
                                                    [--out data/master/collages] [--locator llm|fake] [--model claude-sonnet-5-5] [--workers 3]
Input: data/master/master_list.json (build_master.py): one collage per master-list ATTRIBUTE, one tile per vibe-coded site that has any value of it (generated side only: values kept/changed/added); screenshots data/<site>/generated_cli/r1/free/render/desktop.png.
Step 1, locate (one vision call per site, cached in <out>/boxes/<site>.json): the page screenshot is cut into consecutive slices (1300 px); for each shared observation present on the site the model returns
        the slice and a TIGHT bounding box (fractions of that slice) around the best example, or null when it is page-wide or not visible.
Step 2, collage: crops are padded, scaled to a common tile width and arranged in a grid with a label per tile; the title shows the observation and how many sites it was located on.
Only families with a visible region are used by default (semantic/DOM features have none). --locator fake is ONLY for testing the layout (fixed boxes, never use for results).
Writes <out>/K###_<slug>.png, <out>/index.md, <out>/collage_manifest.json.
"""
import sys, os, re, json, textwrap, collections, pathlib, tempfile, concurrent.futures as cf
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
from PIL import Image, ImageDraw, ImageFont
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MINS, MODEL, WORKERS, LOC = int(g("--min-sites", 3)), g("--model", "claude-sonnet-5-5"), int(g("--workers", 3)), g("--locator", "llm")
FAMS = set(g("--families", "layout,component,decoration,imagery,color,typography,copy").split(",")); OUT = pathlib.Path(g("--out", "data/master/collages")); BD = OUT / "boxes"
OUT.mkdir(parents=True, exist_ok=True); BD.mkdir(exist_ok=True); SLICE_H = 1300; TILE_W, TILE_H, LABEL_H, PAD = 480, 360, 30, 16
shot = lambda s: pathlib.Path(f"data/{s}/generated_cli/r1/free/render/desktop.png")

def load_key(path=g("--master", "data/master/master_list.json")):
    out = []
    for fam, F in json.load(open(path))["families"].items():
        if fam not in FAMS: continue
        for i, a in enumerate(F["attributes"]):
            mem = [{"site": s, "text": v["value"]} for v in a["values"] for s in v["generated_sites"]]
            sites_ = sorted({m["site"] for m in mem})
            if len(sites_) >= MINS: out.append({"id": f"{fam[:3].upper()}{i + 1:03d}", "statement": f"{a['attribute']}: {a['summary']}"[:230], "family": fam, "n_sites": len(sites_), "sites": sites_, "members": mem})
    return out
key = load_key()
if g("--max-features", ""): key = key[:int(g("--max-features", ""))]
sites = [s for s in g("--sites", "").split(",") if s] or sorted({s for k in key for s in k["sites"]})
by_site = {s: [k for k in key if s in k["sites"]] for s in sites}

def valid(b, nslices):
    try: return b and 0 <= int(b["slice"]) < nslices and all(0 <= v <= 1 for v in b["box"]) and b["box"][2] - b["box"][0] > 0.05 and b["box"][3] - b["box"][1] > 0.03
    except Exception: return False

def locate(site):
    fp = BD / f"{site}.json"
    if fp.exists(): return
    feats = by_site[site]; im = Image.open(shot(site)); n = -(-im.height // SLICE_H)
    if LOC == "fake": json.dump({k["id"]: {"slice": 0, "box": [0.05, 0.08 + 0.02 * (i % 5), 0.95, 0.5], "confidence": "fake"} for i, k in enumerate(feats)}, open(fp, "w")); return
    from llm import ask_json_with_files
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); files = []
        for k in range(n):
            f = t / f"slice_{k:02d}.png"; im.convert("RGB").crop((0, k * SLICE_H, im.width, min((k + 1) * SLICE_H, im.height))).save(f); files.append(f)
        items = [{"id": k["id"], "observation": k["statement"], "how_it_appears_here": " | ".join(m["text"] for m in k["members"] if m["site"] == site)[:260]} for k in feats]
        prompt = (f"You are locating UI features on ONE web page. Its screenshot is cut into {n} consecutive slices: slice_00.png ... slice_{n - 1:02d}.png (each 1440 px wide, up to 1300 px tall). Read EVERY slice. "
                  "For each observation below, find the single BEST example on the page and return the slice index and a TIGHT bounding box around it as fractions [x0, y0, x1, y1] (0-1) of THAT slice's width and height "
                  "(e.g. the whole card row, the whole footer, the hero block, the button group). If it is page-wide (e.g. overall type scale), choose a representative block such as the header plus hero. "
                  "The box must contain the whole example but little else; prefer boxes between 10% and 70% of the slice height and within ONE slice. Use null when the feature is not visible.\n"
                  'Final answer ONLY a JSON object mapping each observation id to {"slice": int, "box": [x0, y0, x1, y1], "confidence": "high"|"medium"|"low"} or null.\n\nOBSERVATIONS:\n' + json.dumps(items, ensure_ascii=False))
        res = ask_json_with_files(prompt, MODEL, "collage_locate", files, site=site, n_features=len(feats))
    json.dump({k: v for k, v in res.items() if valid(v, n)}, open(fp, "w"))

todo = [s for s in sites if not (BD / f"{s}.json").exists()]
print(f"{len(key)} shared observations across {len(sites)} sites; {len(todo)} locator calls to run ({LOC})", flush=True)
with cf.ThreadPoolExecutor(WORKERS) as ex:
    futs = [(s, ex.submit(locate, s)) for s in todo]
    for s, f in futs:
        try: f.result(); print("  located", s, flush=True)
        except Exception as e: print("  FAILED", s, type(e).__name__, str(e)[:140], flush=True)

# ---- crop + collage
def font(sz):
    for p in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F_T, F_S = font(22), font(15); manifest, rows = [], []
for k in key:
    crops = []
    for s in k["sites"]:
        fp = BD / f"{s}.json"
        if not fp.exists() or not shot(s).exists(): continue
        b = json.load(open(fp)).get(k["id"])
        im = Image.open(shot(s)).convert("RGB")
        if not b or not valid(b, -(-im.height // SLICE_H)): continue
        y0s = int(b["slice"]) * SLICE_H; sh = min(SLICE_H, im.height - y0s); x0, y0, x1, y1 = b["box"]
        L, T, R, B = max(0, int(x0 * im.width) - PAD), max(0, y0s + int(y0 * sh) - PAD), min(im.width, int(x1 * im.width) + PAD), min(im.height, y0s + int(y1 * sh) + PAD)
        if R - L < 80 or B - T < 40: continue
        crops.append((s, im.crop((L, T, R, min(B, T + 900))), b.get("confidence", "")))
    if not crops: manifest.append({"id": k["id"], "statement": k["statement"], "n_sites": k["n_sites"], "located": 0}); continue
    cols = len(crops) if len(crops) <= 3 else 4; nrows = -(-len(crops) // cols)
    title = textwrap.wrap(f"{k['id']}: {k['statement']}", 78); th = 16 + 28 * len(title) + 26
    W = cols * (TILE_W + 12) + 12; H = th + nrows * (TILE_H + LABEL_H + 12) + 12; canvas = Image.new("RGB", (W, H), (236, 238, 241)); d = ImageDraw.Draw(canvas)
    for i, line in enumerate(title): d.text((12, 12 + 28 * i), line, fill=(20, 24, 31), font=F_T)
    d.text((12, th - 24), f"shared by {k['n_sites']} sites; located on {len(crops)} (family: {k['family'] or 'n/a'})", fill=(90, 98, 110), font=F_S)
    for i, (s, c, conf) in enumerate(crops):
        sc = min(TILE_W / c.width, TILE_H / c.height); c = c.resize((max(1, int(c.width * sc)), max(1, int(c.height * sc))), Image.LANCZOS)
        cx, cy = 12 + (i % cols) * (TILE_W + 12), th + (i // cols) * (TILE_H + LABEL_H + 12)
        d.rectangle([cx, cy, cx + TILE_W, cy + TILE_H + LABEL_H], fill=(255, 255, 255)); canvas.paste(c, (cx + (TILE_W - c.width) // 2, cy + (TILE_H - c.height) // 2))
        d.text((cx + 6, cy + TILE_H + 6), f"{s[:44]}  [{conf}]", fill=(60, 66, 77), font=F_S)
    slug = re.sub(r"[^a-z0-9]+", "-", k["statement"].lower())[:40].strip("-"); name = f"{k['id']}_{slug}.png"; canvas.save(OUT / name)
    manifest.append({"id": k["id"], "statement": k["statement"], "n_sites": k["n_sites"], "located": len(crops), "sites": [c[0] for c in crops], "file": name}); rows.append((k, len(crops), name))
json.dump(manifest, open(OUT / "collage_manifest.json", "w"), indent=1, ensure_ascii=False)
(OUT / "index.md").write_text("# Collages of shared observations\n\n| observation | sites sharing | located | collage |\n|---|---|---|---|\n" + "\n".join(f"| {k['id']} {k['statement']} | {k['n_sites']} | {n} | [{f}]({f}) |" for k, n, f in rows) + "\n")
print(f"{len(rows)} collages written to {OUT} ({sum(m['located'] for m in manifest)} crops of {sum(m['n_sites'] for m in manifest)} possible; {sum(1 for m in manifest if m['located'] == 0)} features with no located crop)")
