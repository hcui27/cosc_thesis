"""Stage 3 of ANALYSIS_PLAN.md: turn verified observations into a catalog of site-independent features shared across the seed sites.
usage: python pipeline/3_annotate/observations_to_features.py [--sites a,b] [--extract-only] [--model claude-sonnet-5-5] [--workers 3]
Input: data/analysis/observations_tiered.csv (check_observations.py). Uses tier A/B observations about the GENERATED side (which_side generated|both); tier C is dropped.
 1. per site: observations that both judges matched are merged into one item; one LLM call turns the items into site-independent feature statements (cached in data/analysis/features/site_<site>.json)
 2. across sites: per family, an LLM groups all statements into canonical features (name, definition, detector, optional programmatic proxy on measurements.KEYS), cached in groups_<family>.json
Outputs in data/analysis/: features_catalog.json / .csv, site_features.csv, feature_mentions.csv (sites x features, 'mentioned' by the judges; NOT presence/absence, that is Stage 4).
"""
import sys, os, csv, json, re, hashlib, collections, pathlib, concurrent.futures as cf
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from llm import ask_json
import measurements

g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MODEL, WORKERS = g("--model", "claude-sonnet-5-5"), int(g("--workers", 3))
OUT = pathlib.Path("data/analysis"); FD = OUT / "features"; FD.mkdir(parents=True, exist_ok=True)
FAMILIES = ["typography", "color", "layout", "component", "decoration", "imagery", "copy", "semantic_dom", "other"]
CHUNK = 200

# ---------- step 1: per-site items and feature statements
def site_items(rows):
    parent = {r["obs_id"]: r["obs_id"] for r in rows}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for r in rows:
        for o in filter(None, r["matched_with"].split(";")):
            if o in parent: parent[find(o)] = find(r["obs_id"])
    comp = collections.defaultdict(list)
    for r in rows: comp[find(r["obs_id"])].append(r)
    items = []
    for k, (_, m) in enumerate(sorted(comp.items())):
        rep = max(m, key=lambda r: (r["judge"].endswith("opus-5-5"), len(r["observation"])))
        items.append({"id": f"I{k}", "text": rep["observation"][:320], "evidence": rep["evidence"][:140], "side": rep["which_side"], "members": [r["obs_id"] for r in m],
                      "tier": "A" if any(r["tier"] == "A" for r in m) else "B"})
    return items

def extract_site(site, items):
    prompt = ("Below are checked observations about differences between an ORIGINAL web page (side A) and an AI-GENERATED page (side B). Extract the TRAITS OF THE GENERATED PAGE (B) "
              "as site-independent features that could be checked on ANY website.\nRules: describe B's trait itself ('Primary buttons are fully rounded pills'), not the change from A; "
              "skip items that only describe A, or that are only about the brand, products or facts with no style/structure/copy-treatment trait; keep traits of tone and microcopy; "
              "merge items that state the same trait (one feature per distinct trait); an item may support at most two features; statement of at most 20 words, with no site-specific names; "
              f"family is one of {FAMILIES}.\n"
              'Final answer ONLY a JSON array: [{"statement": str, "family": str, "items": ["I3", "I9"]}]\n\nITEMS:\n' + json.dumps(
                  [{"id": i["id"], "observation": i["text"], "evidence": i["evidence"]} for i in items], ensure_ascii=False))
    res = ask_json(prompt, MODEL, "feature_extract", site=site, n_items=len(items)); ids = {i["id"] for i in items}
    feats = [{"statement": str(f.get("statement", "")).strip(), "family": f.get("family") if f.get("family") in FAMILIES else "other",
              "items": [x for x in f.get("items", []) if x in ids]} for f in res if f.get("statement")]
    json.dump({"items": items, "features": feats}, open(FD / f"site_{site}.json", "w"), indent=1, ensure_ascii=False)

# ---------- step 2: canonical grouping per family
def group_call(stmts, family, label):
    prompt = ("Group these statements about AI-generated web pages (family: " + family + ") into CANONICAL FEATURES. Statements that describe the same checkable trait go together "
              "(same trait, different wording; not merely related); keep distinct traits separate and do not over-merge.\nFor each group give: name (at most 8 words); definition (one sentence phrased as a "
              "yes/no check on any page); detector: 'programmatic' if the page facts can compute it, 'vision' if it needs looking at the page, 'text' if it only needs the page's words; "
              'proxy: if programmatic, {"key": <one of the measurement keys>, "op": one of >=,>,<=,<,==, "value": number} approximating the check, else null; members: list of statement ids. '
              "Every statement id must appear in exactly one group.\nMeasurement keys: " + json.dumps(measurements.KEYS) +
              '\nFinal answer ONLY a JSON array: [{"name": str, "definition": str, "detector": str, "proxy": null, "members": ["s1", "s2"]}]\n\nSTATEMENTS:\n' + json.dumps(stmts, ensure_ascii=False))
    res = ask_json(prompt, MODEL, "feature_group", family=family, label=label, n_statements=len(stmts))
    seen, groups = set(), []
    for gr in res:
        mem = [m for m in gr.get("members", []) if m in {s["id"] for s in stmts} and m not in seen]; seen.update(mem)
        if mem: groups.append({"name": gr.get("name", "")[:80], "definition": gr.get("definition", ""), "detector": gr.get("detector", "vision"), "proxy": gr.get("proxy"), "members": mem})
    texts = {s["id"]: s["text"] for s in stmts}
    for s in stmts:                      # anything the model dropped becomes its own group
        if s["id"] not in seen: groups.append({"name": s["text"][:60], "definition": s["text"], "detector": "vision", "proxy": None, "members": [s["id"]]})
    return groups

def group_family(family, stmts):
    key = hashlib.sha1(json.dumps(stmts, sort_keys=True).encode()).hexdigest()[:12]; fp = FD / f"groups_{family}.json"
    if fp.exists() and json.load(open(fp)).get("key") == key: return json.load(open(fp))["groups"]
    if len(stmts) <= CHUNK: groups = group_call(stmts, family, "single")
    else:                                # chunk, then merge the chunk-level canonical features in a second pass
        parts = [group_call(stmts[i:i + CHUNK], family, f"chunk{i // CHUNK}") for i in range(0, len(stmts), CHUNK)]
        flat = [c for p in parts for c in p]
        merge = group_call([{"id": f"c{i}", "text": c["name"] + ": " + c["definition"]} for i, c in enumerate(flat)], family, "merge")
        groups = []
        for m in merge:
            mem = [x for c in m["members"] for x in flat[int(c[1:])]["members"]]
            groups.append({**m, "members": mem})
    json.dump({"key": key, "groups": groups}, open(fp, "w"), indent=1, ensure_ascii=False); return groups

if __name__ == "__main__":
    rows = [r for r in csv.DictReader(open(OUT / "observations_tiered.csv")) if r["tier"] in ("A", "B") and r["which_side"] in ("generated", "both")]
    by_site = collections.defaultdict(list)
    for r in rows: by_site[r["site_id"]].append(r)
    sites = [s for s in g("--sites", "").split(",") if s] or sorted(by_site)
    todo = [s for s in sites if not (FD / f"site_{s}.json").exists()]
    print(f"{len(rows)} usable observations; {len(todo)} sites to extract ({len(sites) - len(todo)} cached)", flush=True)
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = {s: ex.submit(extract_site, s, site_items(by_site[s])) for s in todo}
        for s, f in futs.items():
            try: f.result(); print("  extracted", s, flush=True)
            except Exception as e: print("  FAILED", s, type(e).__name__, str(e)[:100], flush=True)
    if "--extract-only" in sys.argv: sys.exit()
    sf = []                                                           # site-level feature statements
    for s in sites:
        fp = FD / f"site_{s}.json"
        if not fp.exists(): continue
        d = json.load(open(fp)); nm = {i["id"]: len(i["members"]) for i in d["items"]}
        for k, f in enumerate(d["features"]):
            sf.append({"sid": f"{s}#{k}", "site": s, "statement": f["statement"], "family": f["family"], "n_obs": sum(nm.get(i, 0) for i in f["items"])})
    by_fam = collections.defaultdict(list)
    for x in sf: by_fam[x["family"]].append({"id": x["sid"], "text": x["statement"]})
    print(f"{len(sf)} site-level statements; grouping {len(by_fam)} families", flush=True)
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        res = {fam: ex.submit(group_family, fam, st) for fam, st in by_fam.items()}
        groups = {fam: f.result() for fam, f in res.items()}
    sfd = {x["sid"]: x for x in sf}; cat = []
    for fam in FAMILIES:
        for gr in groups.get(fam, []):
            mem = [sfd[m] for m in gr["members"] if m in sfd]; sites_ = sorted({m["site"] for m in mem})
            px = gr["proxy"] if isinstance(gr["proxy"], dict) and gr["proxy"].get("key") in measurements.KEYS and gr["proxy"].get("op") in measurements.OPS else None
            cat.append({"name": gr["name"], "family": fam, "definition": gr["definition"], "detector": "programmatic" if px else ("text" if gr["detector"] == "text" else "vision"),
                        "proxy": px, "sites": sites_, "n_sites": len(sites_), "n_statements": len(mem), "n_observations": sum(m["n_obs"] for m in mem), "members": [m["sid"] for m in mem]})
    cat.sort(key=lambda c: (FAMILIES.index(c["family"]), -c["n_sites"], c["name"]))
    for i, c in enumerate(cat, 1): c["id"] = f"F{i:03d}"
    json.dump(cat, open(OUT / "features_catalog.json", "w"), indent=1, ensure_ascii=False)
    with open(OUT / "features_catalog.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "family", "name", "definition", "detector", "proxy", "n_sites", "n_statements", "n_observations", "sites"])
        for c in cat: w.writerow([c["id"], c["family"], c["name"], c["definition"], c["detector"], json.dumps(c["proxy"]) if c["proxy"] else "", c["n_sites"], c["n_statements"], c["n_observations"], ";".join(c["sites"])])
    fid = {m: c["id"] for c in cat for m in c["members"]}
    with open(OUT / "site_features.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["site_statement_id", "site", "feature_id", "family", "statement", "n_obs"])
        for x in sf: w.writerow([x["sid"], x["site"], fid.get(x["sid"], ""), x["family"], x["statement"], x["n_obs"]])
    allsites = sorted({x["site"] for x in sf})
    with open(OUT / "feature_mentions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["site_id"] + [c["id"] for c in cat])
        for s in allsites: w.writerow([s] + [int(s in c["sites"]) for c in cat])
    T = collections.Counter(c["detector"] for c in cat); sing = sum(c["n_sites"] == 1 for c in cat)
    print(f"\ncatalog: {len(cat)} features from {len(allsites)} sites | detectors {dict(T)} | singletons {sing} ({100 * sing / len(cat):.0f}%) | in >=10 sites: {sum(c['n_sites'] >= 10 for c in cat)}")
