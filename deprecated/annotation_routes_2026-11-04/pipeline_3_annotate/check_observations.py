"""Stage 2 of ANALYSIS_PLAN.md (no human grading): confidence tiers for every judge observation.
usage: python pipeline/3_annotate/check_observations.py [--sites a,b,...] [--model claude-sonnet-5-5] [--workers 3]
Per site, ONE call does two things with the programmatic page facts as ground truth:
  1. agreement: which Sonnet observations and Opus observations make the same substantive point (same trait, same direction)
  2. fact check: observations whose claim the facts can verify are marked supported / contradicted (the rest are left unmarked)
Tiers: A = both judges made the point and no fact contradicts it | B = one judge only, not contradicted | C = contradicted by a fact (drop).
Writes data/analysis/tiering/<site>.json (resumable) and data/analysis/observations_tiered.csv; every call is logged to data/ledger.jsonl.
Needs data/analysis/observations.csv (run collate_sites.py first). Run from the project root.
"""
import sys, os, csv, json, pathlib, collections, concurrent.futures as cf
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from llm import ask_json

g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MODEL, WORKERS = g("--model", "claude-sonnet-5-5"), int(g("--workers", 3))
COMPARE = g("--mode", "single") == "compare"          # compare: judges saw original (A) and generated (B) side by side; single: generated page only
OUT = pathlib.Path("data/analysis"); (OUT / "tiering").mkdir(parents=True, exist_ok=True)
KEYS = ["title", "h1_count", "semantic", "counts", "fonts_by_element_count", "body_font_size", "body_line_height", "h1", "h2", "colors",
        "primary_button", "effects", "layout", "classes", "text_stats", "image_overlaps", "meta_names", "jsonld_blocks", "lang"]

def compact(d):
    o = {k: d.get(k) for k in KEYS}
    o["tag_counts_top"] = dict(sorted(d.get("tag_counts", {}).items(), key=lambda kv: -kv[1])[:25])
    o["heading_outline_first12"] = d.get("heading_outline", [])[:12]; o["n_images"] = len(d.get("images", []))
    return o

def tier_site(site, rows):
    S = [r for r in rows if r["judge"].endswith("sonnet-5-5")]; O = [r for r in rows if r["judge"].endswith("opus-5-5")]
    sid = {r["obs_id"]: f"S{i}" for i, r in enumerate(S)}; oid = {r["obs_id"]: f"O{i}" for i, r in enumerate(O)}
    fmt = lambda R, ids: [{"id": ids[r["obs_id"]], "observation": r["observation"][:300], "evidence": r["evidence"][:160]} for r in R]
    gen = compact(json.load(open(f"data/{site}/generated_cli/r1/free/render/dom.json")))
    facts = {"A_original": compact(json.load(open(f"data/{site}/original/dom.json"))), "B_generated": gen} if COMPARE else {"page": gen}
    who = ("Two judges each compared the same two renderings of a web page: side A (the original) and side B (an AI-generated page). " if COMPARE else
           "Two judges each described the same AI-generated web page, without seeing any other page. ")
    prompt = (who + "Below: the observations of judge S and judge O, and programmatic FACTS "
              "measured from the page's DOM (ground truth).\nTask 1 (agreement): for each S observation list the O observations that make the SAME substantive point "
              "(same trait of the pages, same direction; different wording is fine, merely related is not). Skip S items with no match.\n"
              "Task 2 (fact check): for every observation (S or O) whose claim the FACTS can verify (numbers, counts, tags, fonts, colors, radii, shadows, titles, sizes), "
              "give verdict 'supported' or 'contradicted' and a reason of at most 12 words citing the fact. Do NOT list observations the facts cannot verify.\n"
              'Final answer ONLY JSON: {"matches": [{"s": "S3", "o": ["O5"]}], "fact_checks": [{"id": "S7", "verdict": "contradicted", "why": "..."}]}\n\n'
              f"FACTS:\n{json.dumps(facts, ensure_ascii=False)}\n\nS OBSERVATIONS:\n{json.dumps(fmt(S, sid), ensure_ascii=False)}\n\nO OBSERVATIONS:\n{json.dumps(fmt(O, oid), ensure_ascii=False)}")
    res = ask_json(prompt, MODEL, "obs_tiering", site=site, n_obs=len(S) + len(O))
    json.dump({"S": sid, "O": oid, "result": res}, open(OUT / "tiering" / f"{site}.json", "w"), indent=1)

obs = list(csv.DictReader(open(OUT / "observations.csv")))
by_site = collections.defaultdict(list)
for r in obs: by_site[r["site_id"]].append(r)
sites = g("--sites", "").split(",") if g("--sites", "") else sorted(by_site)
todo = [s for s in sites if not (OUT / "tiering" / f"{s}.json").exists()]
print(f"{len(todo)} sites to tier ({len(sites) - len(todo)} cached)", flush=True)
with cf.ThreadPoolExecutor(WORKERS) as ex:
    for s, f in zip(todo, [ex.submit(tier_site, s, by_site[s]) for s in todo]):
        try: f.result(); print("  tiered", s, flush=True)
        except Exception as e: print("  FAILED", s, type(e).__name__, str(e)[:120], flush=True)

# ---- combine into tiers (only for sites that have a tiering file)
out, bad = [], 0
for s in sorted(by_site):
    fp = OUT / "tiering" / f"{s}.json"
    if not fp.exists(): continue
    d = json.load(open(fp)); res = d["result"]; sid, oid = d["S"], d["O"]; inv = {v: k for k, v in {**sid, **oid}.items()}
    match, fact = collections.defaultdict(set), {}
    for m in res.get("matches", []):
        for o in m.get("o", []):
            if m.get("s") in inv and o in inv: match[inv[m["s"]]].add(inv[o]); match[inv[o]].add(inv[m["s"]])
    for c in res.get("fact_checks", []):
        if c.get("id") in inv: fact[inv[c["id"]]] = (c.get("verdict", ""), c.get("why", ""))
    for r in by_site[s]:
        v, why = fact.get(r["obs_id"], ("", ""))
        tier = "C" if v == "contradicted" else ("A" if match.get(r["obs_id"]) else "B")
        out.append({**r, "tier": tier, "matched_with": ";".join(sorted(match.get(r["obs_id"], []))), "fact_verdict": v, "fact_why": why})
if out:
    with open(OUT / "observations_tiered.csv", "w", newline="") as f: w = csv.DictWriter(f, list(out[0])); w.writeheader(); w.writerows(out)
    n = len(out); T = collections.Counter(o["tier"] for o in out)
    print(f"\n{n} observations tiered across {len({o['site_id'] for o in out})} sites: {dict(sorted(T.items()))}")
    for j in sorted({o["judge"] for o in out}): print(f"  {j}: {dict(sorted(collections.Counter(o['tier'] for o in out if o['judge'] == j).items()))}")
    chk = [o for o in out if o["fact_verdict"]]; print(f"  fact-checkable: {len(chk)} ({100 * len(chk) / n:.0f}%), contradicted {sum(o['fact_verdict'] == 'contradicted' for o in chk)}")
