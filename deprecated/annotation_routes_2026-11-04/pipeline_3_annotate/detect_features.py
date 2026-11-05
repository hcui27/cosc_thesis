"""Stage 4 of ANALYSIS_PLAN.md: detect every catalog feature on every page.
usage: python pipeline/3_annotate/detect_features.py [--which generated|original] [--sites a,b] [--model claude-sonnet-5-5] [--workers 3] [--batch 100]
 * programmatic: measurements.compute(dom.json) for every page (measurements_<which>.csv); catalog features that carry a `proxy` are evaluated from it.
 * vision checklist: for every page, the screenshot (cut into slices) + the page text + the feature list -> y / n / u per feature (cached in data/analysis/detections/<which>/).
 * final value per site x feature: the programmatic result when the feature has a proxy, else the checklist (y=1, n=0, u=empty).
 * detector agreement: for proxied features, how often the checklist agrees with the programmatic value.
Writes data/analysis/{measurements_<which>.csv, feature_matrix_<which>.csv, detections_long_<which>.csv, detector_agreement[_original].csv}.
generated pages are the Stage 4 target now; --which original is for the later lift comparison.
"""
import sys, os, csv, json, pathlib, collections, concurrent.futures as cf
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from PIL import Image
from llm import ask_json_with_files
import measurements

g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
WHICH, MODEL, WORKERS, BATCH = g("--which", "generated"), g("--model", "claude-sonnet-5-5"), int(g("--workers", 3)), int(g("--batch", 100))
OUT = pathlib.Path("data/analysis"); DD = OUT / "detections" / WHICH; DD.mkdir(parents=True, exist_ok=True); SLICE_H = 1300
cat = json.load(open(OUT / "features_catalog.json"))
sites_all = [r["site_id"] for r in csv.DictReader(open(OUT / "sites_table.csv"))]
sites = [s for s in g("--sites", "").split(",") if s] or sites_all
pdir = lambda s: pathlib.Path(f"data/{s}/generated_cli/r1/free/render") if WHICH == "generated" else pathlib.Path(f"data/{s}/original")

# ---- programmatic measurements
meas = {}
for s in sites:
    d = pdir(s); meas[s] = measurements.compute(json.load(open(d / "dom.json")), (d / "text.txt").read_text() if (d / "text.txt").exists() else None)
with open(OUT / f"measurements_{WHICH}.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["site_id"] + list(measurements.KEYS)); w.writeheader()
    for s in sites: w.writerow({"site_id": s, **meas[s]})

# ---- vision checklist
def checklist(site, bi, feats):
    fp = DD / f"{site}_{bi}.json"
    if fp.exists(): return
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); im = Image.open(pdir(site) / "desktop.png").convert("RGB"); files = []
        for k, y in enumerate(range(0, im.height, SLICE_H)):
            f = t / f"slice_{k:02d}.png"; im.crop((0, y, im.width, min(y + SLICE_H, im.height))).save(f); files.append(f)
        tx = t / "page_text.txt"; tx.write_text((pdir(site) / "text.txt").read_text()[:6000]); files.append(tx)
        prompt = (f"You are checking ONE web page against a list of features. The page screenshot is cut into consecutive slices ({len(files) - 1}): slice_00.png, slice_01.png, ... "
                  "Read EVERY slice, and page_text.txt (the page's visible text). For each feature answer 'y' (clearly present on this page), 'n' (clearly absent) or 'u' (cannot tell from the screenshot). "
                  "Judge only this page; do not assume a feature is present because it is in the list.\n"
                  'Final answer ONLY a JSON object mapping feature id to "y", "n" or "u" for EVERY feature id given.\n\nFEATURES:\n' +
                  json.dumps([{"id": c["id"], "name": c["name"], "definition": c["definition"]} for c in feats], ensure_ascii=False))
        res = ask_json_with_files(prompt, MODEL, "feature_checklist", files, site=site, which=WHICH, n_features=len(feats))
    json.dump(res, open(fp, "w"))

batches = [cat[i:i + BATCH] for i in range(0, len(cat), BATCH)]
todo = [(s, bi, b) for s in sites for bi, b in enumerate(batches) if not (DD / f"{s}_{bi}.json").exists()]
print(f"{len(cat)} features, {len(sites)} {WHICH} pages, {len(batches)} batch(es); {len(todo)} checklist calls to run", flush=True)
with cf.ThreadPoolExecutor(WORKERS) as ex:
    futs = [(s, bi, ex.submit(checklist, s, bi, b)) for s, bi, b in todo]
    for s, bi, f in futs:
        try: f.result(); print("  checklist", s, bi, flush=True)
        except Exception as e: print("  FAILED", s, bi, type(e).__name__, str(e)[:100], flush=True)

# ---- combine
vis = {s: {} for s in sites}
for s in sites:
    for bi in range(len(batches)):
        fp = DD / f"{s}_{bi}.json"
        if fp.exists(): vis[s].update({k: str(v).strip().lower()[:1] for k, v in json.load(open(fp)).items()})
# pass 1: programmatic proxy and checklist value for every site x feature; pass 2: trust a proxy only if it agrees with the checklist on >= 70% of >= 10 pages
raw = {(s, c["id"]): (measurements.check(meas[s], c["proxy"]) if c.get("proxy") else None, {"y": 1, "n": 0}.get(vis[s].get(c["id"]))) for s in sites for c in cat}
agree = collections.defaultdict(lambda: [0, 0])
for (s, fid), (prog, vv) in raw.items():
    if prog is not None and vv is not None: agree[fid][1] += 1; agree[fid][0] += int(prog == vv)
reliable = {c["id"]: (not c.get("proxy")) or agree[c["id"]][1] < 10 or agree[c["id"]][0] / agree[c["id"]][1] >= 0.7 for c in cat}
long, final = [], {s: {} for s in sites}
for s in sites:
    for c in cat:
        prog, vv = raw[(s, c["id"])]; v = vis[s].get(c["id"])
        if prog is not None and reliable[c["id"]]: val, src = prog, "programmatic"
        elif vv is not None: val, src = vv, "vision" + (" (proxy unreliable)" if prog is not None else "")
        else: val, src = (prog, "programmatic (unconfirmed)") if prog is not None else (None, "")
        final[s][c["id"]] = val
        long.append({"site_id": s, "feature_id": c["id"], "programmatic": "" if prog is None else prog, "vision": v or "", "final": "" if val is None else val, "source": src})
with open(OUT / f"detections_long_{WHICH}.csv", "w", newline="") as f: w = csv.DictWriter(f, list(long[0])); w.writeheader(); w.writerows(long)
with open(OUT / f"feature_matrix_{WHICH}.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["site_id"] + [c["id"] for c in cat])
    for s in sites: w.writerow([s] + ["" if final[s][c["id"]] is None else final[s][c["id"]] for c in cat])
with open(OUT / ("detector_agreement.csv" if WHICH == "generated" else f"detector_agreement_{WHICH}.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["feature_id", "name", "n_compared", "agreement", "proxy_used"])
    for c in cat:
        if c.get("proxy"): a, n = agree[c["id"]]; w.writerow([c["id"], c["name"], n, round(a / n, 3) if n else "", "yes" if reliable[c["id"]] else "no (fell back to vision)"])
filled = sum(v is not None for s in sites for v in final[s].values()); print(f"matrix {len(sites)} x {len(cat)}: {filled} of {len(sites) * len(cat)} cells filled ({100 * filled / (len(sites) * len(cat)):.0f}%); programmatic features: {sum(bool(c.get('proxy')) for c in cat)}, of which unreliable proxies (fell back to vision): {sum(1 for c in cat if c.get('proxy') and not reliable[c['id']])}")
