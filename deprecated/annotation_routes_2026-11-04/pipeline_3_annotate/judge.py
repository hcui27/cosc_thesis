"""LLM-in-the-loop diff of two renders via headless Claude Code. Programmatic facts are given as ground truth.
usage: python pipeline/3_annotate/judge.py <out.json> <labelA> <dirA> <labelB> <dirB> [--model MODEL]
Each dir holds desktop.png and dom.json (from render.py). Screenshots are sliced so detail survives downscaling.
Every call is logged to data/ledger.jsonl.
"""
import sys, os, json, re, shutil, subprocess, tempfile, pathlib, time
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
import ledger
from PIL import Image

CLAUDE = os.path.expanduser("~/.local/bin/claude")
SLICE_H = 1300

PROMPT = """You are a web design analyst comparing two renderings of the same web page (desktop only).
Side A = "{la}", Side B = "{lb}".
Files in the current directory (read ONLY these):
- A_facts.json, B_facts.json: facts measured programmatically from each page's DOM. They are GROUND TRUTH: never contradict them, and
  prefer citing them (title, h1 count, fonts, colors, border radii, shadows, semantic tag counts, class stats, etc.) over eyeballing.
- A_slice_*.png, B_slice_*.png: the full-page screenshot cut top-to-bottom into consecutive slices ({na} slices for A, {nb} for B). View every slice.
Task: list concrete differences between A and B with NO predefined rubric: layout, typography, color, imagery handling, component choices,
copy treatment, decoration/effects, DOM/semantic structure. Each item must cite specific facts or visible evidence; do not assert what you cannot verify.
Aim for 30-50 specific observations.
This is NOT a quality review: do not say which page is better, nicer, more polished, accessible or professional. Describe neutrally what each side does, so the traits of each can be catalogued.
Final answer: ONLY a JSON array (no prose, no code fence) of objects
{{"observation": str, "category": str, "evidence": str, "which_side": "A"|"B"|"both"}}, where which_side says which side exhibits the notable feature."""

def slices(png, prefix, out):
    im = Image.open(png).convert("RGB"); n = 0
    for y in range(0, im.height, SLICE_H):
        im.crop((0, y, im.width, min(y + SLICE_H, im.height))).save(out / f"{prefix}_slice_{n:02d}.png"); n += 1
    return n

def parse_json_array(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    i, j = text.find("["), text.rfind("]")
    return json.loads(text[i:j + 1])

def main():
    out_json, la, da, lb, db = sys.argv[1:6]
    model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-sonnet-5-5"
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        for side, d in (("A", da), ("B", db)): shutil.copy2(pathlib.Path(d) / "dom.json", t / f"{side}_facts.json")
        na = slices(pathlib.Path(da) / "desktop.png", "A", t); nb = slices(pathlib.Path(db) / "desktop.png", "B", t)
        prompt = PROMPT.format(la=la, lb=lb, na=na, nb=nb)
        t0 = time.time()
        p = subprocess.run([CLAUDE, "-p", prompt, "--model", model, "--allowedTools", "Read", "--permission-mode", "acceptEdits",
                            "--setting-sources", "", "--output-format", "json"], cwd=t, capture_output=True, text=True, timeout=900)
    res = json.loads(p.stdout)
    if res.get("is_error"): raise RuntimeError(f"claude call failed (is the CLI logged in? run `claude` then /login): {res.get('result')}")
    obs = parse_json_array(res["result"])
    pathlib.Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obs, open(out_json, "w"), indent=1, ensure_ascii=False)
    rec = ledger.log("judge", pair=f"{la}_vs_{lb}", out=out_json, requested_model=model, prompt=prompt, n_observations=len(obs),
                     wall_seconds=round(time.time() - t0, 1), **ledger.usage_from_result(res))
    print(json.dumps({k: rec[k] for k in ("pair", "models", "total_cost_usd", "n_observations", "wall_seconds")}))

if __name__ == "__main__":
    main()
