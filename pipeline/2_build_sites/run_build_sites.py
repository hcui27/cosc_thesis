"""PIPELINE 2: scraping / skeletonizing, then vibe-coding. Runner.
usage: python pipeline/2_build_sites/run_build_sites.py [--stages check,build] [--reps 1] [--draw data/frames/sites_draw_cf.csv] [--replacements data/frames/replacements_cf.csv] [--dry-run]
  check   check_selected.py   per drawn site: fetch the Wayback snapshot, build the skeleton (copy + images), test it is usable (150-3000 words, 2-40 images); a failing site is
                              replaced from the same category -> data/sites.csv (final list), data/sites_check.csv, data/<site>/{copy.auto.md, images/, images_manifest.json, original/snapshot.html}
  build   run_site.py --all   per usable site: render the 2021 original, sanitize (strip design clues) -> prompt/, one Claude Code generation with NO style or format instruction,
                              auto-detect and render whatever it built -> data/<site>/{original/, prompt/, generated_cli/r<k>/free/}
Input: the draw from pipeline 1. Output for pipeline 3: data/sites.csv + data/<site>/original/ + data/<site>/generated_cli/r1/free/render/. Every stage is resumable; stops when Wayback is unreachable.
"""
import sys, subprocess, pathlib
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
HERE = pathlib.Path(__file__).resolve().parent; PY = sys.executable
CMDS = {"check": [PY, HERE / "check_selected.py", g("--draw", "data/frames/sites_draw_cf.csv"), g("--replacements", "data/frames/replacements_cf.csv")],
        "build": [PY, HERE / "run_site.py", "--all", "--sites", "data/sites.csv", "--reps", g("--reps", 1)]}
for st in g("--stages", "check,build").split(","):
    cmd = [str(c) for c in CMDS[st]]; print(f"[{st}] {' '.join(cmd)}", flush=True)
    if "--dry-run" not in sys.argv: subprocess.run(cmd, check=True)
