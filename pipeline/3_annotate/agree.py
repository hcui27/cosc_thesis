"""Judge agreement: for each observation in list 1, is the same difference also made in list 2 (and vice versa)?
usage: python pipeline/3_annotate/agree.py <judge1.json> <judge2.json> <out.json> [--model claude-sonnet-5-5]
"""
import sys, os, json
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from llm import ask_json

a, b, out = (json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), sys.argv[3])
model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-sonnet-5-5"
fmt = lambda L, p: [{"id": f"{p}{i}", "observation": o["observation"]} for i, o in enumerate(L)]
prompt = ("Two judges compared the same pair of web pages. For every item in LIST1 say which items in LIST2 make the SAME substantive point "
          "(same trait of the pages, same direction), and vice versa. Different wording is fine; merely related topics are not a match.\n"
          'Final answer ONLY JSON: {"list1_matches": [{"id": str, "matches": [list2 ids]}], "list2_matches": [{"id": str, "matches": [list1 ids]}]}\n\n'
          "LIST1:\n" + json.dumps(fmt(a, "A"), ensure_ascii=False) + "\n\nLIST2:\n" + json.dumps(fmt(b, "B"), ensure_ascii=False))
r = ask_json(prompt, model, "agreement")
json.dump(r, open(out, "w"), indent=1)
m1 = sum(bool(x["matches"]) for x in r["list1_matches"]); m2 = sum(bool(x["matches"]) for x in r["list2_matches"])
print(f"judge1: {m1}/{len(a)} observations also made by judge2 ({100*m1/len(a):.0f}%); judge2: {m2}/{len(b)} also made by judge1 ({100*m2/len(b):.0f}%)")
