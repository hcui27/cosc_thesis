"""Run the whole pipeline for one site (or all usable sites); every stage is resumable (skips outputs that already exist).

usage: python pipeline/2_build_sites/run_site.py <site_id | --all> [--sites data/sites.csv] [--reps 1] [--stages a,b,...] [--dry-run]
Reads the sites file (category, site_id, url, timestamp). With --all, only sites marked ok in data/sites_check.csv are run. Stages, in order:
  skeleton  Wayback snapshot -> data/<site>/{copy.auto.md, images/, images_manifest.json}   (copy.auto.md is promoted to copy.md if none exists)
  original  render the archived original -> data/<site>/original/{desktop.png, dom.json, text.txt}
  sanitize  strip design clues -> data/<site>/prompt/{copy.md, images/}   (images + sanitized copy; the generator sees only the brief derived from it)
  brief     LLM rewrites the sanitized copy as a designer's content brief (new wording, same facts, no layout/style) -> data/<site>/prompt/brief.md; verbatim copy kept in data/<site>/copy_verbatim.md
  generate  claude -p, <reps> runs with a neutral prompt and NO format instruction -> data/<site>/generated_cli/r<k>/free/
  render    auto-detect the output type (static html / node project), build if needed, render -> .../render/, .../format.json  (no check that the copy was kept: which copy the agent includes is itself data)
Judging and everything after it is pipeline 3 (3_annotate). LLM calls are logged to data/ledger.jsonl.
"""
import sys, csv, json, shutil, subprocess, pathlib, time, traceback

HERE = pathlib.Path(__file__).resolve().parent
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from render import render
from net import wait_for_net
import formats
from sanitize import sanitize
from brief import brief
from skeletonize import Skeleton

PY = sys.executable
VARIANTS = ["free"]  # no format instruction; the stack the agent chooses is detected at render time
STAGES = ["skeleton", "original", "sanitize", "brief", "generate", "render"]  # judging belongs to pipeline 3 (3_annotate/run_annotation.py)

def sh(args, **kw): return subprocess.run([str(a) for a in args], check=True, **kw)

def run(row, reps, stages):
    site = row["site_id"]; root = pathlib.Path("data") / site
    runs = [(f"r{k}", v) for k in range(1, reps + 1) for v in VARIANTS]
    print(f"[{site}] stages={stages} runs={[f'{a}/{b}' for a, b in runs]}", flush=True)
    if "skeleton" in stages and not (root / "images_manifest.json").exists():
        Skeleton(row["url"], row["timestamp"], root).run()
    if not (root / "copy.md").exists() and (root / "copy.auto.md").exists(): shutil.copy2(root / "copy.auto.md", root / "copy.md")
    if "original" in stages and not (root / "original/desktop.png").exists():
        for attempt in range(4):
            wait_for_net()
            try: render(f"https://web.archive.org/web/{row['timestamp']}/{row['url']}", root / "original", wayback=True); break
            except Exception as e:
                if attempt == 3: raise
                print(f"  original render failed ({type(e).__name__}); retrying", flush=True); time.sleep(30)
    if "sanitize" in stages and not (root / "prompt/copy.md").exists() and not (root / "prompt/brief.md").exists(): print("  sanitize:", sanitize(root), flush=True)
    if "brief" in stages and not (root / "prompt/brief.md").exists(): print("  brief:", brief(root), flush=True)
    if "generate" in stages:
        for t, v in runs:
            if not (root / "generated_cli" / t / v / "meta.json").exists():
                wait_for_net(); sh([PY, HERE / "generate.py", site, v, t])
    if "render" in stages:
        for t, v in runs:
            rd = root / "generated_cli" / t / v
            if not rd.exists(): continue
            if not (rd / "render/desktop.png").exists(): formats.build_and_render(rd, rd / "render")
            if not (rd / "render/text.txt").exists(): continue  # build/render failed; see format.json

def main():
    g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    reps = int(g("--reps", 1))
    stages = g("--stages", ",".join(STAGES)).split(",")
    rows = list(csv.DictReader(open(g("--sites", "data/sites.csv"))))
    if sys.argv[1] == "--all":
        ok = {r["site_id"] for r in csv.DictReader(open("data/sites_check.csv")) if r["ok"] == "True"}
        rows = [r for r in rows if r["site_id"] in ok]
    else: rows = [r for r in rows if r["site_id"] == sys.argv[1]]
    if "--dry-run" in sys.argv: print([r["site_id"] for r in rows]); return
    failed = []
    for row in rows:
        try: run(row, reps, stages)
        except Exception: failed.append(row["site_id"]); print(f"[{row['site_id']}] FAILED:\n{traceback.format_exc()}", flush=True)
    print(f"done: {len(rows) - len(failed)}/{len(rows)} sites ok; failed: {failed}")

if __name__ == "__main__":
    main()
