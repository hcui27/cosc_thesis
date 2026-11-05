"""Stage 1 of ANALYSIS_PLAN.md: collate everything about the study sites into flat tables (read-only, local files, no network/LLM).
usage: python pipeline/3_annotate/collate_sites.py
Writes data/analysis/:
  sites_table.csv    one row per site: category, rank, language, copy words, images, stack, render/judge status, observation counts, cost, key facts (original vs generated)
  observations.csv / observations.jsonl   one row per judge observation: site, judge model, obs_id, category, observation, evidence, which_side (always 'generated' now)
  exclusions.csv     draw slots that never became usable sites, with the reason
  summary.txt        counts and completeness checks
"""
import csv, json, glob, os, re, collections, pathlib

OUT = pathlib.Path("data/analysis"); OUT.mkdir(parents=True, exist_ok=True)
load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
SIDE = {None: "generated"}                    # observation-only judges describe the generated page alone (observe_single.py)
if os.environ.get("ARM") == "compare": SIDE = {"A": "original", "B": "generated", "both": "both"}     # comparison judges (judge.py): A = original, B = generated

sites = list(csv.DictReader(open("data/sites.csv")))
check = {r["site_id"]: r for r in csv.DictReader(open("data/sites_check.csv"))}
cost = collections.defaultdict(lambda: collections.defaultdict(float))        # site -> kind -> usd (from the ledger)
for l in open("data/ledger.jsonl"):
    x = json.loads(l); m = re.search(r"data/([^/]+)/", str(x.get("out", "")))
    if m and x.get("kind") in ("generate", "judge"): cost[m.group(1)][x["kind"]] += x.get("total_cost_usd") or 0

rows, obs = [], []
for r in sites:
    s = r["site_id"]; root = f"data/{s}"; run = f"{root}/generated_cli/r1/free"
    meta, fmt = load(f"{run}/meta.json"), load(f"{run}/format.json")
    og, gd = load(f"{root}/original/dom.json"), load(f"{run}/render/dom.json")
    judges = sorted(glob.glob(f"{root}/observations/r1_free.*.json"))
    counts = {}
    for f in judges:
        model = re.sub(r"^r1_free\.|\.json$", "", os.path.basename(f))
        items = json.load(open(f)); counts[model] = len(items)
        for i, o in enumerate(items):
            obs.append({"site_id": s, "judge": model, "obs_id": f"{s}|{model.split('-')[1]}|{i:02d}", "category": o.get("category", ""),
                        "observation": o.get("observation", ""), "evidence": o.get("evidence", ""), "which_side": SIDE.get(o.get("which_side"), o.get("which_side"))})
    top = lambda d: (d.get("fonts_by_element_count") or [["", 0]])[0][0]
    rows.append({"site_id": s, "category": r["category"], "subcategory": r.get("subcategory", ""), "inclusion_reason": r.get("reason", ""), "rank": r["rank"], "language": r["language"],
                 "title": r["title"], "snapshot": r["timestamp"], "copy_words": check[s]["copy_words"], "images": check[s]["images"],
                 "stack": fmt.get("kind", ""), "frameworks": "+".join(fmt.get("frameworks", [])), "render_status": fmt.get("render_status", ""),
                 "judge_obs_" + "sonnet": counts.get("claude-sonnet-5-5", 0), "judge_obs_opus": counts.get("claude-opus-5-5", 0),
                 "gen_seconds": meta.get("wall_seconds", ""), "gen_cost": round(cost[s]["generate"], 3), "judge_cost": round(cost[s]["judge"], 3),
                 "orig_page_height": og.get("layout", {}).get("page_height", ""), "gen_page_height": gd.get("layout", {}).get("page_height", ""),
                 "orig_top_font": top(og), "gen_top_font": top(gd),
                 "orig_body_bg": og.get("colors", {}).get("body_bg", ""), "gen_body_bg": gd.get("colors", {}).get("body_bg", ""),
                 "orig_shadows": og.get("effects", {}).get("box_shadows", ""), "gen_shadows": gd.get("effects", {}).get("box_shadows", ""),
                 "orig_gradients": og.get("effects", {}).get("gradient_backgrounds", ""), "gen_gradients": gd.get("effects", {}).get("gradient_backgrounds", ""),
                 "gen_images_rendered": gd.get("counts", {}).get("images", ""), "orig_images_rendered": og.get("counts", {}).get("images", "")})

def write(name, data):
    with open(OUT / name, "w", newline="") as f: w = csv.DictWriter(f, list(data[0])); w.writeheader(); w.writerows(data)
write("sites_table.csv", rows); write("observations.csv", obs)
with open(OUT / "observations.jsonl", "w") as f: [f.write(json.dumps(o, ensure_ascii=False) + "\n") for o in obs]

draw = {r["site_id"]: r for r in csv.DictReader(open("data/frames/sites_draw_cf.csv"))}
used = {r["site_id"] for r in sites}
ex = [{"site_id": s, "category": c.get("category", draw.get(s, {}).get("category", "")), "ok": c["ok"], "reason": c["reason"], "copy_words": c["copy_words"], "images": c["images"],
       "role": "in_draw" if s in draw else "replacement"} for s, c in check.items() if s not in used]
if ex: write("exclusions.csv", ex)

n = len(rows); done = [r for r in rows if r["render_status"] == "ok" and r["judge_obs_sonnet"] and r["judge_obs_opus"]]
cat = collections.Counter(r["category"] for r in rows)
lines = [f"sites: {n} | complete (rendered + both judges): {len(done)}",
         f"stacks: {dict(collections.Counter((r['stack'] + ('+' + r['frameworks'] if r['frameworks'] else '')) for r in rows))}",
         f"categories: {dict(sorted(cat.items()))}", f"languages: {dict(collections.Counter(r['language'] for r in rows))}",
         f"observations: {len(obs)} total | per judge: {dict(collections.Counter(o['judge'] for o in obs))} | which_side: {dict(collections.Counter(o['which_side'] for o in obs))}",
         f"observation categories: {dict(collections.Counter(o['category'] for o in obs).most_common(12))}",
         f"cost: generate ${sum(r['gen_cost'] for r in rows):.2f}, judges ${sum(r['judge_cost'] for r in rows):.2f}",
         f"exclusions: {len(ex)} checked sites not in the final list (see exclusions.csv)",
         f"incomplete sites: {[r['site_id'] for r in rows if r not in done]}"]
(OUT / "summary.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
