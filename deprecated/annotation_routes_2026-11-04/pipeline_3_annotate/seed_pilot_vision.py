"""SUPERSEDED by seed_pilot.py (2026-10-29): the seed list is now matched to the judges' observations and the codebook, not coded from the page. Kept as a vision-based reference (page-presence, no judges involved).
PILOT: code every generated page against the closed SEED list (seed_attributes/seed_v1.csv, from external glossaries) and summarise how often each item is present.
NO CULLING YET (decided 2026-10-26): the list is not trimmed here; which items are relevant is read off the prevalence table later (see PLAN.md, "Seed list: culling, later").
usage: python pipeline/3_annotate/seed_pilot.py [--stage code|summary|all] [--sites a,b] [--batch 41] [--model claude-sonnet-5-5] [--workers 4] [--dry-run]
code: per page and batch of seed items, one vision call (screenshot slices from evidence/page.png, page text, measurements, elements.txt from element_map.py). For each item the coder says present yes/no/unclear,
      how many instances, the element ids that show it, and a short note on how it looks (the raw material for values later). Writes data/analysis_seed/pages/<site>_<k>.json and presence.csv.
summary: offline. Per item: pages present, prevalence, mean instances, example notes -> seed_summary.csv (all items, sorted by prevalence), plus presence.csv (one row per page and item). No keep/drop decision.
Needs element_map.py to have been run on the generated pages first. Nothing here uses the 278-attribute codebook.
"""
import sys, csv, json, re, pathlib, tempfile, collections, concurrent.futures as cf
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
STAGE, BATCH, MODEL, WORKERS, DRY = g("--stage", "all"), int(g("--batch", 41)), g("--model", "claude-sonnet-5-5"), int(g("--workers", 4)), "--dry-run" in sys.argv
OUT = pathlib.Path("data/analysis_seed"); PD = OUT / "pages"; PD.mkdir(parents=True, exist_ok=True); SLICE_H = 1300
items = list(csv.DictReader(open("seed_attributes/seed_v1.csv")))
sites = [s for s in g("--sites", "").split(",") if s] or [r["site_id"] for r in csv.DictReader(open("data/sites.csv")) if (pathlib.Path(f"data/{r['site_id']}/generated_cli/r1/free/render/evidence/elements.txt")).exists()]
rd = lambda s: pathlib.Path(f"data/{s}/generated_cli/r1/free/render")
batches = [items[i:i + BATCH] for i in range(0, len(items), BATCH)]

def code(site, k, chunk):
    fp = PD / f"{site}_{k}.json"
    if fp.exists(): return
    from PIL import Image
    from llm import ask_json_with_files
    import measurements
    d = rd(site); ev = d / "evidence"; m = measurements.compute(json.load(open(d / "dom.json")), (d / "text.txt").read_text())
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); im = Image.open(ev / "page.png").convert("RGB"); files = []
        for i, y in enumerate(range(0, im.height, SLICE_H)):
            f = t / f"slice_{i:02d}.png"; im.crop((0, y, im.width, min(y + SLICE_H, im.height))).save(f); files.append(f)
        (t / "page_text.txt").write_text((d / "text.txt").read_text()[:6000]); (t / "elements.txt").write_text((ev / "elements.txt").read_text())
        (t / "measurements.json").write_text(json.dumps({a: (round(v, 3) if isinstance(v, float) else v) for a, v in m.items()})); files += [t / "page_text.txt", t / "elements.txt", t / "measurements.json"]
        q = [{"id": f"s{n}", "item": it["item"], "kind": it["kind"], "also_called": it["alternate_names"]} for n, it in enumerate(chunk)]
        prompt = ("You are cataloguing ONE web page against a fixed list of UI components and page sections. The screenshot is cut into consecutive slices (slice_00.png ..., 1300 px tall, 1440 px wide); also given: page_text.txt, "
                  "measurements.json (ground truth) and elements.txt (numbered visible elements: id | parent | tag | x,y,w,h | text). Read everything. For each item decide whether THIS page has it: kind 'component' = a UI component of that type "
                  "(including under its alternate names); kind 'page_section' = a section of the page that serves that purpose. Do not count something merely because the name could apply loosely.\n"
                  'Final answer ONLY a JSON object mapping each item id to {"present": "yes"|"no"|"unclear", "instances": <int, 0 if none>, "evidence": [element ids, up to 6, smallest element that shows it], "note": "<=12 words on how it looks, or empty"}, for EVERY id.\n\nITEMS:\n' + json.dumps(q, ensure_ascii=False))
        res = ask_json_with_files(prompt, MODEL, "seed_pilot", files, site=site, n_items=len(chunk))
    json.dump(res, open(fp, "w"), ensure_ascii=False)

if STAGE in ("code", "all"):
    todo = [(s, k, c) for s in sites for k, c in enumerate(batches) if not (PD / f"{s}_{k}.json").exists()]
    print(f"{len(items)} seed items, {len(sites)} pages, {len(batches)} batches/page -> {len(todo)} calls (about $0.15 each, so about ${0.15 * len(todo):.1f})", flush=True)
    if DRY: sys.exit()
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = [(s, k, ex.submit(code, s, k, c)) for s, k, c in todo]
        for s, k, f in futs:
            try: f.result(); print("  coded", s, k, flush=True)
            except Exception as e: print("  FAILED", s, k, type(e).__name__, str(e)[:120], flush=True)
if STAGE in ("summary", "all"):
    pres = {}
    for s in sites:
        d = {}
        for k in range(len(batches)):
            fp = PD / f"{s}_{k}.json"
            if fp.exists(): d.update(json.load(open(fp)))
        for n, it in enumerate(items):
            e = d.get(f"s{n}") if not isinstance(d.get(f"s{n}"), str) else None
            if isinstance(e, dict): pres[(s, it["item"])] = e
    with open(OUT / "presence.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["site_id", "item", "kind", "present", "instances", "evidence", "note"])
        for (s, it), e in sorted(pres.items()): w.writerow([s, it, next(x["kind"] for x in items if x["item"] == it), e.get("present"), e.get("instances"), " ".join(e.get("evidence") or []), e.get("note", "")])
    rows = []
    for it in items:
        ps = [(s, pres[(s, it["item"])]) for s in sites if (s, it["item"]) in pres]; yes = [(s, e) for s, e in ps if e.get("present") == "yes"]
        rows.append({"item": it["item"], "kind": it["kind"], "sources": it["sources"], "pages_coded": len(ps), "pages_present": len(yes), "prevalence": round(len(yes) / max(len(ps), 1), 3),
                     "mean_instances_when_present": round(sum(int(e.get("instances") or 0) for _, e in yes) / max(len(yes), 1), 2), "pages_unclear": sum(e.get("present") == "unclear" for _, e in ps),
                     "example_notes": " | ".join(e.get("note", "") for _, e in yes[:4] if e.get("note"))})
    rows.sort(key=lambda r: -r["pages_present"])
    with open(OUT / "seed_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    bins = collections.Counter("0" if r["pages_present"] == 0 else "1-2" if r["pages_present"] <= 2 else "3-6" if r["pages_present"] <= 6 else "7-13" if r["pages_present"] <= 13 else "14+" for r in rows)
    print(f"{len(items)} seed items; present on 0 pages: {bins['0']}, 1-2: {bins['1-2']}, 3-6: {bins['3-6']}, 7-13: {bins['7-13']}, 14+: {bins['14+']} (no items dropped)")
    print("top 15:", ", ".join(f"{r['item']} ({r['pages_present']})" for r in rows[:15]))
