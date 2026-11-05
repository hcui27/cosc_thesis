"""A/B test of judge design on a few sites: arm A = judges compare the original with the generated page (judge.py, existing outputs), arm B = judges only observe the generated page (observe_single.py).
usage: python pipeline/3_annotate/ab_judges.py [--dir data/analysis_ab] [--threshold 0.78]
Reads <dir>/compare/<site>.<model>.json (arm A) and <dir>/observe/<site>.<model>.json (arm B). Offline, uses fastembed BGE-small (same model and cosine threshold as embed_merge.py).
Reports: counts; how much of arm A is about the generated page and how often it is phrased relative to the original; coverage both ways (an observation is covered when another arm has one with cosine >= threshold);
agreement between the two judge models inside each arm; category mix; unmatched examples for reading. Writes <dir>/ab_report.md.
"""
import sys, re, json, glob, os, collections, pathlib
import numpy as np
from fastembed import TextEmbedding
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
D, TH = pathlib.Path(g("--dir", "data/analysis_ab")), float(g("--threshold", 0.78))
emb = TextEmbedding("BAAI/bge-small-en-v1.5")
REL = re.compile(r"\b(original|unlike|whereas|compared|versus|vs\.?|instead of|than (the )?(a|b|original)|side [ab]|[ab] (uses|has|shows|adds|drops|keeps|replaces|is|lacks)|b's|a's)\b", re.I)
sites = sorted({os.path.basename(f).split(".")[0] for f in glob.glob(str(D / "observe/*.json"))}); models = ["claude-sonnet-5-5", "claude-opus-5-5"]
load = lambda p: json.load(open(p)) if os.path.exists(p) else []
E = lambda xs: np.array(list(emb.embed([x["observation"] for x in xs]))) if xs else np.zeros((0, 384))
def cover(src, dst):          # share of src observations with a match in dst
    if len(src) == 0 or len(dst) == 0: return float("nan")
    return float((E(src) @ E(dst).T).max(axis=1).__ge__(TH).mean())
def unmatched(src, dst, k=5):
    if len(src) == 0: return []
    if len(dst) == 0: return src[:k]
    m = (E(src) @ E(dst).T).max(axis=1); return [src[i] for i in np.argsort(m)[:k] if m[i] < TH]
rows, rep, tot = [], [], collections.defaultdict(list)
for s in sites:
    A = {m: load(D / f"compare/{s}.{m}.json") for m in models}; B = {m: load(D / f"observe/{s}.{m}.json") for m in models}
    Agen = {m: [o for o in A[m] if o.get("which_side") in ("B", "both")] for m in models}
    allA = sum(A.values(), []); allB = sum(B.values(), []); allAg = sum(Agen.values(), [])
    r = {"site": s, "A_total": len(allA), "A_generated_side": len(allAg), "A_original_only": sum(o.get("which_side") == "A" for o in allA), "B_total": len(allB),
         "A_gen_relative_phrasing": round(sum(bool(REL.search(o["observation"])) for o in allAg) / max(len(allAg), 1), 3), "B_relative_phrasing": round(sum(bool(REL.search(o["observation"])) for o in allB) / max(len(allB), 1), 3),
         "B_covered_by_A": round(cover(allB, allAg), 3), "A_gen_covered_by_B": round(cover(allAg, allB), 3),
         "A_judge_agree": round(np.nanmean([cover(Agen[models[0]], Agen[models[1]]), cover(Agen[models[1]], Agen[models[0]])]), 3), "B_judge_agree": round(np.nanmean([cover(B[models[0]], B[models[1]]), cover(B[models[1]], B[models[0]])]), 3)}
    rows.append(r)
    for k, v in r.items():
        if k != "site": tot[k].append(v)
    rep += [f"\n## {s}", "Observation-only (B) with no match in comparative generated-side (A):"] + [f"- {o['observation'][:170]}" for o in unmatched(allB, allAg)] + ["Comparative generated-side (A) with no match in observation-only (B):"] + [f"- {o['observation'][:170]}" for o in unmatched(allAg, allB)]
cat = lambda xs: dict(collections.Counter(o.get("category", "") for o in xs).most_common(8))
allA = sum((load(D / f"compare/{s}.{m}.json") for s in sites for m in models), []); allB = sum((load(D / f"observe/{s}.{m}.json") for s in sites for m in models), [])
head = ["# Judge A/B test: compare original vs observe generated page only", f"{len(sites)} sites: {', '.join(sites)}. Models: {', '.join(models)}. Match = BGE-small cosine >= {TH}.\n",
        "| site | A total | A about generated | A original-only | B total | A gen relative phrasing | B relative phrasing | B covered by A | A gen covered by B | A judge agreement | B judge agreement |", "|---|---|---|---|---|---|---|---|---|---|---|"]
head += [f"| {r['site']} | {r['A_total']} | {r['A_generated_side']} | {r['A_original_only']} | {r['B_total']} | {r['A_gen_relative_phrasing']} | {r['B_relative_phrasing']} | {r['B_covered_by_A']} | {r['A_gen_covered_by_B']} | {r['A_judge_agree']} | {r['B_judge_agree']} |" for r in rows]
mean = lambda k: round(float(np.nanmean(tot[k])), 3)
head += [f"| **mean** | {mean('A_total')} | {mean('A_generated_side')} | {mean('A_original_only')} | {mean('B_total')} | {mean('A_gen_relative_phrasing')} | {mean('B_relative_phrasing')} | {mean('B_covered_by_A')} | {mean('A_gen_covered_by_B')} | {mean('A_judge_agree')} | {mean('B_judge_agree')} |",
         f"\nCategory mix, comparative: {cat(allA)}\n\nCategory mix, observation-only: {cat(allB)}", "\n# Unmatched examples (read these)"]
(D / "ab_report.md").write_text("\n".join(head + rep) + "\n"); print("\n".join(head[:12])); print("written", D / "ab_report.md")
