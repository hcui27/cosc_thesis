"""Variation analysis on the attribute-and-value matrix (offline, no LLM): the value distribution of every attribute across the 28 pages.
usage: python pipeline/3_annotate/analyze_attributes.py [--shared 0.75] [--split 0.50] [--min-coded 15] [--codes-dir data/analysis/codebook_evidence] [--out <dir>]
Per attribute: how many pages could be coded, the share of each value, the modal value and its share (how shared the choice is), and normalised entropy (0 = every page picks the same value, 1 = values spread evenly).
Bands by modal share: shared >= --shared, split >= --split, varied below. Also: how the pairwise agreement between pages is distributed (its SD versus a permutation null: do some pages resemble each other more than independent coding would make them?; the MEAN agreement cannot be tested this way because it depends only on the value counts),
and a split of modal values into presence vs absence/other (a feature absent on every page is a shared ABSENCE, not a shared feature),
and, if page_codes_original.csv exists, per attribute the modal value for the originals and whether the generated modal value differs (lift-like contrast).
Writes data/analysis/codebook/{attribute_summary.csv, value_distribution.csv, attribute_report.md, attribute_modal_share.png}.
"""
import sys, os, csv, re, json, math, itertools, collections, pathlib
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SH, SP, MINC = float(g("--shared", 0.75)), float(g("--split", 0.50)), int(g("--min-coded", 15))
BOOK = pathlib.Path("data/analysis/codebook"); book = {b["id"]: b for b in json.load(open(BOOK / "codebook.json"))}
CD = pathlib.Path(g("--codes-dir", "data/analysis/codebook")); OUTD = pathlib.Path(g("--out", str(CD))); OUTD.mkdir(parents=True, exist_ok=True)   # --codes-dir: where page_codes_generated.csv and coder_agreement.csv live (e.g. data/analysis/codebook_evidence)
def read(p):
    rows = list(csv.DictReader(open(p))); return {r["site_id"]: {k: v for k, v in r.items() if k != "site_id"} for r in rows}
gen = read(CD / "page_codes_generated.csv"); sites = sorted(gen); orig = read(BOOK / "page_codes_original.csv") if (BOOK / "page_codes_original.csv").exists() else None
def dist(M, aid):
    v = [M[s][aid] for s in M if M[s].get(aid) not in ("", None, "unclear")]; return collections.Counter(v), len(v)
ABSENT = re.compile(r"\b(none|absent|not present|not used|not applicable|other|missing|without|no [a-z]+)\b|^no[_ ]", re.I)  # heuristic: modal value that says the feature is not there
rows, long = [], []
for aid, b in book.items():
    c, n = dist(gen, aid)
    if n == 0: continue
    mv, mc = c.most_common(1)[0]; k = len(c); H = -sum(x / n * math.log(x / n) for x in c.values()); Hn = H / math.log(k) if k > 1 else 0.0
    share = mc / n; band = "shared" if share >= SH else "split" if share >= SP else "varied"; row = {"attribute_id": aid, "attribute": b["name"], "family": b["family"], "n_coded": n, "n_values_used": k, "modal_value": mv,
        "modal_share": round(share, 3), "entropy_norm": round(Hn, 3), "band": band, "modal_kind": "absence_or_other" if ABSENT.search(mv.replace("_", " ")) else "presence", "n_sites_mentioning": b["n_sites_mentioning"]}
    if orig is not None:
        co, no = dist(orig, aid)
        if no >= MINC: row["original_modal"] = co.most_common(1)[0][0]; row["original_modal_share"] = round(co.most_common(1)[0][1] / no, 3); row["modal_differs_from_original"] = int(row["original_modal"] != mv)
    rows.append(row)
    for val, x in c.most_common(): long.append({"attribute_id": aid, "attribute": b["name"], "value": val, "count": x, "share": round(x / n, 3), "n_coded": n})
rows = [r for r in rows if r["n_coded"] >= MINC]; rows.sort(key=lambda r: (-r["modal_share"], r["attribute"]))
for name, data in (("attribute_summary.csv", rows), ("value_distribution.csv", long)):
    with open(OUTD / name, "w", newline="") as f: w = csv.DictWriter(f, sorted({k for r in data for k in r}, key=lambda k: list(data[0]).index(k) if k in data[0] else 99)); w.writeheader(); w.writerows(data)
# pairwise agreement between pages: the mean is fixed by the value counts (so it is only descriptive); the SD across page pairs tests for structure (clusters of similar pages)
ids = [r["attribute_id"] for r in rows]; M = np.array([[gen[s].get(a, "") for a in ids] for s in sites], dtype=object)
def pair_agreements(Mx):
    out = []
    for i, j in itertools.combinations(range(len(sites)), 2):
        ok = [(Mx[i, k], Mx[j, k]) for k in range(len(ids)) if Mx[i, k] not in ("", "unclear") and Mx[j, k] not in ("", "unclear")]; out.append(sum(a == b for a, b in ok) / max(len(ok), 1))
    return np.array(out)
pa = pair_agreements(M); obs_mean, obs_sd = pa.mean(), pa.std(); rng = np.random.default_rng(0); null_sd = []
for _ in range(200):
    P = M.copy()
    for k in range(len(ids)): P[:, k] = rng.permutation(P[:, k])
    null_sd.append(pair_agreements(P).std())
bands = collections.Counter(r["band"] for r in rows); fam = collections.defaultdict(collections.Counter)
for r in rows: fam[r["family"]][r["band"]] += 1
# figure
top = [x for x in rows if x['modal_kind'] == 'presence'][:30]; plt.figure(figsize=(8, 8)); plt.barh([f"{r['attribute'][:42]} = {r['modal_value'][:24]}" for r in top][::-1], [r["modal_share"] for r in top][::-1]); plt.axvline(SH, ls="--", c="grey")
plt.xlabel("share of pages choosing the modal value"); plt.title("Most shared attribute values (generated pages)"); plt.tight_layout(); plt.savefig(OUTD / "attribute_modal_share.png", dpi=130); plt.close()
rep = [f"# Attribute-value variation across {len(sites)} generated pages", f"{len(rows)} attributes coded on at least {MINC} pages. Bands by modal-value share: shared (>= {SH}) {bands['shared']}, split ({SP}-{SH}) {bands['split']}, varied (< {SP}) {bands['varied']}.\n",
       f"Pairwise agreement between pages over all attributes: mean **{obs_mean:.3f}** (descriptive only: it equals what independent coding with the same value frequencies would give, so it measures how concentrated the choices are, not clustering). "
       f"Spread across page pairs: SD {obs_sd:.4f} vs permutation null {np.mean(null_sd):.4f} (95% of nulls {np.percentile(null_sd, 2.5):.4f}-{np.percentile(null_sd, 97.5):.4f}): "
       f"{'some pages resemble each other MORE than independent coding would give (structure / clusters)' if obs_sd > np.percentile(null_sd, 97.5) else 'no pair-level structure beyond what independent coding gives'}.\n",
       f"By modal value type: shared presence (modal share >= {SH}, a feature is there) {sum(r['band'] == 'shared' and r['modal_kind'] == 'presence' for r in rows)}; shared absence/other (the modal value says the feature is absent or not applicable) {sum(r['band'] == 'shared' and r['modal_kind'] == 'absence_or_other' for r in rows)}.\n",
       "## Bands by family\n" + "\n".join(f"- {f}: {dict(c)}" for f, c in sorted(fam.items())) + "\n", "## Most shared PRESENT values (modal share, modal value is not an absence/other value)\n| attribute | modal value | share | coded | normalised entropy |\n|---|---|---|---|---|\n" +
       "\n".join(f"| {r['attribute']} | {r['modal_value']} | {r['modal_share']} | {r['n_coded']} | {r['entropy_norm']} |" for r in [x for x in rows if x['modal_kind'] == 'presence'][:30]) + "\n\n![top](attribute_modal_share.png)\n",
       "## Most varied attributes (lowest modal share)\n| attribute | modal value | share | values used |\n|---|---|---|---|\n" + "\n".join(f"| {r['attribute']} | {r['modal_value']} | {r['modal_share']} | {r['n_values_used']} |" for r in rows[::-1][:15]) + "\n"]
if orig is not None:
    dif = [r for r in rows if r.get("modal_differs_from_original") == 1]; rep.append(f"## Against the originals\n{len(dif)} of {sum('modal_differs_from_original' in r for r in rows)} comparable attributes have a different modal value in the generated pages than in the originals.\n")
else: rep.append("## Against the originals\nNot computed: run code_pages.py --which original (about the same cost as the generated run).\n")
ca = list(csv.DictReader(open(CD / "coder_agreement.csv"))); tot = sum(int(r["n_compared"]) for r in ca); agr = sum(float(r["agreement"]) * int(r["n_compared"]) for r in ca if r["agreement"])
fa = collections.defaultdict(lambda: [0, 0])
for r in ca:
    if r["agreement"]: fa[r["family"]][0] += float(r["agreement"]) * int(r["n_compared"]); fa[r["family"]][1] += int(r["n_compared"])
rep.append(f"## Coder reliability (vision coder vs values coded from the judges' observations)\nOverall {100 * agr / tot:.0f}% over {tot} comparisons; by family: " + ", ".join(f"{k} {100 * a / b:.0f}%" for k, (a, b) in sorted(fa.items())) + ". Neither side is ground truth.\n")
(OUTD / "attribute_report.md").write_text("\n".join(rep)); print("\n".join(rep[:4]))
print("Top shared present values: " + "; ".join(f"{r['attribute']}={r['modal_value']} ({r['modal_share']})" for r in [x for x in rows if x['modal_kind'] == 'presence'][:10]))
