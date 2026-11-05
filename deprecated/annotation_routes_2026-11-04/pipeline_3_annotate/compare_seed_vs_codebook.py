"""Compare the closed SEED list (external glossaries) with our self-generated CODEBOOK on the same pages. Nothing is culled; this only measures.
usage: python pipeline/3_annotate/compare_seed_vs_codebook.py [--model claude-sonnet-5-5]
Inputs: seed_attributes/seed_v1.csv, data/analysis_seed/corroboration_summary.csv (seed_pilot.py: seed items matched to the JUDGES' observations; "present" below means mentioned by the judges, not coded from the page), data/analysis/codebook/codebook.json and
data/analysis/codebook_evidence/{page_codes_generated.csv, analysis/attribute_summary.csv} (build_codebook.py, code_pages_evidence.py, analyze_attributes.py).
Step 1 (one or two LLM calls, cached in data/analysis_seed/codebook_to_seed.json): for every codebook attribute, is it ABOUT a seed item?
   relation = "is_item" (it is essentially the presence or kind of that component/section), "property_of_item" (a style or variant dimension of that component/section), or "none" (not about any seed item).
   "none" = attributes the codebook ADDED that the open seed list does not have.
Step 2 (offline): how many seed items were pertinent (present on >= 1 / >= 3 / half of the pages), how many codebook attributes were added (relation none), by family; and the distributions to compare:
   prevalence of seed items vs presence rate of codebook attributes (share of pages where the attribute has a real, non-absence value), split by relation; plus seed items the codebook never mentions.
Writes data/analysis_seed/{codebook_to_seed.json, seed_vs_codebook.md, seed_vs_codebook.csv, seed_vs_codebook.png}.
"""
import sys, re, csv, json, collections, pathlib
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SEEDV = g("--seed", "v1_1"); SUF = "" if SEEDV == "v1_1" else "_" + SEEDV; MODEL = g("--model", "claude-sonnet-5-5"); OUT = pathlib.Path("data/analysis_seed"); CE = pathlib.Path("data/analysis/codebook_evidence")
seed = list(csv.DictReader(open(f"seed_attributes/seed_{SEEDV}.csv")))      # v1.1: duplicate names merged (merges_v1_1.csv)
MERGE = {r["from_item"]: r["into_item"] for r in csv.DictReader(open("seed_attributes/merges_v1_1.csv"))} if SEEDV == "v1_1" else {}; book = json.load(open("data/analysis/codebook/codebook.json"))
summ = {r["item"]: {**r, "pages_present": r["pages_mentioned"], "pages_coded": r["pages"]} for r in csv.DictReader(open(OUT / f"corroboration_summary{SUF}.csv"))}
fp = OUT / f"codebook_to_seed{SUF}.json"
if not fp.exists():
    from llm import ask_json
    names = [{"item": s["item"], "kind": s["kind"], "also_called": s["alternate_names"]} for s in seed]; res = {}
    for i in range(0, len(book), 100):
        att = [{"id": a["id"], "attribute": a["name"], "definition": a["definition"][:160], "values": [v["value"] for v in a["values"]][:8]} for a in book[i:i + 100]]
        prompt = ("SEED ITEMS (UI components and page sections from public design-system glossaries):\n" + json.dumps(names, ensure_ascii=False) + "\n\nCODEBOOK ATTRIBUTES (each describes one feature of a web page):\n" + json.dumps(att, ensure_ascii=False) +
                  '\n\nFor EVERY attribute decide whether it is about a seed item. relation: "is_item" = essentially the presence or kind of that component/section; "property_of_item" = a style, layout or variant dimension of that component/section (e.g. button shape, card radius); '
                  '"none" = not about any seed item (typography, color, spacing, copy style, imagery treatment, page-level layout, markup structure, effects...). Use the seed item\'s exact name, or null when relation is none.\n'
                  'Final answer ONLY a JSON object mapping attribute id to {"relation": "is_item"|"property_of_item"|"none", "seed_item": <name or null>}, for EVERY id.')
        res.update(ask_json(prompt, MODEL, "codebook_to_seed", n_attributes=len(att)))
    json.dump(res, open(fp, "w"), ensure_ascii=False, indent=1)
m = json.load(open(fp)); names = {s["item"] for s in seed}
for e in m.values():
    if isinstance(e, dict) and e.get("seed_item") in MERGE: e["seed_item"] = MERGE[e["seed_item"]]      # labels were made against v1; remap merged names
for a in book:
    e = m.get(a["id"]) or {}; a["relation"] = e.get("relation") if e.get("relation") in ("is_item", "property_of_item", "none") else "none"; a["seed_item"] = e.get("seed_item") if e.get("seed_item") in names else None
    if a["seed_item"] is None and a["relation"] != "none": a["relation"] = "none"      # a claimed link to a non-existent item counts as not covered
ABS = re.compile(r"\b(none|absent|not present|not used|not applicable|not shown|not visible|missing|without|other|unclear)\b|\bno[ _][a-z]+|^no$", re.I)
codes = list(csv.DictReader(open(CE / "page_codes_generated.csv"))); n_pages = len(codes)
rate = {}
for a in book:
    vals = [r.get(a["id"], "") for r in codes]; vals = [v for v in vals if v and v != "unclear"]
    rate[a["id"]] = (sum(not ABS.search(v.replace("_", " ")) for v in vals) / len(vals)) if vals else float("nan")
asum = {r["attribute_id"]: r for r in csv.DictReader(open(CE / "analysis/attribute_summary.csv"))}
prev = {i: int(r["pages_present"]) / max(int(r["pages_coded"]), 1) for i, r in summ.items()}; npg = max(int(r["pages_coded"]) for r in summ.values())
rows = [{"attribute_id": a["id"], "attribute": a["name"], "family": a["family"], "relation": a["relation"], "seed_item": a["seed_item"] or "", "presence_rate": round(rate[a["id"]], 3),
         "band": asum.get(a["id"], {}).get("band", ""), "modal_share": asum.get(a["id"], {}).get("modal_share", "")} for a in book]
with open(OUT / f"seed_vs_codebook{SUF}.csv", "w", newline="") as f: w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
cnt = collections.Counter(r["relation"] for r in rows); fam = collections.defaultdict(collections.Counter)
for r in rows: fam[r["family"]][r["relation"]] += 1
th = lambda k: sum(int(r["pages_present"]) >= k for r in summ.values())
cov_items = collections.Counter(r["seed_item"] for r in rows if r["seed_item"]); unmentioned = [i for i in summ if i not in cov_items]
unm_pert = [i for i in unmentioned if int(summ[i]["pages_present"]) >= 3]
pct = lambda xs: "n/a" if not len(xs) else f"median {np.nanmedian(xs):.2f}, mean {np.nanmean(xs):.2f}"
rs = {k: [r["presence_rate"] for r in rows if r["relation"] == k] for k in ("is_item", "property_of_item", "none")}; sv = list(prev.values())
bandc = {k: collections.Counter(r["band"] for r in rows if r["relation"] == k) for k in rs}
md = ["# Seed list vs self-generated codebook", f"{len(seed)} seed items (external glossaries), {len(book)} codebook attributes, {n_pages} pages. No culling applied.\n",
      "## Seed items: pertinence on these pages", f"- mentioned by the judges on >= 1 page: {th(1)} of {len(seed)}; on >= 3 pages: {th(3)}; on >= half the pages: {th(npg / 2)}; on no page: {len(seed) - th(1)}",
      f"- by kind (mentioned on >= 1 page): " + ", ".join(f"{k} {sum(int(r['pages_present']) >= 1 for r in summ.values() if r['kind'] == k)}/{sum(r['kind'] == k for r in summ.values())}" for k in ("component", "page_section")),
      "\n## Codebook attributes vs the seed list", f"- ABOUT a seed item: {cnt['is_item'] + cnt['property_of_item']} ({cnt['is_item']} is the item itself, {cnt['property_of_item']} a property/variant of it)", f"- ADDED by the codebook (not about any seed item): {cnt['none']} of {len(book)} ({100 * cnt['none'] / len(book):.0f}%)",
      "- by family (is_item / property_of_item / none): " + "; ".join(f"{f}: {c['is_item']}/{c['property_of_item']}/{c['none']}" for f, c in sorted(fam.items())),
      f"- seed items no codebook attribute is about: {len(unmentioned)} of {len(seed)}; of those mentioned on >= 3 pages (codebook gaps): {len(unm_pert)}" + (": " + ", ".join(unm_pert) if unm_pert else ""),
      "\n## Distributions to compare (share of pages where the thing is present)", f"- seed items (prevalence): {pct(sv)}", f"- codebook attributes about the item itself: {pct(rs['is_item'])}", f"- codebook property/variant attributes: {pct(rs['property_of_item'])}", f"- codebook attributes ADDED (not in seed): {pct(rs['none'])}",
      "- modal-share bands (shared >= .75 / split / varied): " + "; ".join(f"{k}: {dict(c)}" for k, c in bandc.items()), "\nFigure: seed_vs_codebook.png. Row-level table: seed_vs_codebook.csv. Relation labels are one LLM pass (not human-checked).\n"]
(OUT / f"seed_vs_codebook{SUF}.md").write_text("\n".join(md))
fig, ax = plt.subplots(figsize=(8, 4.5)); bins = np.linspace(0, 1, 11)
for data, lab in ((sv, "seed items (prevalence)"), (rs["is_item"] + rs["property_of_item"], "codebook, about a seed item"), (rs["none"], "codebook, added (not in seed)")): ax.hist([x for x in data if x == x], bins=bins, alpha=0.5, label=lab)
ax.set_xlabel("share of pages where present"); ax.set_ylabel("number of items / attributes"); ax.legend(); plt.tight_layout(); plt.savefig(OUT / f"seed_vs_codebook{SUF}.png", dpi=130)
print("\n".join(md[:14]))
