"""Embedding-based merging of observation sheets into one master list of shared observations (alternative to the LLM grouping in observations_to_features.py).
usage: python pipeline/3_annotate/embed_merge.py [--source statements|observations] [--tau 0.78] [--final-tau 0.85] [--min-sites 3] [--model BAAI/bge-small-en-v1.5] [--no-verify]
Each site's list of observations is a SHEET. Every observation is embedded (fastembed, BGE-small, local, normalised). Then, repeatedly:
  1. for every pair of sheets, match observations that are MUTUAL nearest neighbours with cosine >= tau; sheet similarity = 2 * matches / (size A + size B)
  2. merge the most similar pair of sheets: matched observations become ONE entry (site sets are unioned, the entry's vector is the centroid of its members), unmatched ones are carried over
  3. continue until a single master sheet remains (n sites - 1 merges)
A final pass merges master entries that are still near-duplicates (cosine >= final-tau, average linkage).
VERIFY (default, skip with --no-verify): embeddings group by TOPIC, so one entry can hold OPPOSITE values (square vs rounded corners, red vs blue links). For every entry with >= 2 sites an LLM (Sonnet, one call per entry, cached in merge/verify_cache.json)
splits the members into groups that assert the same trait with the same value; counts are recomputed from those groups. The unverified list is kept as master_observations_unverified.json.
count = number of distinct sites that share an entry.
--source statements: each site's extracted, site-independent feature statements (data/analysis/features/site_<site>.json; default).  --source observations: the raw tier A/B observations about the generated side (matched pairs merged).
Writes data/analysis/merge/{master_observations.csv/.json, key_observations.csv/.json (count >= min-sites), merge_log.csv, sheet_dendrogram.png, summary.txt}.
"""
import sys, os, csv, json, glob, re, collections, pathlib
import numpy as np
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SOURCE, TAU, FTAU, MINS, MODEL = g("--source", "statements"), float(g("--tau", 0.78)), float(g("--final-tau", 0.85)), int(g("--min-sites", 3)), g("--model", "BAAI/bge-small-en-v1.5")
OUT = pathlib.Path("data/analysis"); MD = OUT / "merge"; MD.mkdir(exist_ok=True)

# ---------- load the sheets
sheets_raw = collections.OrderedDict()                                 # site -> [(text, family)]
if SOURCE == "statements":
    for fp in sorted(glob.glob(str(OUT / "features" / "site_*.json"))):
        site = re.sub(r"^site_|\.json$", "", os.path.basename(fp)); d = json.load(open(fp))
        sheets_raw[site] = [(f["statement"], f["family"]) for f in d["features"] if f.get("statement")]
else:
    from observations_to_features import site_items
    rows = [r for r in csv.DictReader(open(OUT / "observations_tiered.csv")) if r["tier"] in ("A", "B") and r["which_side"] in ("generated", "both")]
    by = collections.defaultdict(list)
    for r in rows: by[r["site_id"]].append(r)
    for s in sorted(by): sheets_raw[s] = [(i["text"], "") for i in site_items(by[s])]
sites = list(sheets_raw); N = len(sites)

# ---------- embed (fastembed, local)
from fastembed import TextEmbedding
texts = [t for s in sites for t, _ in sheets_raw[s]]
emb = np.array(list(TextEmbedding(MODEL).embed(texts)), dtype=np.float32); emb /= np.linalg.norm(emb, axis=1, keepdims=True)
print(f"{N} sheets, {len(texts)} observations, embedding dim {emb.shape[1]} ({MODEL}), tau={TAU}", flush=True)

def make_entry(members):                                               # members: list of dicts {site, text, family, vec}
    V = np.stack([m["vec"] for m in members]); c = V.mean(0); c /= np.linalg.norm(c)
    return {"members": members, "cent": c, "sites": {m["site"] for m in members}}
class Sheet:
    def __init__(self, entries, sid, leaf_sites): self.entries, self.id, self.sites = entries, sid, leaf_sites; self.C = np.stack([e["cent"] for e in entries])
def matches(A, B):
    S = A.C @ B.C.T; ia, jb = S.argmax(1), S.argmax(0)
    return [(i, int(j)) for i, j in enumerate(ia) if jb[j] == i and S[i, j] >= TAU], S
def sim(A, B): p, _ = matches(A, B); return 2 * len(p) / (len(A.entries) + len(B.entries)), p

k = 0; sh = {}
for si, s in enumerate(sites):
    ents = []
    for t, fam in sheets_raw[s]: ents.append(make_entry([{"site": s, "text": t, "family": fam, "vec": emb[k]}])); k += 1
    sh[si] = Sheet(ents, si, {s})

# ---------- agglomerative merging of sheets
cache = {(i, j): sim(sh[i], sh[j]) for i in sh for j in sh if i < j}; log, Z, nxt, last = [], [], N, 0.0
while len(sh) > 1:
    (i, j), (sv, pairs) = max(cache.items(), key=lambda kv: (kv[1][0], -(len(sh[kv[0][0]].entries) + len(sh[kv[0][1]].entries)), -kv[0][0]))
    A, B = sh[i], sh[j]; used_a, used_b = {a for a, _ in pairs}, {b for _, b in pairs}; ents = []
    for a, b in pairs: ents.append(make_entry(A.entries[a]["members"] + B.entries[b]["members"]))
    ents += [e for a, e in enumerate(A.entries) if a not in used_a] + [e for b, e in enumerate(B.entries) if b not in used_b]
    new = Sheet(ents, nxt, A.sites | B.sites); dist = max(1 - sv, last); last = dist
    log.append({"step": len(log) + 1, "sim": round(sv, 3), "matched": len(pairs), "size_a": len(A.entries), "size_b": len(B.entries), "merged_size": len(ents),
                "sites_a": ";".join(sorted(A.sites)) if len(A.sites) <= 3 else f"{len(A.sites)} sites", "sites_b": ";".join(sorted(B.sites)) if len(B.sites) <= 3 else f"{len(B.sites)} sites"})
    Z.append([A.id, B.id, dist, len(new.sites)])
    for key in [kk for kk in cache if i in kk or j in kk]: del cache[key]
    del sh[i], sh[j]
    for o in list(sh): cache[(min(o, nxt), max(o, nxt))] = sim(sh[o], new) if o < nxt else sim(new, sh[o])
    sh[nxt] = new; nxt += 1
master = list(sh.values())[0].entries

# ---------- final pass: merge near-duplicates left in the master sheet
if FTAU < 1 and len(master) > 1:
    from sklearn.cluster import AgglomerativeClustering
    lab = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average", distance_threshold=1 - FTAU).fit_predict(np.stack([e["cent"] for e in master]))
    groups = collections.defaultdict(list)
    for e, l in zip(master, lab): groups[l].extend(e["members"])
    before = len(master); master = [make_entry(m) for m in groups.values()]; print(f"final pass: {before} -> {len(master)} master entries (tau {FTAU})")

# ---------- verify: split entries whose members state different values (embeddings cannot tell 'square' from 'rounded')
unverified = None
if "--no-verify" not in sys.argv:
    import hashlib, concurrent.futures as cf
    from llm import ask_json
    cp = MD / "verify_cache.json"; cache = json.load(open(cp)) if cp.exists() else {}
    def verify(e):
        mem = e["members"]; key = hashlib.sha1("|".join(sorted(m["text"] for m in mem)).encode()).hexdigest()[:16]
        if key in cache: return cache[key]
        items = [{"id": f"m{i}", "site": m["site"][:14], "statement": m["text"]} for i, m in enumerate(mem)]
        prompt = ("Below are statements about AI-generated web pages (one or more per website) that an embedding model grouped as similar. Embeddings group by TOPIC, so statements about the same property "
                  "can assert OPPOSITE or different values (e.g. square vs rounded corners; red vs blue links; presence vs absence of a feature). Partition the statements into groups that assert the SAME trait with the "
                  "SAME value or direction (wording may differ). A statement that agrees with no other goes in a group of its own. For each group give one canonical sentence (the most representative wording).\n"
                  'Final answer ONLY JSON: [{"statement": str, "members": ["m0", "m3"]}]. Every id must appear exactly once.\n\n' + json.dumps(items, ensure_ascii=False))
        res = ask_json(prompt, "claude-sonnet-5-5", "merge_verify", entry_sites=len(e["sites"]), n_members=len(mem)); seen, groups = set(), []
        for gr in res:
            ids = [int(x[1:]) for x in gr.get("members", []) if x[1:].isdigit() and int(x[1:]) < len(mem) and int(x[1:]) not in seen]; seen.update(ids)
            if ids: groups.append({"statement": gr.get("statement", ""), "ids": ids})
        for i in range(len(mem)):
            if i not in seen: groups.append({"statement": mem[i]["text"], "ids": [i]})
        cache[key] = groups; return groups
    multi = [e for e in master if len(e["sites"]) >= 2]; print(f"verifying {len(multi)} entries shared by >= 2 sites ...", flush=True)
    with cf.ThreadPoolExecutor(3) as ex: res = dict(zip(map(id, multi), ex.map(verify, multi)))
    json.dump(cache, open(cp, "w"))
    unverified = [{"n_sites": len(e["sites"]), "members": [m["text"] for m in e["members"]]} for e in master]
    new, split = [], 0
    for e in master:
        if id(e) not in res: new.append(e); continue
        gs = res[id(e)]; split += len(gs) > 1
        for gr in gs:
            ne = make_entry([e["members"][i] for i in gr["ids"]]); ne["llm_statement"] = gr["statement"] if len(gr["ids"]) > 1 else None; new.append(ne)
    print(f"verification: {len(master)} -> {len(new)} entries ({split} entries were split because their members stated different values)")
    master = new

# ---------- outputs
out = []
for e in master:
    cs = np.stack([m["vec"] for m in e["members"]]) @ e["cent"]; rep = e["members"][int(cs.argmax())]
    fam = collections.Counter(m["family"] for m in e["members"] if m["family"]).most_common(1)
    out.append({"statement": e.get("llm_statement") or rep["text"], "family": fam[0][0] if fam else "", "n_sites": len(e["sites"]), "sites": sorted(e["sites"]), "n_members": len(e["members"]),
                "cohesion": round(float(cs.mean()), 3), "members": [{"site": m["site"], "text": m["text"]} for m in e["members"]]})
out.sort(key=lambda x: (-x["n_sites"], -x["cohesion"], x["statement"]))
for i, o in enumerate(out, 1): o["id"] = f"K{i:03d}"
json.dump(out, open(MD / "master_observations.json", "w"), indent=1, ensure_ascii=False)
key = [o for o in out if o["n_sites"] >= MINS]; json.dump(key, open(MD / "key_observations.json", "w"), indent=1, ensure_ascii=False)
for name, rows in (("master_observations.csv", out), ("key_observations.csv", key)):
    with open(MD / name, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "statement", "family", "n_sites", "n_members", "cohesion", "sites"])
        for o in rows: w.writerow([o["id"], o["statement"], o["family"], o["n_sites"], o["n_members"], o["cohesion"], ";".join(o["sites"])])
with open(MD / "merge_log.csv", "w", newline="") as f: w = csv.DictWriter(f, list(log[0])); w.writeheader(); w.writerows(log)
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from scipy.cluster.hierarchy import dendrogram
    plt.figure(figsize=(9, 6)); dendrogram(np.array(Z), labels=sites, orientation="left", leaf_font_size=7); plt.xlabel("1 - sheet similarity (matched observations)")
    plt.title("Order in which observation sheets were merged"); plt.tight_layout(); plt.savefig(MD / "sheet_dendrogram.png", dpi=140); plt.close()
except Exception as e: print("dendrogram skipped:", e)
cnt = collections.Counter(o["n_sites"] for o in out)
lines = [f"source={SOURCE} tau={TAU} final_tau={FTAU} model={MODEL} verify={'--no-verify' not in sys.argv}", f"{N} sheets, {len(texts)} observations -> master list of {len(out)} entries; {len(key)} shared by >= {MINS} sites",
         "entries by number of sites sharing: " + ", ".join(f"{k}:{cnt[k]}" for k in sorted(cnt, reverse=True)), "", "top shared observations:"] + [f"  {o['n_sites']:2d} sites  {o['id']}  {o['statement']}" for o in out[:25]]
if unverified: json.dump(unverified, open(MD / "master_observations_unverified.json", "w"), indent=1, ensure_ascii=False)
(MD / "summary.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
