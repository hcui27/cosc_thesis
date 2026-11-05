"""Observation-only judge: describe ONE rendered page, with no original to compare against (arm B of the judge A/B test, see ab_judges.py).
usage: python pipeline/3_annotate/observe_single.py <out.json> <dir> [--model MODEL]
<dir> holds desktop.png and dom.json (from render.py). Same slicing, ground-truth facts, neutral tone and 30-50 observation target as judge.py, but one page and no which_side.
Every call is logged to data/ledger.jsonl.
"""
import sys, os, json, shutil, subprocess, tempfile, pathlib, time
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]
import ledger
from judge import slices, parse_json_array, CLAUDE

PROMPT = """You are a web design analyst describing ONE rendering of a web page (desktop only).
Files in the current directory (read ONLY these):
- facts.json: facts measured programmatically from the page's DOM. They are GROUND TRUTH: never contradict them, and
  prefer citing them (title, h1 count, fonts, colors, border radii, shadows, semantic tag counts, class stats, etc.) over eyeballing.
- slice_*.png: the full-page screenshot cut top-to-bottom into consecutive slices ({n} slices). View every slice.
Task: list concrete observations about this page with NO predefined rubric: layout, typography, color, imagery handling, component choices,
copy treatment, decoration/effects, DOM/semantic structure. Each item must cite specific facts or visible evidence; do not assert what you cannot verify.
Aim for 30-50 specific observations.
This is NOT a quality review: do not say the page is good, nice, polished, accessible or professional. Describe neutrally what the page does, so its traits can be catalogued.
Final answer: ONLY a JSON array (no prose, no code fence) of objects {{"observation": str, "category": str, "evidence": str}}."""

def main():
    out_json, d = sys.argv[1:3]
    model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-sonnet-5-5"
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); shutil.copy2(pathlib.Path(d) / "dom.json", t / "facts.json")
        n = slices(pathlib.Path(d) / "desktop.png", "slice", t); prompt = PROMPT.format(n=n); t0 = time.time()
        p = subprocess.run([CLAUDE, "-p", prompt, "--model", model, "--allowedTools", "Read", "--permission-mode", "acceptEdits", "--setting-sources", "", "--output-format", "json"], cwd=t, capture_output=True, text=True, timeout=900)
    res = json.loads(p.stdout)
    if res.get("is_error"): raise RuntimeError(f"claude call failed: {res.get('result')}")
    obs = parse_json_array(res["result"]); pathlib.Path(out_json).parent.mkdir(parents=True, exist_ok=True); json.dump(obs, open(out_json, "w"), indent=1, ensure_ascii=False)
    rec = ledger.log("observe", out=out_json, requested_model=model, prompt=prompt, n_observations=len(obs), wall_seconds=round(time.time() - t0, 1), **ledger.usage_from_result(res))
    print(json.dumps({k: rec[k] for k in ("models", "total_cost_usd", "n_observations", "wall_seconds")}))

if __name__ == "__main__":
    main()
