"""Combining judge: merge the ORIGINAL page's observations and the VIBE-CODED page's observations (made separately) into one list that says what is general and what differs.
usage: python pipeline/3_annotate/combine_observations.py <site> [--model claude-opus-5-5]
Reads data/<site>/diff/observations_{original,generated}.json and both pages' DOM facts; writes data/<site>/diff/combined.json:
[{id, observation, category, status, original_ids, generated_ids, element_ids}] where status is
  general         both pages have the trait the same way
  changed         both pages have the dimension, the vibe-coded page differs (the observation states BOTH values)
  generated_only  the vibe-coded page has a trait the original lacks
  original_only   the original has a trait the vibe-coded page lacks (dropped by the agent)
original_ids / generated_ids point to the source observations; element_ids (generated side) are the union of the elements those observations cited. Resumable.
"""
import sys, json, pathlib
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]
from llm import ask_json
from pageio import compact

PROMPT = """Two judges described the SAME website in two renderings, each seeing only one page and not the other: O = the ORIGINAL page, G = a page an AI coding agent built from a content brief of the original (the agent never saw the original's design).
Below: observations by judge O (ids O1..), observations by judge G (ids G1..), and programmatic FACTS measured from each page's DOM (ground truth; never contradict them).
Task: produce ONE combined list of observations that covers every substantive point from both lists, merging the ones that describe the same dimension of the page. Give each combined observation a status:
- "general": both pages have this trait in the same way (a trait of the page that the agent also produced or that the original also has)
- "changed": both pages have this dimension but the G page differs from the O page; the observation must state BOTH values (e.g. "Original sets body text in a serif face; the AI-built page sets it in a system sans-serif")
- "generated_only": the G page has the trait and the O page does not (or O's judge did not mention anything comparable and the facts show it is absent there)
- "original_only": the O page has the trait and the G page does not
Use the facts to settle disagreements and to check absence. Do not invent traits. Stay neutral: no quality judgement. Keep each observation to one trait, specific, citing the evidence.
Final answer ONLY a JSON array of {{"observation": str, "category": str, "status": "general"|"changed"|"generated_only"|"original_only", "original_ids": ["O3"], "generated_ids": ["G7"]}}.

FACTS (original): {fo}
FACTS (AI-built): {fg}
O OBSERVATIONS: {o}
G OBSERVATIONS: {g}"""

def combine(site, model="claude-opus-5-5"):
    root = pathlib.Path("data") / site; dd = root / "diff"; out = dd / "combined.json"
    if out.exists(): return
    O, G = json.load(open(dd / "observations_original.json")), json.load(open(dd / "observations_generated.json"))
    fmt = lambda L, p: [{"id": f"{p}{i + 1}", "observation": x["observation"][:300], "evidence": x.get("evidence", "")[:160]} for i, x in enumerate(L)]
    fo, fg = compact(json.load(open(root / "original/dom.json"))), compact(json.load(open(root / "generated_cli/r1/free/render/dom.json")))
    prompt = PROMPT.format(fo=json.dumps(fo, ensure_ascii=False), fg=json.dumps(fg, ensure_ascii=False), o=json.dumps(fmt(O, "O"), ensure_ascii=False), g=json.dumps(fmt(G, "G"), ensure_ascii=False))
    res = ask_json(prompt, model, "combine", site=site, n_original=len(O), n_generated=len(G))
    cited = {f"G{i + 1}": x.get("element_ids") or [] for i, x in enumerate(G)}; items = []
    for i, r in enumerate(res):
        if r.get("status") not in ("general", "changed", "generated_only", "original_only"): continue
        ids = [e for g in r.get("generated_ids", []) for e in cited.get(g, [])]
        items.append({"id": f"c{i + 1:02d}", "observation": r["observation"], "category": r.get("category", ""), "status": r["status"], "original_ids": r.get("original_ids", []), "generated_ids": r.get("generated_ids", []), "element_ids": list(dict.fromkeys(ids))[:8]})
    json.dump(items, open(out, "w"), indent=1, ensure_ascii=False)

if __name__ == "__main__":
    combine(sys.argv[1], sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-opus-5-5")
