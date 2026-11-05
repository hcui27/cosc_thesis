"""LAST STEP of the pipeline: match the MASTER LIST to the closed SEED list (the corpus), to see which seed features the observations corroborate and what the observations add that the seed list lacks.
usage: python pipeline/3_annotate/match_seed.py [--seed v1_3] [--min-sites 2] [--model claude-sonnet-5-5]
For every master-list attribute (canonical name, summary, values), one LLM label (batches of 80, cached in data/master/seed_match_<seed>.json): is it ABOUT a seed item?
  relation = "is_item" (it is the presence or kind of that component/section), "property_of_item" (a style, layout or variant dimension of it), or "none" (not about any seed item = ADDED by the observations).
Offline: per seed item, the master attributes matched to it and the sites where the AI-built page shows it (union over matched attributes' generated values) and where the original does; seed items with no match; master attributes with none.
Writes data/master/seed_match_<seed>.{json,csv,md}. Nothing is culled.
"""
import sys, csv, json, collections, pathlib
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]
from llm import ask_json
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SEED, MINS, MODEL = g("--seed", "v1_3"), int(g("--min-sites", 2)), g("--model", "claude-sonnet-5-5"); MD = pathlib.Path("data/master")
seed = list(csv.DictReader(open(f"seed_attributes/seed_{SEED}.csv"))); M = json.load(open(MD / "master_list.json")); nsites = M["n_sites"]
atts = [{"id": f"m{i}", "key": f"{fam}|{a['attribute']}", "family": fam, **a} for i, (fam, a) in enumerate((f, a) for f, F in M["families"].items() for a in F["attributes"])]      # labels are cached by family|attribute so a rebuilt master list keeps them
fp = MD / f"seed_match_{SEED}.json"; lab = json.load(open(fp)) if fp.exists() else {}
names = [{"item": s["item"], "kind": s["kind"], "also_called": s["alternate_names"]} for s in seed]
for k in range(0, len(atts), 80):
    todo = [a for a in atts[k:k + 80] if a["key"] not in lab]
    if not todo: continue
    q = [{"id": a["id"], "attribute": a["attribute"], "summary": a["summary"][:200], "values": [v["value"] for v in a["values"]][:8]} for a in todo]
    prompt = ("SEED ITEMS (UI components and page sections from public glossaries and design systems):\n" + json.dumps(names, ensure_ascii=False) + "\n\nMASTER-LIST ATTRIBUTES (each describes one feature of web pages that observations of AI-built sites and their originals revealed):\n" + json.dumps(q, ensure_ascii=False) +
              '\n\nFor EVERY attribute decide whether it is about a seed item. relation: "is_item" = essentially the presence or kind of that component/section; "property_of_item" = a style, layout or variant dimension of that component/section (e.g. button shape, card radius); '
              '"none" = not about any seed item (typography, color, spacing, copy style, imagery treatment, page-level layout, markup structure, effects...). Use the seed item\'s exact name, or null.\n'
              'Final answer ONLY a JSON object mapping attribute id to {"relation": "is_item"|"property_of_item"|"none", "seed_item": <name or null>}, for EVERY id.')
    got = ask_json(prompt, MODEL, "master_to_seed", n_attributes=len(q)); lab.update({a["key"]: got[a["id"]] for a in todo if isinstance(got.get(a["id"]), dict)}); json.dump(lab, open(fp, "w"), ensure_ascii=False, indent=1)
valid = {s["item"] for s in seed}
for a in atts:
    e = lab.get(a["key"]) or {}; a["relation"] = e.get("relation") if e.get("relation") in ("is_item", "property_of_item", "none") else "none"; a["seed_item"] = e.get("seed_item") if e.get("seed_item") in valid else None
    if a["seed_item"] is None: a["relation"] = "none"
by_item = collections.defaultdict(list)
for a in atts:
    if a["seed_item"]: by_item[a["seed_item"]].append(a)
rows = []
for s in seed:
    A = by_item.get(s["item"], []); gs = {x for a in A for v in a["values"] for x in v["generated_sites"]}; os_ = {x for a in A for v in a["values"] for x in v["original_sites"]}
    rows.append({"item": s["item"], "kind": s["kind"], "sources": s["sources"], "master_attributes": len(A), "is_item_attributes": sum(a["relation"] == "is_item" for a in A), "sites_ai_built": len(gs), "sites_original": len(os_), "attributes": " | ".join(a["attribute"] for a in A)})
rows.sort(key=lambda r: -r["sites_ai_built"])
with open(MD / f"seed_match_{SEED}.csv", "w", newline="") as f: w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
added = [a for a in atts if a["relation"] == "none"]; cov = [r for r in rows if r["master_attributes"]]
th = lambda k: sum(r["sites_ai_built"] >= k for r in rows)
fam = collections.defaultdict(collections.Counter)
for a in atts: fam[a["family"]][a["relation"]] += 1
common = lambda xs: [a for a in xs if a["n_sites"] >= MINS]
md = [f"# Master list vs seed list {SEED}", f"{len(seed)} seed items, {len(atts)} master attributes over {nsites} sites. Nothing culled.\n",
      "## Seed items corroborated by the observations", f"- with at least one matched master attribute: {len(cov)} of {len(seed)}; AI-built page shows it on >= 1 site: {th(1)}, >= {MINS}: {th(MINS)}, >= half the sites: {th(nsites / 2)}; no match: {len(seed) - len(cov)}",
      f"- by kind (matched): " + ", ".join(f"{k} {sum(1 for r in cov if r['kind'] == k)}/{sum(1 for r in rows if r['kind'] == k)}" for k in ("component", "page_section")),
      "\n## What the observations add beyond the seed list", f"- master attributes about a seed item: {len(atts) - len(added)} ({sum(a['relation'] == 'is_item' for a in atts)} the item itself, {sum(a['relation'] == 'property_of_item' for a in atts)} a property of it)",
      f"- ADDED (not about any seed item): {len(added)} of {len(atts)} ({100 * len(added) // max(len(atts), 1)}%); of those on >= {MINS} sites: {len(common(added))}; of all attributes on >= {MINS} sites: {len(common(atts))}",
      "- by family (is_item / property_of_item / none): " + "; ".join(f"{f}: {c['is_item']}/{c['property_of_item']}/{c['none']}" for f, c in sorted(fam.items())),
      f"\n## Seed items never matched ({len(seed) - len(cov)}): " + ", ".join(r["item"] for r in rows if not r["master_attributes"]),
      "\n## Added attributes seen on the most sites"] + [f"- {a['attribute']} ({a['family']}, {a['n_sites']} sites): {a['summary']}" for a in sorted(added, key=lambda a: -a["n_sites"])[:15]]
(MD / f"seed_match_{SEED}.md").write_text("\n".join(md) + "\n"); print("\n".join(md[:12]))
