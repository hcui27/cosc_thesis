"""Master list: hierarchically summarise what is COMMON across the per-site diffs (family -> attribute = UI/UX feature -> value = what happens to it), separately for what is kept, changed, added and dropped on the vibe-coded pages.
usage: python pipeline/3_annotate/build_master.py [--min-sites 2] [--thr 0.30] [--max-group 40] [--pack 60] [--model claude-sonnet-5-5]
Reads data/<site>/diff/diff.json for all sites. Step 1 (offline): collect every tag. Step 1b (embedding pre-grouping, fastembed BGE-small): within each family, attributes (name + their commonest values) are embedded and clustered (agglomerative, cosine, average linkage,
distance < --thr; clusters above --max-group are re-split with a stricter threshold), so near-duplicate features sit in the same group and no LLM call sees an arbitrary slice. Step 2 (LLM, cached in data/master/cache/): groups are packed into calls of at most --pack
attributes (a group is never split across calls); each call merges attribute names and values that mean the same and writes a one-sentence summary per attribute; one more call per family writes the family summary. Step 3 (offline): counts.
Per attribute and value: sites with it (n), sites whose VIBE-CODED page has the feature (action kept/changed/added), sites whose ORIGINAL has it (kept/changed/dropped), action and status counts; element ids per site
(for galleries). Writes data/master/master_list.json and master_list.md. 'Common' = on at least --min-sites sites.
"""
import sys, json, glob, hashlib, collections, pathlib
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]
from llm import ask_json
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MINS, MODEL, THR, MAXG, PACK = int(g("--min-sites", 2)), g("--model", "claude-sonnet-5-5"), float(g("--thr", 0.30)), int(g("--max-group", 40)), int(g("--pack", 60)); MD = pathlib.Path("data/master"); (MD / "cache").mkdir(parents=True, exist_ok=True)
diffs = [json.load(open(f)) for f in sorted(glob.glob("data/*/diff/diff.json"))]; nsites = len(diffs)
rows = [{"site": d["site"], "status": o["status"], "obs": o["observation"], "elements": o.get("element_ids", []), **t} for d in diffs for o in d["observations"] for t in o.get("tags", [])]
print(f"{nsites} sites, {len(rows)} tags", flush=True)
by_fam = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows: by_fam[r["family"]][r["attribute"]].append(r)

PROMPT = """These are the ATTRIBUTE-VALUE tags that observations of {n} website pairs (original page vs a page an AI coding agent built from a content brief) received in the family "{fam}".
An ATTRIBUTE is a UI/UX feature (e.g. "primary navigation"); a VALUE says what happens to that feature on the AI-built page relative to the original, written "<action>: <what>" with action kept / changed / added / dropped.
For each attribute below: the number of sites and its values with how many sites each.
Task 1: merge attributes that name the same feature (e.g. "hero area" and "main banner"), choose one canonical name, and map every value of the merged attributes to a canonical value (merge only values that mean the same and have the same action word; keep the action word first).
Task 2: for each canonical attribute write ONE sentence on what is COMMON in what the AI-built pages do with this feature (the typical outcome and how widespread); neutral, no quality judgement. Also one sentence summarising the family.
Final answer ONLY JSON: {{"family_summary": str, "attributes": [{{"canonical": str, "members": [original attribute names], "value_map": {{"original value": "canonical value"}}, "summary": str}}]}}; every attribute below must appear in exactly one members list.

ATTRIBUTES: {att}"""

_emb = []
def embed(texts):
    import numpy as np
    if not _emb:
        from fastembed import TextEmbedding; _emb.append(TextEmbedding("BAAI/bge-small-en-v1.5"))
    E = np.array(list(_emb[0].embed(texts)), dtype=np.float32); return E / np.linalg.norm(E, axis=1, keepdims=True)
def pregroup(names, atts):
    """embedding pre-grouping of one family's attributes -> list of groups (lists of attribute names)"""
    from sklearn.cluster import AgglomerativeClustering
    if len(names) < 2: return [list(names)]
    texts = []
    for a in names:
        c = collections.Counter(r["value"] for r in atts[a]); texts.append(a + ": " + "; ".join(v for v, _ in c.most_common(3)))
    E = embed(texts); out = []
    def split(idx, thr):
        if len(idx) <= MAXG or thr < 0.10: out.append(idx); return
        lab = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average", distance_threshold=thr - 0.04).fit_predict(E[idx])
        parts = collections.defaultdict(list)
        for i, l in zip(idx, lab): parts[l].append(i)
        if len(parts) == 1: out.append(idx); return
        for p in parts.values(): split(p, thr - 0.04)
    lab = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average", distance_threshold=THR).fit_predict(E); parts = collections.defaultdict(list)
    for i, l in enumerate(lab): parts[l].append(i)
    for p in parts.values(): split(p, THR)
    return [[names[i] for i in p] for p in out]
def pack(groups):
    """first-fit packing of groups into calls of at most PACK attributes; a group is never split"""
    calls = []
    for g_ in sorted(groups, key=len, reverse=True):
        for c in calls:
            if len(c) + len(g_) <= PACK: c += g_; break
        else: calls.append(list(g_))
    return calls
FAM_PROMPT = """One-sentence summary of what AI-built web pages typically do with features in the family "{fam}", relative to the original pages, from these per-feature summaries (neutral, no quality judgement). Final answer ONLY JSON: {{"family_summary": str}}.
{items}"""

master = {}
for fam, atts in sorted(by_fam.items()):
    names = sorted(atts); groups = pregroup(names, atts); calls = pack(groups)
    print(f"  {fam}: {len(names)} attributes -> {len(groups)} groups -> {len(calls)} LLM calls", flush=True); res = {"family_summary": "", "attributes": []}
    for names_c in calls:
        tab = []
        for a in names_c:
            vv = collections.defaultdict(set)
            for r in atts[a]: vv[r["value"]].add(r["site"])
            tab.append({"attribute": a, "sites": len({r["site"] for r in atts[a]}), "values": {v: len(x) for v, x in vv.items()}})
        cache = MD / "cache" / (hashlib.sha1(json.dumps([fam, tab, nsites], sort_keys=True).encode()).hexdigest()[:14] + ".json")
        if cache.exists(): part = json.load(open(cache))
        else:
            part = ask_json(PROMPT.format(n=nsites, fam=fam, att=json.dumps(tab, ensure_ascii=False)), MODEL, "master_consolidate", family=fam, n_attributes=len(tab)); json.dump(part, open(cache, "w"), ensure_ascii=False, indent=1)
        res["attributes"] += part.get("attributes", [])
    items = json.dumps([{"feature": a["canonical"], "summary": a.get("summary", "")} for a in res["attributes"]], ensure_ascii=False)
    fc = MD / "cache" / ("fam_" + hashlib.sha1((fam + items).encode()).hexdigest()[:14] + ".json")
    if fc.exists(): res["family_summary"] = json.load(open(fc))["family_summary"]
    else: r2 = ask_json(FAM_PROMPT.format(fam=fam, items=items), MODEL, "master_family_summary", family=fam); json.dump(r2, open(fc, "w"), ensure_ascii=False); res["family_summary"] = r2.get("family_summary", "")
    canon = {}
    for a in res["attributes"]:
        for m in a.get("members", []): canon[m] = a
    out = []
    for a in res["attributes"]:
        vals = collections.defaultdict(lambda: {"sites": set(), "gen": set(), "orig": set(), "action": collections.Counter(), "status": collections.Counter(), "examples": [], "elements": collections.defaultdict(set)})
        for m in a.get("members", []):
            for r in atts.get(m, []):
                v = (a.get("value_map", {}) or {}).get(r["value"], r["value"]); e = vals[v]; e["sites"].add(r["site"]); e["action"][r["action"]] += 1; e["status"][r["status"]] += 1
                if r["action"] in ("kept", "changed", "added"): e["gen"].add(r["site"]); e["elements"][r["site"]].update(r["elements"])         # the vibe-coded page has the feature
                if r["action"] in ("kept", "changed", "dropped"): e["orig"].add(r["site"])                                                       # the original has it
                if len(e["examples"]) < 3: e["examples"].append(r["obs"][:200])
        vl = [{"value": v, "action": e["action"].most_common(1)[0][0], "n_sites": len(e["sites"]), "sites": sorted(e["sites"]), "generated_sites": sorted(e["gen"]), "n_generated": len(e["gen"]), "original_sites": sorted(e["orig"]), "n_original": len(e["orig"]),
               "status_counts": dict(e["status"]), "examples": e["examples"], "elements": {s: sorted(x) for s, x in e["elements"].items()}} for v, e in vals.items()]
        vl.sort(key=lambda x: -x["n_sites"])
        sites = {s for x in vl for s in x["sites"]}
        out.append({"attribute": a["canonical"], "members": a.get("members", []), "summary": a.get("summary", ""), "n_sites": len(sites), "values": vl,
                    "top_value_share": round(vl[0]["n_sites"] / nsites, 2) if vl else 0})
    out.sort(key=lambda x: -x["n_sites"])
    master[fam] = {"summary": res.get("family_summary", ""), "attributes": out}
json.dump({"n_sites": nsites, "min_sites": MINS, "families": master}, open(MD / "master_list.json", "w"), indent=1, ensure_ascii=False)
md = [f"# Master list over {nsites} sites (common = on >= {MINS} sites)\n"]
for fam, f in master.items():
    common = [a for a in f["attributes"] if a["n_sites"] >= MINS]
    md += [f"\n## {fam}: {f['summary']}", f"{len(f['attributes'])} attributes ({len(common)} on >= {MINS} sites)\n"]
    for a in common:
        md.append(f"- **{a['attribute']}** ({a['n_sites']} sites): {a['summary']}")
        for v in a["values"][:5]: md.append(f"    - {v['value']}: {v['n_sites']} sites")
(MD / "master_list.md").write_text("\n".join(md) + "\n")
print(f"master list: {sum(len(f['attributes']) for f in master.values())} attributes in {len(master)} families -> {MD}/master_list.json")
