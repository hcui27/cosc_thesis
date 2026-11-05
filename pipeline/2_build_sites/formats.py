"""Format-agnostic handling of whatever the generator built (no format instruction is given to it).
detect(run_dir)  -> {"kind": "static_html" | "node_project" | "unknown", "root": ..., "frameworks": [...], "files": ..., "entry": ...}
build_and_render(run_dir, out_dir) -> detection dict + {"render_status": "ok"|"build_failed"|"no_output"|"render_failed", "error": ...}
Static output is always served over a local HTTP server (absolute paths like /images/x.png then work); node projects are built
(npm install if needed, npm run build) and the static build directory is served. Results are written to <run_dir>/format.json.
"""
import json, pathlib, subprocess, functools, threading, http.server
from render import render

IGNORE = {"node_modules", ".git", "render", "images", "dist_old"}
HARNESS = {"copy.md", "PROMPT.txt", "meta.json", "transcript.jsonl", "format.json", "fidelity.json"}  # files the pipeline itself puts in the run dir
FRAMEWORKS = ["react", "vue", "svelte", "next", "nuxt", "astro", "solid-js", "@angular/core", "preact", "vite", "tailwindcss", "bootstrap", "gatsby", "@sveltejs/kit"]
OUTDIRS = ["dist", "build", "out", "public", ".output/public", "docs"]

def _files(root):
    return [p for p in root.rglob("*") if p.is_file() and p.name not in HARNESS and not (set(p.relative_to(root).parts) & IGNORE)]

def detect(run_dir):
    run_dir = pathlib.Path(run_dir)
    pk = sorted((p for p in run_dir.rglob("package.json") if "node_modules" not in p.parts and len(p.relative_to(run_dir).parts) <= 3), key=lambda p: len(p.parts))
    files = _files(run_dir)
    ext = lambda e: sum(f.suffix.lower() == e for f in files)
    info = {"files": {"html": ext(".html"), "css": ext(".css"), "js": ext(".js") + ext(".jsx") + ext(".ts") + ext(".tsx"), "other_code": ext(".vue") + ext(".svelte")}}
    if pk:
        d = json.loads(pk[0].read_text() or "{}"); deps = {**d.get("dependencies", {}), **d.get("devDependencies", {})}
        info.update(kind="node_project", root=str(pk[0].parent.relative_to(run_dir)), frameworks=[f for f in FRAMEWORKS if f in deps], scripts=list(d.get("scripts", {})))
        return info
    html = sorted((f for f in files if f.suffix.lower() in (".html", ".htm")), key=lambda p: (p.name != "index.html", len(p.parts)))
    if html:
        info.update(kind="static_html", root=str(html[0].parent.relative_to(run_dir)), entry=html[0].name, frameworks=[])
        txt = html[0].read_text(errors="ignore").lower()          # CDN-loaded libraries are part of the stack too
        info["frameworks"] = [n for n, k in (("tailwindcss", "tailwind"), ("react", "react"), ("vue", "vue"), ("bootstrap", "bootstrap"), ("alpine", "alpine")) if k in txt]
        info["multi_file"] = len(files) - ext(".png") - ext(".jpg") - ext(".svg") > 1
        return info
    info.update(kind="unknown", root=".", frameworks=[]); return info

def _serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k): pass
    h = functools.partial(Quiet, directory=str(directory))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv

def build_and_render(run_dir, out_dir, timeout=600):
    run_dir = pathlib.Path(run_dir); info = detect(run_dir); info["render_status"] = "ok"; serve_dir = None
    try:
        if info["kind"] == "static_html": serve_dir = run_dir / info["root"]
        elif info["kind"] == "node_project":
            proj = run_dir / info["root"]
            if not (proj / "node_modules").exists(): subprocess.run(["npm", "install", "--silent"], cwd=proj, check=True, timeout=timeout, capture_output=True)
            if "build" in info["scripts"]: subprocess.run(["npm", "run", "build", "--silent"], cwd=proj, check=True, timeout=timeout, capture_output=True)
            serve_dir = next((proj / o for o in OUTDIRS if (proj / o / "index.html").exists()), None)
            if serve_dir is None and (proj / "index.html").exists() and "build" not in info["scripts"]: serve_dir = proj
            if serve_dir is None: info["render_status"] = "no_output"
        else: info["render_status"] = "no_output"
    except Exception as e:
        info["render_status"] = "build_failed"; info["error"] = f"{type(e).__name__}: {str(getattr(e, 'stderr', '') or e)[:300]}"
    if info["render_status"] == "ok":
        srv = _serve(serve_dir)
        try: render(f"http://127.0.0.1:{srv.server_address[1]}/", out_dir)
        except Exception as e: info["render_status"] = "render_failed"; info["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        finally: srv.shutdown()
    (run_dir / "format.json").write_text(json.dumps(info, indent=1))
    return info
