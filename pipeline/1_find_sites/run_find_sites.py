"""PIPELINE 1: finding the websites themselves. Runner.
usage: python pipeline/1_find_sites/run_find_sites.py [--stages sample,label,draw] [--n 300] [--seed 0] [--min-english 0.90] [--target 30] [--dry-run]
  sample  build_frame.py          random domains ranked > 100,000 on the 2021-06-01 Tranco list; fetch each homepage from Wayback (<= 2021) -> data/frames/sample_unpopular.csv, data/frames/html/
  label   label_categories.py     LLM labels each saved homepage with a Cloudflare top-level category, language and confidence -> data/frames/cf_labels.csv   (about $2.60 per 270 pages)
  draw    draw_cf.py              English-only, per-category draw (2 per fulfilled category, topped up to --target) -> data/frames/sites_draw_cf.csv, replacements_cf.csv, qualifying_sites.md
Manual helper, run separately: review_english.py (threshold review sheet). Output of this pipeline: the DRAW. Pipeline 2 takes it from there.
Needs data/frames/tranco_2021/tranco_2021-06-01.csv. Every stage is resumable.
"""
import sys, subprocess, pathlib
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
HERE = pathlib.Path(__file__).resolve().parent; PY = sys.executable
STAGES = g("--stages", "sample,label,draw").split(",")
CMDS = {"sample": [PY, HERE / "build_frame.py", "--n", g("--n", 300), "--seed", g("--seed", 0), "--min-english", g("--min-english", 0.90)],
        "label": [PY, HERE / "label_categories.py"],
        "draw": [PY, HERE / "draw_cf.py", "--target", g("--target", 30), "--seed", g("--seed", 0)]}
for st in STAGES:
    cmd = [str(c) for c in CMDS[st]]; print(f"[{st}] {' '.join(cmd)}", flush=True)
    if "--dry-run" not in sys.argv: subprocess.run(cmd, check=True)
