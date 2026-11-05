"""Spot-check feature-to-evidence links with a model other than the one that clustered them.
usage: python pipeline/3_annotate/spotcheck.py <diffs_dir> [--n 25] [--seed 0] [--model claude-opus-5-5]
Reads features_candidates.json + features_input.json; writes spotcheck.json (per-link verdicts) and prints support rates.
"""
import sys, os, json, random, collections
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from llm import ask_json

d = sys.argv[1]; g = lambda k, dflt: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else dflt
n, seed, model = int(g("--n", 25)), int(g("--seed", 0)), g("--model", "claude-opus-5-5")
feats = json.load(open(f"{d}/features_candidates.json")); obs = {o["id"]: o for o in json.load(open(f"{d}/features_input.json"))}
random.Random(seed).shuffle(feats); sample = feats[:n]
items = [{"feature_id": f["feature_id"], "feature": f["name"], "definition": f["definition"],
          "cited": [{"id": e, "observation": obs[e]["observation"], "evidence": obs[e]["evidence"]} for e in f["evidence_ids"] if e in obs]} for f in sample]
prompt = ("Audit candidate website-style features. For each feature, judge each cited observation: does it genuinely support the feature "
          "as defined (a trait of the regenerated site matching the definition)? Use verdicts 'yes', 'partial' (related but not the same trait), or 'no'.\n"
          'Final answer ONLY a JSON array: [{"feature_id": str, "links": [{"id": str, "verdict": "yes"|"partial"|"no", "why": str (<=15 words)}]}].\n\n'
          + json.dumps(items, ensure_ascii=False))
res = ask_json(prompt, model, "spotcheck", features_checked=len(sample))
json.dump(res, open(f"{d}/spotcheck.json", "w"), indent=1, ensure_ascii=False)
c = collections.Counter(l["verdict"] for r in res for l in r["links"]); tot = sum(c.values())
print(f"{len(res)} features, {tot} links:", dict(c), f"-> strict support {100*c['yes']/tot:.0f}%, lenient {100*(c['yes']+c['partial'])/tot:.0f}%")
bad = [(r["feature_id"], l["id"], l["verdict"], l["why"]) for r in res for l in r["links"] if l["verdict"] != "yes"]
for b in bad: print(" ", *b)
