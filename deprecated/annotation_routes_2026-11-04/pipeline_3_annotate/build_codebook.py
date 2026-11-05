"""Attribute-and-value codebook (alternative to merging statements): embeddings find TOPICS, an LLM defines ATTRIBUTES with closed VALUE sets and codes the statements.
usage: python pipeline/3_annotate/build_codebook.py [--thr 0.32] [--max-topic 40] [--misc-batch 25] [--model claude-sonnet-5-5] [--workers 3] [--max-topics N]
 1. every site-level observation statement (data/analysis/features/site_<site>.json) is embedded (fastembed, BGE-small); agglomerative clustering (cosine, average linkage, distance < thr) forms topics;
    topics larger than --max-topic are re-split with a stricter threshold; singleton statements are batched by family
 2. one LLM call per topic: define 1-4 ATTRIBUTES (a dimension on which pages can differ) with 2-7 mutually exclusive VALUES each, and code each statement to attribute-value pairs (cached per topic)
 3. one consolidation call per family merges attributes that describe the same dimension (unified value set + value mapping), and the codes are remapped
Because values are explicit, "square corners" and "pill corners" can never be merged; granularity is set by the attribute/value definitions, not by a similarity threshold.
Writes data/analysis/codebook/{codebook.json, codebook.csv, observation_codes.csv, site_attribute_values_from_observations.csv, topics/*.json}.
NOTE: 'not mentioned' is not 'absent': observation coding only says what judges noticed; code_pages.py codes every page for every attribute.
"""
import sys, os, csv, json, re, glob, hashlib, collections, pathlib, concurrent.futures as cf
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
import numpy as np
from llm import ask_json
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
THR, MAXT, MISC, MODEL, WORKERS = float(g("--thr", 0.32)), int(g("--max-topic", 40)), int(g("--misc-batch", 25)), g("--model", "claude-sonnet-5-5"), int(g("--workers", 3))
OUT = pathlib.Path("data/analysis"); CD = OUT / "codebook"; (CD / "topics").mkdir(parents=True, exist_ok=True)
FAMILIES = ["typography", "color", "layout", "component", "decoration", "imagery", "copy", "semantic_dom", "other"]

# ---- statements
S = []
for fp in sorted(glob.glob(str(OUT / "features" / "site_*.json"))):
    site = re.sub(r"^site_|\.json$", "", os.path.basename(fp))
    for f in json.load(open(fp))["features"]:
        if f.get("statement"): S.append({"id": f"s{len(S)}", "site": site, "text": f["statement"], "family": f["family"]})
print(f"{len(S)} statements from {len({s['site'] for s in S})} sites", flush=True)

# ---- topics from embeddings
from fastembed import TextEmbedding
from sklearn.cluster import AgglomerativeClustering
E = np.array(list(TextEmbedding("BAAI/bge-small-en-v1.5").embed([s["text"] for s in S])), dtype=np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True)
def cluster(idx, thr):
    if len(idx) < 2: return [list(idx)]
    lab = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average", distance_threshold=thr).fit_predict(E[idx]); out = collections.defaultdict(list)
    for i, l in zip(idx, lab): out[l].append(i)
    return list(out.values())
topics, thr_used = [], THR
def split(idx, thr):
    if len(idx) <= MAXT or thr < 0.12: topics.append(idx); return
    parts = cluster(idx, thr - 0.04)
    if len(parts) == 1: topics.append(idx); return
    for p in parts: split(p, thr - 0.04)
for c in cluster(list(range(len(S))), THR): split(c, THR)
multi = [t for t in topics if len(t) > 1]; singles = [t[0] for t in topics if len(t) == 1]
by_fam = collections.defaultdict(list)
for i in singles: by_fam[S[i]["family"]].append(i)
misc = [v[k:k + MISC] for v in by_fam.values() for k in range(0, len(v), MISC)]
units = [("topic", t) for t in multi] + [("misc", m) for m in misc]
if g("--max-topics", ""): units = units[:int(g("--max-topics", ""))]
print(f"{len(multi)} topics (sizes max {max(map(len, multi))}, median {int(np.median([len(t) for t in multi]))}) + {len(misc)} batches of singletons = {len(units)} LLM calls", flush=True)

# ---- step 2: define attributes + code statements, one call per topic
SCHEMA = ('Final answer ONLY JSON: {"attributes": [{"name": str, "definition": str, "family": str, "values": [{"value": str, "definition": str}]}], '
          '"codes": [{"id": "s12", "attribute": "<attribute name>", "value": "<one of its values>"}]}')
def code_unit(u):
    kind, idx = u; items = [{"id": S[i]["id"], "site": S[i]["site"][:16], "statement": S[i]["text"]} for i in idx]
    key = hashlib.sha1(json.dumps(items, sort_keys=True).encode()).hexdigest()[:14]; fp = CD / "topics" / f"{key}.json"
    if fp.exists(): return json.load(open(fp))
    prompt = (("These statements, from observations of different AI-generated web pages, were grouped by an embedding model because they share a TOPIC. " if kind == "topic" else
               "These statements, from observations of different AI-generated web pages, are mostly unrelated one-off observations. ") +
              "Define the ATTRIBUTES they are about: an attribute is a dimension on which pages can differ (e.g. 'primary button shape'), site-independent and checkable on any page; 1-4 attributes per group "
              "(for unrelated one-offs, one attribute per distinct dimension, skipping statements that are not about design, structure or copy treatment). For each attribute give a closed set of 2-7 mutually "
              "exclusive VALUES that covers the statements and any other page (include a value for 'not present' or 'other' where it makes sense); values must not contain brand names or incidental details "
              "(a colour only if colour IS the attribute). Then CODE each statement to the attribute-value pairs it asserts (a statement may have several). Statements that contradict each other must get DIFFERENT values. "
              f"family is one of {FAMILIES}.\n" + SCHEMA + "\n\nSTATEMENTS:\n" + json.dumps(items, ensure_ascii=False))
    res = ask_json(prompt, MODEL, "codebook_topic", n_statements=len(items), unit=kind)
    ids = {x["id"] for x in items}; attrs = {}
    for a in res.get("attributes", []):
        vals = [v["value"] for v in a.get("values", []) if v.get("value")]
        if a.get("name") and len(vals) >= 2: attrs[a["name"]] = {"name": a["name"], "definition": a.get("definition", ""), "family": a.get("family") if a.get("family") in FAMILIES else "other", "values": a["values"]}
    codes = [c for c in res.get("codes", []) if c.get("id") in ids and c.get("attribute") in attrs and c.get("value") in [v["value"] for v in attrs[c["attribute"]]["values"]]]
    out = {"attributes": list(attrs.values()), "codes": codes}; json.dump(out, open(fp, "w"), indent=1, ensure_ascii=False); return out
with cf.ThreadPoolExecutor(WORKERS) as ex: results = list(ex.map(code_unit, [u for u in units]))
raw = []                                                                            # raw attributes with unique ids
for ti, r in enumerate(results):
    amap = {}
    for a in r["attributes"]: aid = f"R{len(raw):03d}"; amap[a["name"]] = aid; raw.append({**a, "id": aid, "topic": ti, "codes": []})
    for c in r["codes"]: raw[int(amap[c["attribute"]][1:])]["codes"].append((c["id"], c["value"]))
print(f"{len(raw)} raw attributes, {sum(len(a['codes']) for a in raw)} codes", flush=True)

# ---- step 3: consolidate duplicate attributes per family
def consolidate(fam):
    A = [a for a in raw if a["family"] == fam]
    if not A: return fam, []
    if len(A) == 1: return fam, [{"name": A[0]["name"], "definition": A[0]["definition"], "values": A[0]["values"], "sources": [{"attribute": A[0]["id"], "map": {}}]}]
    items = [{"id": a["id"], "name": a["name"], "definition": a["definition"], "values": [v["value"] for v in a["values"]]} for a in A]
    prompt = ("These attributes of web-page design were defined independently from different groups of statements, so several may describe the SAME dimension. Merge duplicates into canonical attributes: "
              "for each canonical attribute give name, definition and ONE unified closed set of 2-7 mutually exclusive values, and for every source attribute a mapping from its old values to the unified values. "
              "Attributes that are genuinely different stay separate (do not merge dimensions that merely relate, e.g. button shape and button fill). Every source id must appear exactly once.\n"
              'Final answer ONLY JSON: [{"name": str, "definition": str, "values": [{"value": str, "definition": str}], "sources": [{"attribute": "R007", "map": {"old value": "new value"}}]}]\n\nATTRIBUTES:\n' + json.dumps(items, ensure_ascii=False))
    return fam, ask_json(prompt, MODEL, "codebook_consolidate", family=fam, n_attributes=len(A))
with cf.ThreadPoolExecutor(WORKERS) as ex: cons = dict(ex.map(consolidate, FAMILIES))
book, codes_final, seen = [], [], set()
rawd = {a["id"]: a for a in raw}
for fam in FAMILIES:
    for c in cons.get(fam, []):
        vals = [v["value"] for v in c.get("values", []) if v.get("value")]; srcs = [s for s in c.get("sources", []) if s.get("attribute") in rawd and s["attribute"] not in seen]
        if len(vals) < 2 or not srcs: continue
        aid = f"A{len(book) + 1:03d}"; entry = {"id": aid, "name": c["name"], "definition": c.get("definition", ""), "family": fam, "values": c["values"], "sources": [s["attribute"] for s in srcs]}
        for s in srcs:
            seen.add(s["attribute"]); mp = s.get("map") or {}
            for sid, val in rawd[s["attribute"]]["codes"]:
                nv = mp.get(val, val); nv = nv if nv in vals else "other"
                st = next(x for x in S if x["id"] == sid); codes_final.append({"statement_id": sid, "site": st["site"], "attribute_id": aid, "value": nv, "text": st["text"]})
        book.append(entry)
for a in raw:                                                                       # raw attributes the consolidation dropped keep their own entry
    if a["id"] not in seen:
        aid = f"A{len(book) + 1:03d}"; book.append({"id": aid, "name": a["name"], "definition": a["definition"], "family": a["family"], "values": a["values"], "sources": [a["id"]]})
        for sid, val in a["codes"]:
            st = next(x for x in S if x["id"] == sid); codes_final.append({"statement_id": sid, "site": st["site"], "attribute_id": aid, "value": val, "text": st["text"]})
for b in book:
    cs = [c for c in codes_final if c["attribute_id"] == b["id"]]; b["n_statements"] = len(cs); b["n_sites_mentioning"] = len({c["site"] for c in cs})
json.dump(book, open(CD / "codebook.json", "w"), indent=1, ensure_ascii=False)
with open(CD / "codebook.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "family", "attribute", "definition", "values", "n_statements", "n_sites_mentioning"])
    for b in book: w.writerow([b["id"], b["family"], b["name"], b["definition"], " | ".join(v["value"] for v in b["values"]), b["n_statements"], b["n_sites_mentioning"]])
with open(CD / "observation_codes.csv", "w", newline="") as f: w = csv.DictWriter(f, list(codes_final[0])); w.writeheader(); w.writerows(codes_final)
sv = collections.defaultdict(lambda: collections.defaultdict(list))
for c in codes_final: sv[c["attribute_id"]][c["site"]].append(c["value"])
sites = sorted({s["site"] for s in S})
with open(CD / "site_attribute_values_from_observations.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["site_id"] + [b["id"] for b in book])
    for s in sites: w.writerow([s] + [collections.Counter(sv[b["id"]][s]).most_common(1)[0][0] if sv[b["id"]].get(s) else "" for b in book])
print(f"codebook: {len(book)} attributes ({sum(len(b['values']) for b in book)} values) from {len(raw)} raw attributes; {len(codes_final)} codes; mentioned by >=3 sites: {sum(b['n_sites_mentioning'] >= 3 for b in book)}")
