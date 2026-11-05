"""PILOT: do the JUDGES' OBSERVATIONS (and the codebook built from them) corroborate the closed SEED list (seed_attributes/seed_v1.csv, from external glossaries)?
The seed list is NOT coded from the page. For every page, one text call matches each seed item to the judge observations that state the page has it; the codebook then says whether an attribute about
that item received a value for the page. The point: which seed features do the judges actually notice, and which do they never mention.
NO CULLING YET (decided 2026-10-26): items are not trimmed here; relevance is read off the corroboration table later (PLAN.md, "Seed list: culling, later").
usage: python pipeline/3_annotate/seed_pilot.py [--stage match|summary|all] [--sites a,b] [--model claude-sonnet-5-5] [--workers 4] [--dry-run]     (run from the arm's root: project root, or arms/compare/)
match:   per page, observations (tier A/B; about the generated page: which_side generated|both) + the 82 seed items -> data/analysis_seed/observation_match/<site>.json
         {item id: {"mentioned": bool, "obs_ids": [...], "how": "<=12 words"}}. A property statement ("buttons have 8px corners") counts for its item (Button); a loose name overlap does not.
summary: offline. Per item: pages with a judge observation, pages where BOTH judges mention it (Sonnet and Opus), pages where a codebook attribute about the item has a value from the observations
         (needs data/analysis_seed/codebook_to_seed.json from compare_seed_vs_codebook.py; otherwise that column is blank) -> corroboration.csv (item x page) and corroboration_summary.csv (item).
The vision-based page-presence version is seed_pilot_vision.py (data/analysis_seed/presence.csv), kept as a reference for how often an item is on the page vs how often a judge says so.
"""
import sys, csv, json, pathlib, collections, concurrent.futures as cf
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
STAGE, MODEL, WORKERS, DRY = g("--stage", "all"), g("--model", "claude-sonnet-5-5"), int(g("--workers", 4)), "--dry-run" in sys.argv
SEED = g("--seed", "v1_1")          # v1_1: Component Gallery + Open UI + Tailwind Plus (duplicates merged); v1_2: Component Gallery + Open UI + public CSS frameworks
SUF = "" if SEED == "v1_1" else "_" + SEED
OUT = pathlib.Path("data/analysis_seed"); MD = OUT / f"observation_match{SUF}"; MD.mkdir(parents=True, exist_ok=True)
if SEED == "v1_1":
    items = list(csv.DictReader(open("seed_attributes/seed_v1.csv")))          # v1 order: the cached matches are indexed by it
    MERGE = {r["from_item"]: r["into_item"] for r in csv.DictReader(open("seed_attributes/merges_v1_1.csv"))}      # v1.1: duplicate names merged at SUMMARY time (matches are not redone)
    items11 = list(csv.DictReader(open("seed_attributes/seed_v1_1.csv")))
else: items = items11 = list(csv.DictReader(open(f"seed_attributes/seed_{SEED}.csv"))); MERGE = {}      # later versions are matched afresh, no merge map
obs = [r for r in csv.DictReader(open("data/analysis/observations_tiered.csv")) if r["tier"] in ("A", "B") and r["which_side"] in ("generated", "both")]
by_site = collections.defaultdict(list)
for r in obs: by_site[r["site_id"]].append(r)
sites = [s for s in g("--sites", "").split(",") if s] or sorted(by_site)
Q = [{"id": f"i{n}", "item": it["item"], "kind": it["kind"], "also_called": it["alternate_names"]} for n, it in enumerate(items)]

def match(site):
    from llm import ask_json
    rows = by_site[site]; ids = {f"o{n}": r for n, r in enumerate(rows)}
    lines = [{"id": k, "observation": r["observation"][:300]} for k, r in ids.items()]
    prompt = ("Below are observations that two judges made about ONE web page, and a fixed list of UI components and page sections (with alternate names). For EACH list item, say whether any observation states that THIS page "
              "has it: a 'component' is a UI component of that type (alternate names count); a 'page_section' is a section that serves that purpose. An observation about a property of the item (e.g. 'buttons have 8px corners' "
              "for Button) counts. A loose overlap of words does not count, and an observation that says the page LACKS the item is not a mention. Use only what the observations say; do not guess from the item list.\n"
              'Final answer ONLY a JSON object mapping EVERY item id to {"mentioned": true|false, "obs_ids": [up to 6 observation ids], "how": "<=12 words on what the observations say, or empty"}.\n\n'
              f"ITEMS:\n{json.dumps(Q, ensure_ascii=False)}\n\nOBSERVATIONS:\n{json.dumps(lines, ensure_ascii=False)}")
    res = ask_json(prompt, MODEL, "seed_match", site=site, n_items=len(Q), n_obs=len(rows))
    for v in res.values():
        if isinstance(v, dict): v["obs_ids"] = [ids[o]["obs_id"] for o in (v.get("obs_ids") or []) if o in ids]       # store the real obs_id (carries the judge)
    json.dump(res, open(MD / f"{site}.json", "w"), ensure_ascii=False, indent=1)

if STAGE in ("match", "all"):
    todo = [s for s in sites if not (MD / f"{s}.json").exists()]
    print(f"{len(items)} seed items, {len(obs)} observations on {len(sites)} pages -> {len(todo)} calls (text only, about $0.12 each, so about ${0.12 * len(todo):.1f})", flush=True)
    if DRY: sys.exit()
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        for s, f in [(s, ex.submit(match, s)) for s in todo]:
            try: f.result(); print("  matched", s, flush=True)
            except Exception as e: print("  FAILED", s, type(e).__name__, str(e)[:120], flush=True)
if STAGE in ("summary", "all"):
    cts = json.load(open(OUT / f"codebook_to_seed{SUF}.json")) if (OUT / f"codebook_to_seed{SUF}.json").exists() else {}
    attr_of = collections.defaultdict(set)
    for a, v in cts.items():
        v = {**v, "seed_item": MERGE.get(v.get("seed_item"), v.get("seed_item"))}
        if v.get("relation") in ("is_item", "property_of_item") and v.get("seed_item"): attr_of[v["seed_item"]].add(a)
    sav = {r["site_id"]: r for r in csv.DictReader(open("data/analysis/codebook/site_attribute_values_from_observations.csv"))}
    rows, cell = [], {}
    for s in sites:
        fp = MD / f"{s}.json"
        if not fp.exists(): continue
        d = json.load(open(fp)); acc = collections.defaultdict(lambda: {"mentioned": False, "obs": [], "how": []})
        for n, it in enumerate(items):
            e = d.get(f"i{n}"); e = e if isinstance(e, dict) else {}; a = acc[MERGE.get(it["item"], it["item"])]
            a["mentioned"] |= bool(e.get("mentioned")); a["obs"] += e.get("obs_ids", []); a["how"] += [e["how"]] if e.get("how") else []
        for it in items11:
            a = acc[it["item"]]; judges = {o.split("|")[1] for o in a["obs"]}
            cb = bool(cts) and any(sav.get(s, {}).get(x) for x in attr_of[it["item"]])
            cell[(s, it["item"])] = {"site_id": s, "item": it["item"], "kind": it["kind"], "mentioned": a["mentioned"], "judges": "+".join(sorted(judges)), "both_judges": len(judges) >= 2,
                                     "codebook_value": cb if cts else "", "obs_ids": " ".join(dict.fromkeys(a["obs"])), "how": " / ".join(a["how"][:2])}
    with open(OUT / f"corroboration{SUF}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(next(iter(cell.values())))); w.writeheader(); w.writerows(cell.values())
    done = sorted({s for s, _ in cell}); summ = []
    for it in items11:
        c = [cell[(s, it["item"])] for s in done]; m = [x for x in c if x["mentioned"]]
        summ.append({"item": it["item"], "kind": it["kind"], "sources": it["sources"], "pages": len(done), "pages_mentioned": len(m), "prevalence": round(len(m) / max(len(done), 1), 3),
                     "pages_both_judges": sum(x["both_judges"] for x in c), "codebook_attributes": len(attr_of[it["item"]]) if cts else "", "pages_codebook_value": sum(x["codebook_value"] is True for x in c) if cts else "",
                     "example_how": " | ".join(x["how"] for x in m[:3] if x["how"])})
    summ.sort(key=lambda r: -r["pages_mentioned"])
    with open(OUT / f"corroboration_summary{SUF}.csv", "w", newline="") as f: w = csv.DictWriter(f, list(summ[0])); w.writeheader(); w.writerows(summ)
    bins = collections.Counter("0" if r["pages_mentioned"] == 0 else "1-2" if r["pages_mentioned"] <= 2 else "3-6" if r["pages_mentioned"] <= 6 else "7-13" if r["pages_mentioned"] <= 13 else "14+" for r in summ)
    print(f"{len(items11)} seed items (v1.1) over {len(done)} pages; mentioned by the judges on 0 pages: {bins['0']}, 1-2: {bins['1-2']}, 3-6: {bins['3-6']}, 7-13: {bins['7-13']}, 14+: {bins['14+']} (no items dropped)")
    print("top 15:", ", ".join(f"{r['item']} ({r['pages_mentioned']})" for r in summ[:15]))
