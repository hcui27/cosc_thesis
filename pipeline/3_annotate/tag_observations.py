"""Tag every combined observation with an ATTRIBUTE (the UI/UX feature it is about) and a VALUE (what happens to that feature on the vibe-coded page relative to the original).
usage: python pipeline/3_annotate/tag_observations.py [--sites a,b] [--model claude-sonnet-5-5]       (sites are tagged one after another so the vocabulary can be shared)
Reads data/<site>/diff/combined.json; writes data/<site>/diff/diff.json (the site's tagged diff) and keeps the running vocabulary in data/diff_vocab.json (attribute -> family, values seen).
Each combined observation gets 1-3 tags {attribute, family, action, value, page_wide}. The attribute is NOT a side ("original"/"generated"): it is the interface feature itself (e.g. "primary navigation", "hero area", "card grid",
"body typeface", "color palette", "call-to-action button", "footer", "image treatment"), named generally so the same feature on other sites gets the same name. The value says what happens to the feature, as
"<action>: <what>" with action one of kept (same on both pages), changed (present on both, treated differently), added (only the vibe-coded page has it), dropped (only the original has it), e.g. "kept: top horizontal bar",
"changed: serif body text becomes sans-serif", "added: sticky translucent header", "dropped: image carousel". The action must match the observation's status (general=kept, changed=changed, generated_only=added, original_only=dropped).
Vocabulary is REUSED across sites; consolidation of near-duplicate attributes and values happens in build_master.py. Resumable per site.
"""
import sys, json, pathlib, csv
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]
from llm import ask_json
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MODEL = g("--model", "claude-sonnet-5-5"); VOC = pathlib.Path("data/diff_vocab.json")
FAMILIES = "typography, color, layout, component, decoration, imagery, copy, semantic_dom, other"
ACTION = {"general": "kept", "changed": "changed", "generated_only": "added", "original_only": "dropped"}
PROMPT = """You tag observations about a web page pair (ORIGINAL page vs a page an AI agent built from a content brief of it) so observations from many websites can be counted together.
For each observation give 1-3 tags. A tag = {{"attribute": the UI/UX FEATURE the observation is about, as a general noun phrase (e.g. "primary navigation", "hero area", "card grid", "body typeface", "color palette", "call-to-action button", "footer", "image treatment", "page layout");
NEVER use "original" or "generated" or the page side as an attribute, "family": one of {fam}, "action": "kept" | "changed" | "added" | "dropped", "value": "<action>: <what happens to that feature>" (action word first, then 2-8 lowercase words saying what the feature is or becomes), "page_wide": true if it is a whole-page property (palette, type scale, overall layout), else false}}.
Action must match the observation's status: general -> kept, changed -> changed, generated_only -> added, original_only -> dropped. The value is about the feature on the AI-built page relative to the original ("changed: serif body text becomes sans-serif", "kept: top horizontal bar", "added: sticky translucent header", "dropped: image carousel").
REUSE an existing attribute and one of its values whenever it fits (EXISTING VOCABULARY below); create a new attribute or value only when none fits. Do not judge quality.
Final answer ONLY a JSON object mapping each observation id to a list of tags.

EXISTING VOCABULARY (attribute [family]: values): {voc}

OBSERVATIONS: {obs}"""

voc = json.load(open(VOC)) if VOC.exists() else {}
sites = [s for s in g("--sites", "").split(",") if s] or sorted(p.parent.parent.name for p in pathlib.Path("data").glob("*/diff/combined.json"))
for s in sites:
    out = pathlib.Path(f"data/{s}/diff/diff.json")
    if out.exists(): continue
    items = json.load(open(f"data/{s}/diff/combined.json"))
    v = "; ".join(f"{a} [{x['family']}]: {' | '.join(x['values'][:10])}" for a, x in sorted(voc.items())) or "(empty: this is the first site)"
    res = ask_json(PROMPT.format(fam=FAMILIES, voc=v, obs=json.dumps([{"id": i["id"], "status": i["status"], "observation": i["observation"]} for i in items], ensure_ascii=False)), MODEL, "tag_observations", site=s, n_obs=len(items))
    for it in items:
        tags = []
        for t in (res.get(it["id"]) or [])[:3]:
            if not isinstance(t, dict) or not t.get("attribute"): continue
            a = t["attribute"].strip().lower(); fam = t.get("family") if t.get("family") in FAMILIES.split(", ") else "other"
            act = ACTION[it["status"]]; val = (t.get("value") or "").strip().lower()
            if not val: continue
            if not val.startswith(act + ":"): val = act + ": " + val.split(":", 1)[-1].strip()      # force the action word to match the status
            tag = {"attribute": a, "family": fam, "action": act, "value": val, "page_wide": bool(t.get("page_wide"))}; tags.append(tag)
            e = voc.setdefault(a, {"family": fam, "values": []})
            if val not in e["values"]: e["values"].append(val)
        it["tags"] = tags
    json.dump({"site": s, "n_observations": len(items), "observations": items}, open(out, "w"), indent=1, ensure_ascii=False); json.dump(voc, open(VOC, "w"), indent=1, ensure_ascii=False)
    print(f"  tagged {s}: {len(items)} observations, vocabulary {len(voc)} attributes", flush=True)
