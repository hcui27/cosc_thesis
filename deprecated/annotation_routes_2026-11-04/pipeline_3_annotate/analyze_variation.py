"""Stage 5 of ANALYSIS_PLAN.md: how much do the generated pages vary, and which features are shared? Offline (no LLM).
usage: python pipeline/3_annotate/analyze_variation.py
In scope now: (1) prevalence of every catalog feature with Wilson 95% intervals; (4) homogenization (similarity among generated pages, and spread in measured style vs the originals).
Also computed because they need no new data: (3) paired original-vs-generated comparisons of measurements, (5) inheritance vs invention, (6) drivers of variation.
(2) lift vs the originals runs only if data/analysis/feature_matrix_original.csv exists (detect_features.py --which original). (7) run-to-run noise needs repeat runs: not computed.
Reads data/analysis/{feature_matrix_generated.csv, features_catalog.json, sites_table.csv}; originals' and generated pages' dom.json/text.txt for measurements.
Writes data/analysis/variation/*: prevalence.csv, similarity_heatmap.png, similarity_mds.png, paired_measurements.csv, inheritance.csv, drivers.csv, [lift.csv], variation_report.md.
"""
import sys, os, csv, json, math, itertools, collections, statistics as st, pathlib
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
import numpy as np
from scipy import stats
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import measurements as M

OUT = pathlib.Path("data/analysis"); VD = OUT / "variation"; VD.mkdir(exist_ok=True)
cat = json.load(open(OUT / "features_catalog.json")); cmap = {c["id"]: c for c in cat}
tab = {r["site_id"]: r for r in csv.DictReader(open(OUT / "sites_table.csv"))}; sites = sorted(tab)
def read_matrix(p):
    rows = list(csv.DictReader(open(p))); return {r["site_id"]: {k: (None if v == "" else int(float(v))) for k, v in r.items() if k != "site_id"} for r in rows}
gen = read_matrix(OUT / "feature_matrix_generated.csv"); fids = [c["id"] for c in cat]

def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return (max(0, c - h), min(1, c + h))
band = lambda p: "universal" if p >= .9 else "common" if p >= .5 else "occasional" if p >= .2 else "rare"

# ---- (1) prevalence
prev = []
for f in fids:
    v = [gen[s][f] for s in sites if gen[s].get(f) is not None]; k, n = sum(v), len(v); lo, hi = wilson(k, n)
    prev.append({"feature_id": f, "family": cmap[f]["family"], "name": cmap[f]["name"], "detector": cmap[f]["detector"], "n_known": n, "n_present": k,
                 "prevalence": round(k / n, 3) if n else "", "ci_low": round(lo, 3) if lo is not None else "", "ci_high": round(hi, 3) if hi is not None else "", "band": band(k / n) if n else "",
                 "discovery_sites_mentioning": cmap[f]["n_sites"]})
prev.sort(key=lambda r: -(r["prevalence"] or 0))
with open(VD / "prevalence.csv", "w", newline="") as f: w = csv.DictWriter(f, list(prev[0])); w.writeheader(); w.writerows(prev)
bands = collections.Counter(r["band"] for r in prev)

# ---- (4) homogenization on the feature matrix
def vec(s): return np.array([1 if gen[s].get(f) == 1 else 0 for f in fids])
V = {s: vec(s) for s in sites}
def jac(a, b): u = (V[a] | V[b]).sum(); return (V[a] & V[b]).sum() / u if u else 0
Jm = np.array([[jac(a, b) if a != b else 1.0 for b in sites] for a in sites]); pairs = list(itertools.combinations(range(len(sites)), 2))
same = [Jm[i, j] for i, j in pairs if tab[sites[i]]["category"] == tab[sites[j]]["category"]]; diff = [Jm[i, j] for i, j in pairs if tab[sites[i]]["category"] != tab[sites[j]]["category"]]
D = 1 - Jm; np.fill_diagonal(D, 0); Z = linkage(squareform(D, checks=False), "average"); order = dendrogram(Z, no_plot=True)["leaves"]
fig, ax = plt.subplots(figsize=(9, 8)); im = ax.imshow(Jm[np.ix_(order, order)], cmap="viridis"); ax.set_xticks(range(len(sites))); ax.set_yticks(range(len(sites)))
lab = [f"{sites[i][:22]} ({tab[sites[i]]['category'][:10]})" for i in order]; ax.set_xticklabels(lab, rotation=90, fontsize=6); ax.set_yticklabels(lab, fontsize=6); plt.colorbar(im, label="Jaccard similarity of present features")
plt.title("Similarity of generated pages (clustered)"); plt.tight_layout(); plt.savefig(VD / "similarity_heatmap.png", dpi=140); plt.close()
from sklearn.manifold import MDS
xy = MDS(n_components=2, dissimilarity="precomputed", random_state=0, init="random", n_init=4).fit_transform(D); cats = sorted({tab[s]["category"] for s in sites})
plt.figure(figsize=(8, 6)); cm = plt.get_cmap("tab20")
for k, c in enumerate(cats):
    idx = [i for i, s in enumerate(sites) if tab[s]["category"] == c]; plt.scatter(xy[idx, 0], xy[idx, 1], label=c, color=cm(k % 20))
plt.legend(fontsize=6, loc="best"); plt.title("2-D embedding of generated pages (feature similarity)"); plt.tight_layout(); plt.savefig(VD / "similarity_mds.png", dpi=140); plt.close()

# ---- measurements for originals and generated pages (free): homogenization in style space, paired comparisons, inheritance
def meas(path):
    d = json.load(open(path / "dom.json")); t = path / "text.txt"; return M.compute(d, t.read_text() if t.exists() else None)
mo = {s: meas(pathlib.Path(f"data/{s}/original")) for s in sites}; mg = {s: meas(pathlib.Path(f"data/{s}/generated_cli/r1/free/render")) for s in sites}
STYLE = ["radius_round_share", "shadow_share", "gradient_count", "h1_size_px", "body_size_px", "font_family_count", "saturated_bg_colors", "body_bg_lightness", "text_color_lightness",
         "tailwind_like_fraction", "semantic_tag_count", "transition_count"]
def spread(mm):
    X = np.array([[mm[s][k] if mm[s][k] is not None else np.nan for k in STYLE] for s in sites], dtype=float); both = np.array([[mo[s][k] if mo[s][k] is not None else np.nan for k in STYLE] for s in sites], dtype=float)
    allx = np.vstack([X, both]); mu, sd = np.nanmean(allx, 0), np.nanstd(allx, 0) + 1e-9; Zs = np.nan_to_num((X - mu) / sd)       # common scaling so original and generated are comparable
    d = [np.linalg.norm(Zs[i] - Zs[j]) for i, j in itertools.combinations(range(len(sites)), 2)]; return st.mean(d), Zs
sp_g, Zg = spread(mg); sp_o, Zo = spread(mo)
rng = np.random.default_rng(0); boots = []
for _ in range(2000):
    idx = rng.integers(0, len(sites), len(sites)); a = [np.linalg.norm(Zg[i] - Zg[j]) for i, j in itertools.combinations(idx, 2) if i != j]; b = [np.linalg.norm(Zo[i] - Zo[j]) for i, j in itertools.combinations(idx, 2) if i != j]
    boots.append(st.mean(a) - st.mean(b))
homog = {"mean_pairwise_distance_generated": round(sp_g, 3), "mean_pairwise_distance_original": round(sp_o, 3), "diff_gen_minus_orig": round(sp_g - sp_o, 3),
         "bootstrap_95ci": [round(float(np.percentile(boots, 2.5)), 3), round(float(np.percentile(boots, 97.5)), 3)]}

paired = []                                                                                  # (3)
for k in M.KEYS:
    a = [(mo[s][k], mg[s][k]) for s in sites if mo[s][k] is not None and mg[s][k] is not None]
    if len(a) < 10: continue
    x, y = np.array([p[0] for p in a], float), np.array([p[1] for p in a], float); d = y - x
    if np.allclose(d, 0): p_, r = 1.0, 0.0
    else:
        try: p_ = float(stats.wilcoxon(x, y).pvalue)
        except Exception: p_ = float("nan")
        rk = stats.rankdata(abs(d[d != 0])); r = float((rk[d[d != 0] > 0].sum() - rk[d[d != 0] < 0].sum()) / rk.sum())
    paired.append({"measurement": k, "n": len(a), "median_original": round(float(np.median(x)), 3), "median_generated": round(float(np.median(y)), 3), "median_diff": round(float(np.median(d)), 3), "rank_biserial": round(r, 3), "p_wilcoxon": p_})
ps = sorted((r["p_wilcoxon"], i) for i, r in enumerate(paired) if r["p_wilcoxon"] == r["p_wilcoxon"]); m = len(ps)
for rank, (p_, i) in enumerate(ps, 1): paired[i]["q_bh"] = min(1.0, p_ * m / rank)
for r in paired: r["q_bh"] = round(r.get("q_bh", float("nan")), 4); r["p_wilcoxon"] = round(r["p_wilcoxon"], 4)
paired.sort(key=lambda r: r["q_bh"])
with open(VD / "paired_measurements.csv", "w", newline="") as f: w = csv.DictWriter(f, list(paired[0])); w.writeheader(); w.writerows(paired)

inh = []; hue = lambda a, b: min(abs(a - b), 360 - abs(a - b))                                 # (5)
for s in sites:
    inh.append({"site_id": s, "accent_hue_diff_deg": round(hue(mo[s]["accent_hue"], mg[s]["accent_hue"]), 1) if mo[s]["accent_hue"] is not None and mg[s]["accent_hue"] is not None else "",
                "body_bg_lightness_diff": round(abs(mo[s]["body_bg_lightness"] - mg[s]["body_bg_lightness"]), 3) if mo[s]["body_bg_lightness"] is not None and mg[s]["body_bg_lightness"] is not None else "",
                "h1_size_ratio": round(mg[s]["h1_size_px"] / mo[s]["h1_size_px"], 2) if mo[s]["h1_size_px"] and mg[s]["h1_size_px"] else "",
                "page_height_ratio": round(mg[s]["page_height"] / mo[s]["page_height"], 2) if mo[s]["page_height"] and mg[s]["page_height"] else ""})
with open(VD / "inheritance.csv", "w", newline="") as f: w = csv.DictWriter(f, list(inh[0])); w.writeheader(); w.writerows(inh)
hd = [r["accent_hue_diff_deg"] for r in inh if r["accent_hue_diff_deg"] != ""]
gh = [mg[s]["accent_hue"] for s in sites if mg[s]["accent_hue"] is not None]; oh = [mo[s]["accent_hue"] for s in sites if mo[s]["accent_hue"] is not None]
perm = [st.median(hue(a, b) for a, b in zip(gh, rng.permutation(oh)[:len(gh)])) for _ in range(2000)] if len(gh) >= 8 and len(oh) >= 8 else []
inh_s = {"n_hue_pairs": len(hd), "median_accent_hue_diff_deg": round(st.median(hd), 1) if hd else None, "chance_median_deg": round(float(np.median(perm)), 1) if perm else None,
         "p_closer_than_chance": round(float(np.mean([p <= st.median(hd) for p in perm])), 3) if perm and hd else None,
         "spearman_body_bg_lightness": [round(float(x), 3) for x in stats.spearmanr([mo[s]["body_bg_lightness"] for s in sites if mo[s]["body_bg_lightness"] is not None and mg[s]["body_bg_lightness"] is not None],
                                                                                   [mg[s]["body_bg_lightness"] for s in sites if mo[s]["body_bg_lightness"] is not None and mg[s]["body_bg_lightness"] is not None])]}

drv = []                                                                                     # (6)
nfeat = {s: sum(1 for f in fids if gen[s].get(f) == 1) for s in sites}
for name, vals in (("copy_words", [float(tab[s]["copy_words"]) for s in sites]), ("images_in_prompt", [float(tab[s]["images"]) for s in sites]),
                   ("original_page_height", [float(tab[s]["orig_page_height"]) for s in sites])):
    r, p_ = stats.spearmanr(vals, [nfeat[s] for s in sites]); drv.append({"driver": name, "target": "number of features present", "spearman_rho": round(float(r), 3), "p": round(float(p_), 4)})
groups = collections.defaultdict(list)
for s in sites: groups[tab[s]["category"]].append(nfeat[s])
kw = stats.kruskal(*[g for g in groups.values() if len(g) >= 1]) if len(groups) > 1 else None
drv.append({"driver": "category (14 groups of 1-3 sites; descriptive only)", "target": "number of features present", "spearman_rho": "", "p": round(float(kw.pvalue), 4) if kw else ""})
with open(VD / "drivers.csv", "w", newline="") as f: w = csv.DictWriter(f, list(drv[0])); w.writeheader(); w.writerows(drv)

lift_note = "not computed (no original-page feature matrix yet: run detect_features.py --which original)"                  # (2)
if (OUT / "feature_matrix_original.csv").exists():
    orig = read_matrix(OUT / "feature_matrix_original.csv"); lift = []
    for r in prev:
        f = r["feature_id"]; o = [orig[s][f] for s in sites if orig.get(s, {}).get(f) is not None]
        if o and r["prevalence"] != "": lift.append({"feature_id": f, "name": r["name"], "prev_generated": r["prevalence"], "prev_original": round(sum(o) / len(o), 3), "lift": round(r["prevalence"] - sum(o) / len(o), 3)})
    lift.sort(key=lambda x: -x["lift"])
    with open(VD / "lift.csv", "w", newline="") as f: w = csv.DictWriter(f, list(lift[0])); w.writeheader(); w.writerows(lift)
    lift_note = f"lift.csv written ({len(lift)} features); top: " + "; ".join(f"{x['name']} (+{x['lift']})" for x in lift[:5])

# ---- report
top = [f"| {r['name']} | {r['family']} | {r['n_present']}/{r['n_known']} | {r['prevalence']} ({r['ci_low']}-{r['ci_high']}) | {r['band']} |" for r in prev[:25]]
rep = ["# Variation among the generated pages (28 seed sites)", f"Features in the catalog: {len(cat)}. Prevalence bands: {dict(bands)}.\n",
       "## (1) Most shared features (prevalence with Wilson 95% interval)\n| feature | family | present/known | prevalence | band |\n|---|---|---|---|---|\n" + "\n".join(top) + "\n\nFull table: prevalence.csv.\n",
       f"## (4) Homogenization\nJaccard similarity of present features between generated pages: mean {np.mean(Jm[np.triu_indices(len(sites), 1)]):.3f}; same-category pairs {np.mean(same):.3f} (n={len(same)}) vs different-category {np.mean(diff):.3f}. "
       f"Spread in measured style (z-scored measurements, mean pairwise distance): generated {homog['mean_pairwise_distance_generated']} vs originals {homog['mean_pairwise_distance_original']}; difference {homog['diff_gen_minus_orig']} (bootstrap 95% CI {homog['bootstrap_95ci']}); a negative difference with an interval below 0 means the generated pages are MORE alike than the originals.\n\n![heatmap](similarity_heatmap.png) ![mds](similarity_mds.png)\n",
       "## (3) Paired original vs generated (measurements; Wilcoxon, BH-adjusted q)\n" + "\n".join(f"- {r['measurement']}: original median {r['median_original']} -> generated {r['median_generated']} (diff {r['median_diff']}, rank-biserial {r['rank_biserial']}, q={r['q_bh']})" for r in paired[:12]) + "\n",
       f"## (5) Inheritance vs invention\n{inh_s}\n", "## (6) Drivers of variation (descriptive; ~2 sites per category)\n" + "\n".join(f"- {r['driver']}: rho {r['spearman_rho']}, p {r['p']}" for r in drv) + "\n",
       f"## (2) Lift vs originals\n{lift_note}\n", "## (7) Run-to-run noise\nNot computed: needs repeat generations (one run per site so far).\n"]
(VD / "variation_report.md").write_text("\n".join(rep))
print(f"prevalence bands {dict(bands)}; mean Jaccard {np.mean(Jm[np.triu_indices(len(sites), 1)]):.3f} (same-cat {np.mean(same):.3f} vs diff-cat {np.mean(diff):.3f}); style spread gen {sp_g:.2f} vs orig {sp_o:.2f}, diff CI {homog['bootstrap_95ci']}")
