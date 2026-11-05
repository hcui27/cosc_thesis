"""Observation judge for ONE page, original or vibe-coded, seen alone (never together with the other).
usage: python pipeline/3_annotate/observe_page.py <site> <original|generated> [--model claude-sonnet-5-5]
original  -> reads data/<site>/original/{desktop.png, dom.json}; writes data/<site>/diff/observations_original.json
generated -> reads data/<site>/generated_cli/r1/free/render/{desktop.png, dom.json} and its evidence/{elements.txt}; writes data/<site>/diff/observations_generated.json,
             each observation also cites the numbered elements that show it (element_ids), so galleries can crop them later (run element_map.py first).
Items: {observation, category, evidence[, element_ids]}. Neutral description, 30-50 observations, no quality judgement. Resumable. Every call is logged to data/ledger.jsonl.
"""
import sys, json, shutil, subprocess, tempfile, pathlib, time
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]
import ledger
from pageio import slices, parse_json, CLAUDE

PROMPT = """You are a web design analyst describing ONE rendering of a web page (desktop only).
Files in the current directory (read ONLY these):
- facts.json: facts measured programmatically from the page's DOM. They are GROUND TRUTH: never contradict them, and prefer citing them (title, h1 count, fonts, colors, border radii, shadows, semantic tag counts, class stats, etc.) over eyeballing.
- slice_*.png: the full-page screenshot cut top-to-bottom into consecutive slices ({n} slices). View every slice.
{elements}Task: list concrete observations about this page with NO predefined rubric: layout, typography, color, imagery handling, component choices, copy treatment, decoration/effects, DOM/semantic structure.
Each item must cite specific facts or visible evidence; do not assert what you cannot verify. Aim for 30-50 specific observations.
This is NOT a quality review: do not say the page is good, nice, polished, accessible or professional. Describe neutrally what the page does, so its traits can be catalogued.
Final answer: ONLY a JSON array (no prose, no code fence) of objects {{"observation": str, "category": str, "evidence": str{cite}}}."""
ELEM = "- elements.txt: the page's numbered visible elements (id | parent | tag | x,y,w,h | text). Use it to say WHERE each observation applies.\n"

def observe(site, side, model="claude-sonnet-5-5"):
    root = pathlib.Path("data") / site; d = root / "original" if side == "original" else root / "generated_cli/r1/free/render"
    out = root / "diff" / f"observations_{side}.json"
    if out.exists(): return
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); shutil.copy2(d / "dom.json", t / "facts.json"); n = slices(d / "desktop.png", "slice", t)
        gen = side == "generated" and (d / "evidence" / "elements.txt").exists()
        if gen: shutil.copy2(d / "evidence" / "elements.txt", t / "elements.txt")
        prompt = PROMPT.format(n=n, elements=ELEM if gen else "", cite=', "element_ids": [up to 6 element ids from elements.txt that show it, or [] if it is page-wide]' if gen else ""); t0 = time.time()
        p = subprocess.run([CLAUDE, "-p", prompt, "--model", model, "--allowedTools", "Read", "--permission-mode", "acceptEdits", "--setting-sources", "", "--output-format", "json"], cwd=t, capture_output=True, text=True, timeout=900)
    res = json.loads(p.stdout)
    if res.get("is_error"): raise RuntimeError(f"claude call failed: {res.get('result')}")
    obs = parse_json(res["result"]); out.parent.mkdir(parents=True, exist_ok=True); json.dump(obs, open(out, "w"), indent=1, ensure_ascii=False)
    ledger.log("observe_" + side, site=site, out=str(out), requested_model=model, prompt=prompt, n_observations=len(obs), wall_seconds=round(time.time() - t0, 1), **ledger.usage_from_result(res))

if __name__ == "__main__":
    observe(sys.argv[1], sys.argv[2], sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-sonnet-5-5")
