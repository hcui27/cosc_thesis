"""Generate a site variant with headless Claude Code (`claude -p`) from brief.md (a designer-style content brief, not the original wording) + images/ only.

usage: python generate.py <site> free <tag> [--model MODEL]   (no output-format instruction: the agent chooses HTML, a framework, etc.)
Writes data/<site>/generated_cli/<tag>/<variant>/ with: copy.md, images/, PROMPT.txt, the generated site,
transcript.jsonl (stream-json) and meta.json (claude version, model, cost, duration, exit status).
The run starts in a fresh directory containing only the prompt inputs; user/project settings are not loaded.
"""
import sys, json, shutil, subprocess, pathlib, time, os
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
import ledger, formats

BASE = "Build a website from this content. brief.md has the content and images/ has the images."
VARIANTS = {"free": BASE}  # deliberately NO format instruction: whatever stack the agent picks is recorded as data
CLAUDE = os.path.expanduser("~/.local/bin/claude")

def main():
    site, variant, tag = sys.argv[1:4]
    model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else None
    root = pathlib.Path("data") / site
    out = root / "generated_cli" / tag / variant
    if out.exists(): sys.exit(f"{out} exists; pick a new tag")
    out.mkdir(parents=True)
    src = root / "prompt"                                  # sanitized inputs (pipeline/2_build_sites/sanitize.py); never feed raw skeleton output
    if not (src / "brief.md").exists(): sys.exit(f"{src}/brief.md missing: run pipeline/2_build_sites/sanitize.py then brief.py on {root} first")
    shutil.copy2(src / "brief.md", out / "brief.md")
    shutil.copytree(src / "images", out / "images")
    prompt = VARIANTS[variant]; (out / "PROMPT.txt").write_text(prompt + "\n")
    cmd = [CLAUDE, "-p", prompt, "--permission-mode", "acceptEdits", "--allowedTools", "Bash",
           "--setting-sources", "", "--output-format", "stream-json", "--verbose"]
    if model: cmd += ["--model", model]
    t0 = time.time()
    with open(out / "transcript.jsonl", "w") as tr:
        p = subprocess.run(cmd, cwd=out, stdout=tr, stderr=subprocess.PIPE, text=True)
    meta = {"site": site, "variant": variant, "tag": tag, "exit_code": p.returncode,
            "wall_seconds": round(time.time() - t0, 1), "prompt": prompt,
            "claude_version": subprocess.run([CLAUDE, "--version"], capture_output=True, text=True).stdout.strip()}
    for line in open(out / "transcript.jsonl"):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") == "result":
            meta.update({k: d.get(k) for k in ("is_error", "total_cost_usd", "duration_ms", "num_turns")})
            meta["models"] = list((d.get("modelUsage") or {}).keys())
    meta["format"] = formats.detect(out)  # what the agent chose (static html / node project, frameworks, file counts)
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    ledger.log("generate", site=site, variant=variant, tag=tag, out=str(out), **{k: meta.get(k) for k in ("prompt", "claude_version", "exit_code", "wall_seconds", "total_cost_usd", "models")})
    print(json.dumps(meta))

if __name__ == "__main__":
    main()
