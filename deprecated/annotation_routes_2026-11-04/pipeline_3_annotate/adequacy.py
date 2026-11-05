"""Stage 3b of ANALYSIS_PLAN.md: is the seed catalog adequate? Offline (no LLM). Uses only variation in observations between the seed sites.
usage: python pipeline/3_annotate/adequacy.py [--splits 20] [--perms 300] [--seed 0]
Reads data/analysis/{features_catalog.json, observations_tiered.csv, features/site_*.json, sites_table.csv, detector_agreement.csv (optional)}.
Writes data/analysis/{adequacy_report.md, adequacy_metrics.json, adequacy_splits.csv, discovery_curve.png, recurrence_hist.png}.
Thresholds (decided): plateau = mean new features per added site over the LAST 8 sites < 1; singleton share > 40% of features or > 30% of observations = too concrete;
hold-out coverage >= 80%. Hold-out coverage uses canonical ids assigned once over all sites (a hold-out feature is covered when its id also occurs on a discovery site):
an approximation of per-split re-discovery that can only leak by merging decisions, documented in the report.
"""
import sys, os, csv, json, glob, re, random, itertools, collections, statistics as st, pathlib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SPLITS, PERMS, SEED = int(g("--splits", 20)), int(g("--perms", 300)), int(g("--seed", 0))
OUT = pathlib.Path("data/analysis"); rnd = random.Random(SEED)
cat = json.load(open(OUT / "features_catalog.json")); sites = sorted({s for c in cat for s in c["sites"]})
sites_tab = {r["site_id"]: r for r in csv.DictReader(open(OUT / "sites_table.csv"))}; sites = sorted(sites_tab)  # all seed sites, even ones with few features
fs = {s: {c["id"] for c in cat if s in c["sites"]} for s in sites}
M = {}

# 1. discovery curve
curves = []
for _ in range(PERMS):
    order = sites[:]; rnd.shuffle(order); seen, new = set(), []
    for s in order: new.append(len(fs[s] - seen)); seen |= fs[s]
    curves.append(new)
mean_new = [st.mean(c[i] for c in curves) for i in range(len(sites))]
last8 = st.mean(mean_new[-8:]); M["discovery"] = {"mean_new_per_added_site": [round(x, 2) for x in mean_new], "last8_mean_new": round(last8, 2), "plateau": last8 < 1,
                                                   "total_features": len(cat), "first_site_new": round(mean_new[0], 1)}
plt.figure(figsize=(6, 3.5)); plt.plot(range(1, len(sites) + 1), mean_new, marker="o"); plt.axhline(1, ls="--", c="grey")
plt.xlabel("site added (random order, mean of %d orders)" % PERMS); plt.ylabel("new features contributed"); plt.title("Discovery curve"); plt.tight_layout(); plt.savefig(OUT / "discovery_curve.png", dpi=130); plt.close()

# 2. singleton share (features and observations)
sing = [c for c in cat if c["n_sites"] == 1]; feat_share = len(sing) / len(cat)
tot_obs = unm_obs = 0
for fp in glob.glob(str(OUT / "features" / "site_*.json")):
    d = json.load(open(fp)); covered = {i for f in d["features"] for i in f["items"]}
    for it in d["items"]:
        tot_obs += len(it["members"]); unm_obs += 0 if it["id"] in covered else len(it["members"])
sing_obs = sum(c["n_observations"] for c in sing); obs_share = (sing_obs + unm_obs) / max(tot_obs, 1)
M["singletons"] = {"feature_share": round(feat_share, 3), "observation_share": round(obs_share, 3), "unmapped_observation_share": round(unm_obs / max(tot_obs, 1), 3),
                   "too_concrete": feat_share > 0.40 or obs_share > 0.30}

# 3. recurrence profile
bins = [("1", 1, 1), ("2-3", 2, 3), ("4-9", 4, 9), ("10-19", 10, 19), ("20+", 20, 99)]
prof = {b: sum(lo <= c["n_sites"] <= hi for c in cat) for b, lo, hi in bins}
fam_prof = {fam: {b: sum(lo <= c["n_sites"] <= hi for c in cat if c["family"] == fam) for b, lo, hi in bins} for fam in sorted({c["family"] for c in cat})}
M["recurrence"] = {"overall": prof, "by_family": fam_prof}
plt.figure(figsize=(5, 3.5)); plt.bar(list(prof), list(prof.values())); plt.xlabel("number of sites a feature appears on"); plt.ylabel("features"); plt.title("Recurrence profile"); plt.tight_layout(); plt.savefig(OUT / "recurrence_hist.png", dpi=130); plt.close()

# 4. between-site overlap
jac = lambda a, b: len(fs[a] & fs[b]) / max(len(fs[a] | fs[b]), 1)
pairs = list(itertools.combinations(sites, 2)); J = [jac(a, b) for a, b in pairs]
same = [jac(a, b) for a, b in pairs if sites_tab[a]["category"] == sites_tab[b]["category"]]; diff = [jac(a, b) for a, b in pairs if sites_tab[a]["category"] != sites_tab[b]["category"]]
q = lambda x, p: sorted(x)[int(p * (len(x) - 1))]
M["overlap"] = {"mean": round(st.mean(J), 3), "q25": round(q(J, .25), 3), "median": round(q(J, .5), 3), "q75": round(q(J, .75), 3),
                "same_category_mean": round(st.mean(same), 3) if same else None, "diff_category_mean": round(st.mean(diff), 3), "n_same_category_pairs": len(same)}

# 5. judge consistency by family (share of each judge's observations matched by the other judge)
def fam_of(c):
    c = c.lower()
    for k, v in (("layout", "layout"), ("typo", "typography"), ("color", "color"), ("component", "component"), ("imag", "imagery"), ("copy", "copy"), ("decor", "decoration"), ("effect", "decoration"), ("dom", "semantic_dom"), ("semantic", "semantic_dom"), ("structure", "semantic_dom")):
        if k in c: return v
    return "other"
cons = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for r in csv.DictReader(open(OUT / "observations_tiered.csv")):
    j = "sonnet" if "sonnet" in r["judge"] else "opus"; x = cons[fam_of(r["category"])][j]; x[1] += 1; x[0] += bool(r["matched_with"])
M["judge_consistency"] = {f: {j: round(a / b, 3) for j, (a, b) in d.items() if b} | {"n": sum(b for a, b in d.values())} for f, d in cons.items()}
weak = [f for f, d in M["judge_consistency"].items() if min(d.get("sonnet", 1), d.get("opus", 1)) < 0.6]

# 6. hold-out coverage over repeated 24/4 splits
rows, per_site = [], collections.defaultdict(list)
for k in range(SPLITS):
    order = sites[:]; rnd.shuffle(order); hold, seen_cat = [], set()
    for s in order:
        if len(hold) == 4: break
        if sites_tab[s]["category"] not in seen_cat: hold.append(s); seen_cat.add(sites_tab[s]["category"])
    disc = set(sites) - set(hold); catalog = {c["id"] for c in cat if set(c["sites"]) & disc}
    cov = {h: (len(fs[h] & catalog) / len(fs[h]) if fs[h] else None) for h in hold}
    for h, v in cov.items():
        if v is not None: per_site[h].append(v)
    v = [x for x in cov.values() if x is not None]; rows.append({"split": k, "holdout": ";".join(hold), "coverage_mean": round(st.mean(v), 3), "coverage_min": round(min(v), 3)})
with open(OUT / "adequacy_splits.csv", "w", newline="") as f: w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
cm = [r["coverage_mean"] for r in rows]
M["holdout_coverage"] = {"splits": SPLITS, "mean": round(st.mean(cm), 3), "min": round(min(cm), 3), "max": round(max(cm), 3), "share_of_splits_ge_80": round(sum(x >= .8 for x in cm) / len(cm), 2),
                         "lowest_covered_sites": sorted(((round(st.mean(v), 2), s) for s, v in per_site.items()))[:5], "generalizes": st.mean(cm) >= .8}

# 7. detector agreement (if Stage 4 has run)
da = OUT / "detector_agreement.csv"
if da.exists():
    r = list(csv.DictReader(open(da))); ag = [float(x["agreement"]) for x in r if x["agreement"]]
    M["detector_agreement"] = {"features_compared": len(ag), "mean_agreement": round(st.mean(ag), 3) if ag else None, "low_agreement_features": [x["feature_id"] for x in r if x["agreement"] and float(x["agreement"]) < .7]}
json.dump(M, open(OUT / "adequacy_metrics.json", "w"), indent=1)

# ---- report with the decision-table readout
D, S_, H = M["discovery"], M["singletons"], M["holdout_coverage"]; act = []
if not D["plateau"] and not H["generalizes"]: act.append("Discovery curve still rising AND hold-out coverage low -> catalog incomplete: add seed sites (stratified toward thin categories) or run a second, structured per-site discovery pass.")
elif D["plateau"] and H["generalizes"]: act.append("Plateau and high hold-out coverage -> common features captured: freeze the catalog and move on to detection and prevalence (Stages 4-5).")
else: act.append(f"Mixed signal (plateau={D['plateau']}, hold-out coverage>=80%={H['generalizes']}): treat the catalog as provisional; extend discovery before freezing.")
if S_["too_concrete"]: act.append("High singleton share -> features too concrete: run a merge/abstraction pass by family and define parameterized (valued) features.")
if weak: act.append(f"Low judge consistency in {weak} -> prefer programmatic detectors there or add facts to the judge prompt.")
if M.get("detector_agreement", {}).get("low_agreement_features"): act.append("Low detector agreement on some features -> tighten definitions and relabel a sample.")
unmeasured = [c["id"] + " " + c["name"] for c in cat if c["detector"] != "programmatic"]
rep = ["# Adequacy of the seed feature catalog", f"{len(sites)} seed sites, {len(cat)} canonical features. Hold-out coverage uses ids assigned once over all sites (see script docstring).\n",
       f"## Discovery curve\nMean new features per added site over the last 8 sites: **{D['last8_mean_new']}** (plateau if < 1) -> plateau = **{D['plateau']}**. First site contributes {D['first_site_new']} features. ![curve](discovery_curve.png)\n",
       f"## Singleton share\nFeatures seen on one site only: **{100 * S_['feature_share']:.0f}%** (limit 40%). Observations in singleton features or mapped to no feature: **{100 * S_['observation_share']:.0f}%** (limit 30%; {100 * S_['unmapped_observation_share']:.0f}% mapped to no feature). Too concrete = **{S_['too_concrete']}**.\n",
       "## Recurrence profile (sites per feature)\n" + " | ".join(f"{b}: {n}" for b, n in prof.items()) + "\n\n![recurrence](recurrence_hist.png)\n\nBy family:\n" + "\n".join(f"- {f}: {d}" for f, d in fam_prof.items()) + "\n",
       f"## Between-site overlap (Jaccard of feature sets)\nmean {M['overlap']['mean']}, quartiles {M['overlap']['q25']} / {M['overlap']['median']} / {M['overlap']['q75']}; same-category pairs {M['overlap']['same_category_mean']} (n={M['overlap']['n_same_category_pairs']}) vs different-category {M['overlap']['diff_category_mean']}.\n",
       "## Judge consistency (share of a judge's observations matched by the other)\n" + "\n".join(f"- {f}: {d}" for f, d in M["judge_consistency"].items()) + "\n",
       f"## Hold-out coverage over {SPLITS} repeated 24/4 splits\nmean **{H['mean']}**, range {H['min']}-{H['max']}, {int(100 * H['share_of_splits_ge_80'])}% of splits >= 80%. Lowest-covered sites when held out: {H['lowest_covered_sites']}. Generalizes (mean >= 80%) = **{H['generalizes']}**.\n",
       "## Detector agreement\n" + (str(M["detector_agreement"]) if "detector_agreement" in M else "not available until Stage 4 has run.") + "\n",
       "## Readout (decision table)\n" + "\n".join("- " + a for a in act) + f"\n\n## Features with no programmatic detector ({len(unmeasured)})\nThese need the vision checklist (candidate engineering gaps): " + "; ".join(unmeasured[:40]) + (" ..." if len(unmeasured) > 40 else "") + "\n"]
(OUT / "adequacy_report.md").write_text("\n".join(rep)); print("\n".join(rep[:1] + [f"plateau={D['plateau']} (last8 {D['last8_mean_new']}); singleton features {100 * S_['feature_share']:.0f}%, observations {100 * S_['observation_share']:.0f}%; hold-out coverage mean {H['mean']} ({H['min']}-{H['max']})"] + ["- " + a for a in act]))
