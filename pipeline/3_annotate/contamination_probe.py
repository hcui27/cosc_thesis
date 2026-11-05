"""Stage 6 (validity) of ANALYSIS_PLAN.md: could the generator have memorised these sites? LATER item, built but not run by default.
usage: python pipeline/3_annotate/contamination_probe.py [--sites a,b] [--model claude-sonnet-5-5]
For each site the model sees ONLY the sanitized prompt copy (data/<site>/prompt/copy.md, the same text the generator got), with no tools, and is asked which website it is.
A hit = it names the site's real domain. Writes data/analysis/contamination_probe.csv and prints the hit rate. One call per site (about $0.03 each).
"""
import sys, os, csv, json, re, pathlib, urllib.parse, concurrent.futures as cf
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from llm import ask_json

g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MODEL = g("--model", "claude-sonnet-5-5"); OUT = pathlib.Path("data/analysis")
rows = list(csv.DictReader(open("data/sites.csv"))); want = [s for s in g("--sites", "").split(",") if s]
if want: rows = [r for r in rows if r["site_id"] in want]
dom = lambda u: urllib.parse.urlparse(u).netloc.lower().removeprefix("www.")

def probe(r):
    copy = (pathlib.Path("data") / r["site_id"] / "prompt/copy.md").read_text()[:6000]
    prompt = ("Below is the text of a website's homepage (markdown). Which website is it? Answer with its domain if you recognise it, otherwise 'unknown'. Do not guess from the generic topic alone; "
              'only name a domain if specific wording, names or details identify it. Final answer ONLY JSON: {"domain": str, "confidence": number 0-1, "clue": str (at most 15 words)}\n\n' + copy)
    res = ask_json(prompt, MODEL, "contamination_probe", site=r["site_id"]); said = dom(str(res.get("domain", ""))) if res.get("domain", "unknown") != "unknown" else "unknown"
    true = dom(r["url"]); hit = said != "unknown" and (said == true or said.endswith("." + true) or true.endswith("." + said))
    return {"site_id": r["site_id"], "category": r["category"], "rank": r["rank"], "true_domain": true, "model_said": said, "confidence": res.get("confidence", ""), "clue": res.get("clue", ""), "hit": int(hit)}

with cf.ThreadPoolExecutor(3) as ex: out = list(ex.map(probe, rows))
with open(OUT / "contamination_probe.csv", "w", newline="") as f: w = csv.DictWriter(f, list(out[0])); w.writeheader(); w.writerows(out)
print(f"{sum(o['hit'] for o in out)}/{len(out)} sites recognised from copy alone; named a different domain: {sum(1 for o in out if o['model_said'] not in ('unknown', o['true_domain']) and not o['hit'])}")
