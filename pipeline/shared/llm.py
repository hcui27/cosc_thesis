"""Tiny helper: one headless Claude Code call that returns parsed JSON, logged to the ledger."""
import os, re, json, subprocess, time, tempfile, sys
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
import ledger
CLAUDE = os.path.expanduser("~/.local/bin/claude")

def ask_json(prompt, model, kind, **log_fields):
    t0 = time.time()
    with tempfile.TemporaryDirectory() as t:
        p = subprocess.run([CLAUDE, "-p", prompt, "--model", model, "--allowedTools", "", "--setting-sources", "",
                            "--output-format", "json"], cwd=t, capture_output=True, text=True, timeout=900)
    res = json.loads(p.stdout)
    if res.get("is_error"): raise RuntimeError(f"claude call failed (is the CLI logged in? run `claude` then /login): {res.get('result')}")
    text = re.sub(r"^```(?:json)?|```$", "", res["result"].strip(), flags=re.M).strip()
    i = min([x for x in (text.find("["), text.find("{")) if x >= 0]); j = max(text.rfind("]"), text.rfind("}"))
    ledger.log(kind, requested_model=model, prompt=prompt, wall_seconds=round(time.time() - t0, 1), **log_fields, **ledger.usage_from_result(res))
    return json.loads(text[i:j + 1])

def ask_json_with_files(prompt, model, kind, files, **log_fields):
    """Like ask_json but copies `files` (paths) into the call's working directory and lets the model Read them (images, text)."""
    import shutil, pathlib
    t0 = time.time()
    with tempfile.TemporaryDirectory() as t:
        for f in files: shutil.copy2(f, pathlib.Path(t) / pathlib.Path(f).name)
        p = subprocess.run([CLAUDE, "-p", prompt, "--model", model, "--allowedTools", "Read", "--permission-mode", "acceptEdits", "--setting-sources", "",
                            "--output-format", "json"], cwd=t, capture_output=True, text=True, timeout=900)
    res = json.loads(p.stdout)
    if res.get("is_error"): raise RuntimeError(f"claude call failed (is the CLI logged in? run `claude` then /login): {res.get('result')}")
    text = re.sub(r"^```(?:json)?|```$", "", res["result"].strip(), flags=re.M).strip()
    i = min([x for x in (text.find("["), text.find("{")) if x >= 0]); j = max(text.rfind("]"), text.rfind("}"))
    ledger.log(kind, requested_model=model, prompt=prompt, wall_seconds=round(time.time() - t0, 1), **log_fields, **ledger.usage_from_result(res))
    return json.loads(text[i:j + 1])

def ask_text(prompt, model, kind, **log_fields):
    """One headless Claude Code call that returns the reply as plain text (no tools), logged to the ledger."""
    t0 = time.time()
    with tempfile.TemporaryDirectory() as t:
        p = subprocess.run([CLAUDE, "-p", prompt, "--model", model, "--allowedTools", "", "--setting-sources", "", "--output-format", "json"], cwd=t, capture_output=True, text=True, timeout=900)
    res = json.loads(p.stdout)
    if res.get("is_error"): raise RuntimeError(f"claude call failed (is the CLI logged in? run `claude` then /login): {res.get('result')}")
    ledger.log(kind, requested_model=model, prompt=prompt, wall_seconds=round(time.time() - t0, 1), **log_fields, **ledger.usage_from_result(res))
    return res["result"].strip()
