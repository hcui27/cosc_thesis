"""Observation-only arm (data/analysis*) vs comparison-judge arm (arms/compare/data/analysis*) on the SAME 28 generated pages. Offline except the embedding model (fastembed BGE-small).
usage: python pipeline/3_annotate/compare_arms.py [--thr 0.78]
Writes data/analysis_arms/{arms_report.md, attribute_matches.csv}.
Sections: observations (volume, side, relative phrasing, cross-arm coverage) | codebooks (size, matched attributes by embedding of name+definition, unique to each) | value agreement on matched attributes (modal value, band) | seed pertinence/additions.
"""
import csv, json, re, collections, pathlib, sys, numpy as np
from fastembed import TextEmbedding
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
THR = float(g("--thr", 0.78)); A, B = pathlib.Path("data"), pathlib.Path("arms/compare/data"); OUT = A / "analysis_arms"; OUT.mkdir(exist_ok=True)
emb = TextEmbedding("BAAI/bge-small-en-v1.5"); E = lambda t: (lambda m: m / np.linalg.norm(m, axis=1, keepdims=True))(np.array(list(emb.embed(t)), dtype=np.float32))
rd = lambda p: list(csv.DictReader(open(p))); L = []; w = L.append
REL = re.compile(r"\b(side [AB]|\bA\b|\bB\b|original|compared (to|with)|whereas|in contrast|unlike|differs?|instead of|replaces?|drops?|adds?|retains?|than the)\b", re.I)

# ---- observations
oa, ob = rd(A / "analysis/observations.csv"), rd(B / "analysis/observations.csv")
gb = [r for r in ob if r["which_side"] in ("generated", "both")]
w("# Observation-only arm vs comparison-judge arm (same 28 generated pages)\n")
w("## Observations")
w(f"- observation-only: {len(oa)} observations ({len(oa)/28:.0f} per page). comparison: {len(ob)} ({len(ob)/28:.0f} per page); sides {dict(collections.Counter(r['which_side'] for r in ob))}")
w(f"- comparison observations about the ORIGINAL only (never reach the codebook): {sum(r['which_side']=='original' for r in ob)} ({100*sum(r['which_side']=='original' for r in ob)/len(ob):.0f}%)")
w(f"- relative phrasing (mentions side A/B, original, 'whereas', 'instead of' ...): observation-only {100*np.mean([bool(REL.search(r['observation'])) for r in oa]):.0f}%, comparison generated/both {100*np.mean([bool(REL.search(r['observation'])) for r in gb]):.0f}%")
Ea, Eb = E([r["observation"] for r in oa]), E([r["observation"] for r in gb]); sa, sb = np.array([r["site_id"] for r in oa]), np.array([r["site_id"] for r in gb])
def cover(X, Y, sx, sy):
    hit = [(X[i] @ Y[sy == sx[i]].T).max() >= THR if (sy == sx[i]).any() else False for i in range(len(X))]; return 100 * np.mean(hit)
w(f"- cross-arm coverage within the same page (cosine >= {THR}): {cover(Ea, Eb, sa, sb):.0f}% of observation-only observations have a comparison counterpart; {cover(Eb, Ea, sb, sa):.0f}% of comparison generated-side observations have an observation-only counterpart (lowered by relative phrasing)")
for arm, p in (("observation-only", A), ("comparison", B)):
    t = rd(p / "analysis/observations_tiered.csv"); T = collections.Counter(r["tier"] for r in t); w(f"- tiers, {arm}: {dict(sorted(T.items()))}")

# ---- codebooks
ca, cb = json.load(open(A / "analysis/codebook/codebook.json")), json.load(open(B / "analysis/codebook/codebook.json"))
w(f"\n## Codebooks\n- attributes: observation-only {len(ca)}, comparison {len(cb)}; values {sum(len(x['values']) for x in ca)} vs {sum(len(x['values']) for x in cb)}")
txt = lambda c: f"{c['attribute'] if 'attribute' in c else c['name']}: {c.get('definition','')}"
Xa, Xb = E([txt(c) for c in ca]), E([txt(c) for c in cb]); S = Xa @ Xb.T
pairs = [(i, int(S[i].argmax())) for i in range(len(ca)) if S[i].max() >= 0.80 and int(S[:, S[i].argmax()].argmax()) == i]
ma, mb = {i for i, _ in pairs}, {j for _, j in pairs}
nm = lambda c: c.get("attribute", c.get("name"))
w(f"- matched attributes (mutual nearest, cosine >= 0.80 on name+definition): {len(pairs)}; unique to observation-only {len(ca)-len(ma)}; unique to comparison {len(cb)-len(mb)}")
fam = lambda cs, m: dict(sorted(collections.Counter(c["family"] for i, c in enumerate(cs) if i not in m).items()))
w(f"- unique to observation-only by family: {fam(ca, ma)}\n- unique to comparison by family: {fam(cb, mb)}")
w("- examples unique to observation-only: " + "; ".join(nm(ca[i]) for i in sorted(set(range(len(ca))) - ma)[:12]))
w("- examples unique to comparison: " + "; ".join(nm(cb[j]) for j in sorted(set(range(len(cb))) - mb)[:12]))

# ---- value agreement on matched attributes
sa_, sb_ = {r["attribute"]: r for r in rd(A / "analysis/codebook_evidence/analysis/attribute_summary.csv")}, {r["attribute"]: r for r in rd(B / "analysis/codebook_evidence/analysis/attribute_summary.csv")}
rows, agree_band, agree_mod, n = [], 0, 0, 0
for i, j in pairs:
    x, y = sa_.get(nm(ca[i])), sb_.get(nm(cb[j]))
    if not x or not y: continue
    n += 1; ab = x["band"] == y["band"]; agree_band += ab
    rows.append({"obs_attr": nm(ca[i]), "cmp_attr": nm(cb[j]), "cosine": round(float(S[i, j]), 2), "obs_modal": x["modal_value"], "cmp_modal": y["modal_value"], "obs_share": x["modal_share"], "cmp_share": y["modal_share"], "obs_band": x["band"], "cmp_band": y["band"]})
with open(OUT / "attribute_matches.csv", "w", newline="") as f: wr = csv.DictWriter(f, list(rows[0])); wr.writeheader(); wr.writerows(rows)
w(f"\n## Matched attributes: do the arms find the same pages the same way?\n- {n} matched attributes with codes in both; same band (shared/split/varied) {100*agree_band/n:.0f}%; mean abs difference in modal share {np.mean([abs(float(r['obs_share'])-float(r['cmp_share'])) for r in rows]):.2f}")
dist = lambda p: collections.Counter(r["band"] for r in rd(p / "analysis/codebook_evidence/analysis/attribute_summary.csv"))
w(f"- band distribution over ALL attributes: observation-only {dict(dist(A))}, comparison {dict(dist(B))}")

# ---- seed
for arm, p in (("observation-only", A), ("comparison", B)):
    s = rd(p / "analysis_seed/seed_vs_codebook.csv"); rel = collections.Counter(r["relation"] for r in s)
    w(f"- seed relation, {arm}: {dict(rel)}; added (none) share {100*rel['none']/len(s):.0f}%; median presence of added attributes {np.median([float(r['presence_rate']) for r in s if r['relation']=='none']):.2f}")
open(OUT / "arms_report.md", "w").write("\n".join(L)); print("\n".join(L))
