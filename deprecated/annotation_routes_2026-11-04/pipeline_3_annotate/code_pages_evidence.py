"""Code every page for every codebook attribute AND cite the evidence (element ids) in the same call.
usage: python pipeline/3_annotate/code_pages_evidence.py --sites a,b [--model claude-sonnet-5-5] [--workers 3] [--batch 60] [--out data/analysis/codebook_evidence]
Same inputs as code_pages.py (screenshot slices, page text, measurements, closed value sets) plus elements.txt from element_map.py (the numbered visible elements of that page; the
screenshot slices are cut from evidence/page.png, the image the element boxes belong to). Per attribute the coder returns {"value": ..., "evidence": [element ids], "page_wide": bool}.
The gallery crop of an instance is that element's real bounding box, so no separate locator call is needed. Writes <out>/pages/<site>_<k>.json and <out>/codes_long.csv + evidence.csv.
"""
import sys, os, csv, json, re, pathlib, tempfile, concurrent.futures as cf
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
from PIL import Image
from llm import ask_json_with_files
import measurements
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MODEL, WORKERS, BATCH = g("--model", "claude-sonnet-5-5"), int(g("--workers", 3)), int(g("--batch", 60))
CD = pathlib.Path("data/analysis/codebook"); OUT = pathlib.Path(g("--out", "data/analysis/codebook_evidence")); PD = OUT / "pages"; PD.mkdir(parents=True, exist_ok=True); SLICE_H = 1300
NOT_STATED = re.compile(r"\bnot[ _-]?(stated|specified|mentioned|observed|noted)\b|\bunspecified\b|\bunknown\b|\bn/a\b", re.I)
ABSENCE = re.compile(r"\b(none|absent|not present|not used|not applicable|missing|without)\b|\bno[ _][a-z]+|^no$|\bother\b", re.I)
ESCAPE = {"value": "not_applicable", "definition": "the feature this attribute describes does not exist on this page"}
book = json.load(open(CD / "codebook.json"))
for b in book:      # identical allowed-value rules to code_pages.py
    b["allowed"] = [v for v in b["values"] if not NOT_STATED.search(v["value"])] or b["values"]
    if not any(ABSENCE.search(v["value"]) for v in b["allowed"]) and (b["n_sites_mentioning"] <= 5 or len(b["allowed"]) < 2): b["allowed"] = b["allowed"] + [ESCAPE]
sites = [s for s in g("--sites", "").split(",") if s] or [r["site_id"] for r in csv.DictReader(open("data/analysis/sites_table.csv"))]
rdir = lambda s: pathlib.Path(f"data/{s}/generated_cli/r1/free/render")

def code(site, k, attrs):
    fp = PD / f"{site}_{k}.json"
    if fp.exists(): return
    d = rdir(site); ev = d / "evidence"; m = measurements.compute(json.load(open(d / "dom.json")), (d / "text.txt").read_text())
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); im = Image.open(ev / "page.png").convert("RGB"); files = []
        for i, y in enumerate(range(0, im.height, SLICE_H)):
            f = t / f"slice_{i:02d}.png"; im.crop((0, y, im.width, min(y + SLICE_H, im.height))).save(f); files.append(f)
        (t / "page_text.txt").write_text((d / "text.txt").read_text()[:6000]); (t / "elements.txt").write_text((ev / "elements.txt").read_text())
        (t / "measurements.json").write_text(json.dumps({a: (round(v, 3) if isinstance(v, float) else v) for a, v in m.items()})); files += [t / "page_text.txt", t / "elements.txt", t / "measurements.json"]
        items = [{"id": a["id"], "attribute": a["name"], "definition": a["definition"], "values": [{"value": v["value"], "definition": v.get("definition", "")} for v in a["allowed"]]} for a in attrs]
        prompt = ("You are coding ONE web page. Its screenshot is cut into consecutive slices (slice_00.png ... , 1300 px tall each, 1440 px wide); also provided: page_text.txt (visible text), measurements.json (programmatic measurements: "
                  "treat as ground truth) and elements.txt, the numbered list of the page's visible elements (id | parent | tag | x,y,w,h in page pixels | text; slice i covers y from 1300*i to 1300*(i+1)). Read EVERYTHING. "
                  "For each attribute below choose EXACTLY ONE of its allowed values for THIS page, or 'unclear' if it cannot be determined. Judge only this page.\n"
                  "ALSO give the EVIDENCE for the value you chose: the ids (from elements.txt) of the elements that show it. Rules: cite each distinct instance you can see (up to 6) by the SMALLEST element that shows the value "
                  "(the label itself, not the section containing it); for a value that describes the page as a whole (palette, type scale, overall layout, spacing) set page_wide true and cite no ids; for absence values "
                  "('none', 'not_applicable', 'unclear') cite nothing. Only use ids that appear in elements.txt. If the value is real but you cannot find a matching element, return an empty evidence list.\n"
                  'Final answer ONLY a JSON object mapping each attribute id to {"value": "<chosen value>", "evidence": ["e12", "e40"], "page_wide": false}, for EVERY attribute id given.\n\nATTRIBUTES:\n' + json.dumps(items, ensure_ascii=False))
        res = ask_json_with_files(prompt, MODEL, "page_coding_evidence", files, site=site, n_attributes=len(attrs))
    json.dump(res, open(fp, "w"), ensure_ascii=False)

todo = [(s, i // BATCH, book[i:i + BATCH]) for s in sites for i in range(0, len(book), BATCH) if not (PD / f"{s}_{i // BATCH}.json").exists()]
print(f"{len(book)} attributes, {len(sites)} pages, {len(todo)} calls to run", flush=True)
with cf.ThreadPoolExecutor(WORKERS) as ex:
    futs = [(s, k, ex.submit(code, s, k, ch)) for s, k, ch in todo]
    for s, k, f in futs:
        try: f.result(); print("  coded", s, k, flush=True)
        except Exception as e: print("  FAILED", s, k, type(e).__name__, str(e)[:150], flush=True)
allowed = {b["id"]: {v["value"] for v in b["allowed"]} for b in book}
with open(OUT / "codes_long.csv", "w", newline="") as f1, open(OUT / "evidence.csv", "w", newline="") as f2:
    w1, w2 = csv.writer(f1), csv.writer(f2); w1.writerow(["site_id", "attribute_id", "attribute", "family", "value"]); w2.writerow(["site_id", "attribute_id", "value", "page_wide", "element_ids"])
    for s in sites:
        d = {}
        for fp in sorted(PD.glob(f"{s}_*.json")): d.update(json.load(open(fp)))
        valid_ids = {e["id"] for e in json.load(open(rdir(s) / "evidence/elements.json"))}
        for b in book:
            e = d.get(b["id"]); 
            if not isinstance(e, dict): continue
            v = e.get("value"); v = v if v in allowed[b["id"]] else "unclear"; w1.writerow([s, b["id"], b["name"], b["family"], v])
            ids = [i for i in (e.get("evidence") or []) if i in valid_ids]; w2.writerow([s, b["id"], v, int(bool(e.get("page_wide"))), " ".join(ids)])
import collections          # wide matrix + agreement with the values coded from the judges' observations (same outputs as code_pages.py, so analyze_attributes.py can read this directory)
vals = collections.defaultdict(dict)
for r in csv.DictReader(open(OUT / "codes_long.csv")): vals[r["site_id"]][r["attribute_id"]] = r["value"]
with open(OUT / "page_codes_generated.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["site_id"] + [b["id"] for b in book])
    for s_ in sites: w.writerow([s_] + [vals[s_].get(b["id"], "") for b in book])
obs = {r["site_id"]: r for r in csv.DictReader(open(CD / "site_attribute_values_from_observations.csv"))}; ag = collections.defaultdict(lambda: [0, 0, 0])
for s_ in sites:
    for b in book:
        o, p_ = obs.get(s_, {}).get(b["id"], ""), vals[s_].get(b["id"], "")
        if o and p_ and p_ != "unclear": ag[b["id"]][1] += 1; ag[b["id"]][0] += int(o == p_)
        if o and p_ == "unclear": ag[b["id"]][2] += 1
with open(OUT / "coder_agreement.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["attribute_id", "attribute", "family", "n_compared", "agreement", "n_unclear_vs_observed"])
    for b in book: a, n, u = ag[b["id"]]; w.writerow([b["id"], b["name"], b["family"], n, round(a / n, 3) if n else "", u])
print("written", OUT)
