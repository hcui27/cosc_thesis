"""Code EVERY generated page to a value for EVERY codebook attribute (so 'not mentioned' is separated from 'absent').
usage: python pipeline/3_annotate/code_pages.py [--which generated|original] [--sites a,b] [--model claude-sonnet-5-5] [--workers 3] [--batch 60]
Per page and batch of attributes, one vision call: the screenshot (cut into slices), the page text and the programmatic measurements (ground truth) go in with each attribute's definition and its CLOSED value
set (+ 'unclear'); the coder returns one value per attribute. Values such as 'not stated' are removed from the allowed sets (the coder can see the page).
Writes data/analysis/codebook/{page_codes_<which>.csv (sites x attributes), page_codes_long_<which>.csv, coder_agreement.csv} (agreement with the values coded from the judges' observations).
--which original codes the 2021 originals with the same codebook (needed for lift against the originals).
"""
import sys, os, csv, json, re, pathlib, tempfile, collections, concurrent.futures as cf
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
from PIL import Image
from llm import ask_json_with_files
import measurements
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
WHICH, MODEL, WORKERS, BATCH = g("--which", "generated"), g("--model", "claude-sonnet-5-5"), int(g("--workers", 3)), int(g("--batch", 60))
OUT = pathlib.Path("data/analysis"); CD = OUT / "codebook"; PD = CD / "pages" / WHICH; PD.mkdir(parents=True, exist_ok=True); SLICE_H = 1300
NOT_STATED = re.compile(r"\bnot[ _-]?(stated|specified|mentioned|observed|noted)\b|\bunspecified\b|\bunknown\b|\bn/a\b", re.I)  # word-bounded: an unbounded n/?a once removed real values (dominant, navy, banner)
book = json.load(open(CD / "codebook.json"))
ABSENCE = re.compile(r"\b(none|absent|not present|not used|not applicable|missing|without)\b|\bno[ _][a-z]+|^no$|\bother\b", re.I)
ESC_MAX = int(g("--escape-max-mentions", 5))   # attributes mentioned by few sites are usually conditional (e.g. 'announcement bar height'): give them an explicit way to say the feature is absent
ESCAPE = {"value": "not_applicable", "definition": "the feature this attribute describes does not exist on this page"}
for b in book:
    b["allowed"] = [v for v in b["values"] if not NOT_STATED.search(v["value"])] or b["values"]
    if not any(ABSENCE.search(v["value"]) for v in b["allowed"]) and (b["n_sites_mentioning"] <= ESC_MAX or len(b["allowed"]) < 2): b["allowed"] = b["allowed"] + [ESCAPE]
sites_all = [r["site_id"] for r in csv.DictReader(open(OUT / "sites_table.csv"))]; sites = [s for s in g("--sites", "").split(",") if s] or sites_all
pdir = lambda s: pathlib.Path(f"data/{s}/generated_cli/r1/free/render") if WHICH == "generated" else pathlib.Path(f"data/{s}/original")
def have(s):                                    # everything already coded for this site (initial batch files and later fix-up files)
    d = {}
    for fp in sorted(PD.glob(f"{s}_*.json")):
        if re.fullmatch(rf"{re.escape(s)}_(\d+|x[A-Z]\d+)\.json", fp.name): d.update(json.load(open(fp)))
    return d

def code(site, name, attrs):
    fp = PD / f"{site}_{name}.json"
    d = pdir(site); m = measurements.compute(json.load(open(d / "dom.json")), (d / "text.txt").read_text() if (d / "text.txt").exists() else None)
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); im = Image.open(d / "desktop.png").convert("RGB"); files = []
        for k, y in enumerate(range(0, im.height, SLICE_H)):
            f = t / f"slice_{k:02d}.png"; im.crop((0, y, im.width, min(y + SLICE_H, im.height))).save(f); files.append(f)
        (t / "page_text.txt").write_text((d / "text.txt").read_text()[:6000]); (t / "measurements.json").write_text(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}))
        files += [t / "page_text.txt", t / "measurements.json"]
        items = [{"id": a["id"], "attribute": a["name"], "definition": a["definition"], "values": [{"value": v["value"], "definition": v.get("definition", "")} for v in a["allowed"]]} for a in attrs]
        prompt = (f"You are coding ONE web page. Its screenshot is cut into consecutive slices (slice_00.png ... ); also provided: page_text.txt (visible text) and measurements.json (programmatic measurements of the page: "
                  "treat them as ground truth, e.g. border radius shares, shadow counts, font sizes, tag counts). Read EVERYTHING. For each attribute below choose EXACTLY ONE of its allowed values for THIS page, "
                  "or 'unclear' if it cannot be determined from what you can see. Judge only this page.\n"
                  'Final answer ONLY a JSON object mapping attribute id to the chosen value string, for EVERY attribute id given.\n\nATTRIBUTES:\n' + json.dumps(items, ensure_ascii=False))
        res = ask_json_with_files(prompt, MODEL, "page_coding", files, site=site, which=WHICH, n_attributes=len(attrs))
    json.dump(res, open(fp, "w"), ensure_ascii=False)

todo = []                                       # (site, file name, attributes still missing); first pass uses numbered batches, later passes x<first attribute id>
for s in sites:
    h = have(s); missing = [b for b in book if b["id"] not in h]
    for i in range(0, len(missing), BATCH):
        ch = missing[i:i + BATCH]; first_pass = not h and len(missing) == len(book)
        todo.append((s, (i // BATCH) if first_pass else f"x{ch[0]['id']}", ch))
print(f"{len(book)} attributes, {len(sites)} {WHICH} pages; {len(todo)} coding calls to run ({sum(len(c) for _, _, c in todo)} attribute-codings)", flush=True)
with cf.ThreadPoolExecutor(WORKERS) as ex:
    futs = [(s, nm, ex.submit(code, s, nm, ch)) for s, nm, ch in todo]
    for s, nm, f in futs:
        try: f.result(); print("  coded", s, nm, flush=True)
        except Exception as e: print("  FAILED", s, nm, type(e).__name__, str(e)[:120], flush=True)

vals = {s: {} for s in sites}; allowed = {b["id"]: {v["value"] for v in b["allowed"]} for b in book}
for s in sites:
    for k, v in have(s).items():
        if k in allowed: vals[s][k] = v if v in allowed[k] else "unclear"
with open(CD / f"page_codes_{WHICH}.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["site_id"] + [b["id"] for b in book])
    for s in sites: w.writerow([s] + [vals[s].get(b["id"], "") for b in book])
with open(CD / f"page_codes_long_{WHICH}.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["site_id", "attribute_id", "attribute", "family", "value"])
    for s in sites:
        for b in book:
            if b["id"] in vals[s]: w.writerow([s, b["id"], b["name"], b["family"], vals[s][b["id"]]])
# agreement with values coded from the judges' observations
obs = {}
for r in csv.DictReader(open(CD / "site_attribute_values_from_observations.csv")): obs[r["site_id"]] = r
ag = collections.defaultdict(lambda: [0, 0, 0])
for s in sites:
    for b in book:
        o, p = obs.get(s, {}).get(b["id"], ""), vals[s].get(b["id"], "")
        if o and p and p != "unclear": ag[b["id"]][1] += 1; ag[b["id"]][0] += int(o == p)
        if o and p == "unclear": ag[b["id"]][2] += 1
with open(CD / ("coder_agreement.csv" if WHICH == "generated" else f"coder_agreement_{WHICH}.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["attribute_id", "attribute", "family", "n_compared", "agreement", "n_unclear_vs_observed"])
    for b in book: a, n, u = ag[b["id"]]; w.writerow([b["id"], b["name"], b["family"], n, round(a / n, 3) if n else "", u])
tot = sum(v[1] for v in ag.values()); agree = sum(v[0] for v in ag.values()); filled = sum(1 for s in sites for b in book if vals[s].get(b["id"], "") not in ("", "unclear"))
print(f"coded matrix {len(sites)} x {len(book)}: {filled} of {len(sites) * len(book)} cells have a value ({100 * filled / (len(sites) * len(book)):.0f}%); agreement with the observation-derived values: {agree}/{tot} = {100 * agree / max(tot, 1):.0f}%")
