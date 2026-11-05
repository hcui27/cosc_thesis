"""CONTROLLED ARM: same 28 generated pages, same downstream stages, but the judges COMPARE original (A) vs generated (B) (judge.py) instead of describing the generated page alone.
usage: python pipeline/3_annotate/run_compare_arm.py [--stages setup,judge,collate,tier,features,codebook,code,attributes,galleries,seed,compare]   (resumable)
Runs in arms/compare/ whose data/<site>/ links to the shared original/, generated_cli/ (so identical pages, identical element ids) and has its OWN observations/ and data/analysis*/ trees.
Everything the observation arm wrote under data/analysis* is untouched. The only variable that differs between arms is the judge type.
"""
import sys, csv, os, subprocess, pathlib, concurrent.futures as cf
ROOT = pathlib.Path(__file__).resolve().parents[2]; ARM = ROOT / "arms" / "compare"; HERE = pathlib.Path(__file__).resolve().parent; PY = sys.executable
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MODELS = ["claude-sonnet-5-5", "claude-opus-5-5"]
sh = lambda cmd: (print("  " + " ".join(map(str, cmd)), flush=True), subprocess.run([str(c) for c in cmd], cwd=ARM, check=True, env={**os.environ, "ARM": "compare"}))
sites = [r["site_id"] for r in csv.DictReader(open(ROOT / "data/sites.csv")) if (ROOT / f"data/{r['site_id']}/generated_cli/r1/free/render/desktop.png").exists()]
for st in g("--stages", "setup,judge,collate,tier,features,codebook,code,attributes,galleries,seed,compare").split(","):
    print(f"[{st}]", flush=True)
    if st == "setup":
        (ARM / "data").mkdir(parents=True, exist_ok=True)
        for n in ("sites.csv", "sites_check.csv", "frames", "ledger.jsonl"):
            if not (ARM / "data" / n).exists(): (ARM / "data" / n).symlink_to(ROOT / "data" / n)
        if not (ARM / "seed_attributes").exists(): (ARM / "seed_attributes").symlink_to(ROOT / "seed_attributes")
        for s in sites:
            d = ARM / "data" / s; (d / "observations").mkdir(parents=True, exist_ok=True)
            for n in ("original", "generated_cli", "copy.md", "images"):
                if not (d / n).exists() and (ROOT / "data" / s / n).exists(): (d / n).symlink_to(ROOT / "data" / s / n)
    elif st == "judge":
        jobs = [(s, m) for s in sites for m in MODELS if not (ARM / f"data/{s}/observations/r1_free.{m}.json").exists()]
        def run(j):
            s, m = j; rd = ROOT / f"data/{s}/generated_cli/r1/free/render"
            r = subprocess.run([PY, HERE / "judge.py", ARM / f"data/{s}/observations/r1_free.{m}.json", "original", ROOT / f"data/{s}/original", "generated", rd, "--model", m], cwd=ARM, capture_output=True, text=True)
            print("  judged", s, m, "ok" if r.returncode == 0 else "FAILED " + r.stderr[-150:], flush=True)
        with cf.ThreadPoolExecutor(4) as ex: list(ex.map(run, jobs))
    elif st == "collate": sh([PY, HERE / "collate_sites.py"])
    elif st == "tier": sh([PY, HERE / "check_observations.py", "--mode", "compare", "--workers", "3"])
    elif st == "features": sh([PY, HERE / "observations_to_features.py", "--workers", "3"])
    elif st == "codebook": sh([PY, HERE / "build_codebook.py"])
    elif st == "code": sh([PY, HERE / "code_pages_evidence.py", "--workers", "4"])
    elif st == "attributes": sh([PY, HERE / "analyze_attributes.py", "--codes-dir", "data/analysis/codebook_evidence", "--out", "data/analysis/codebook_evidence/analysis"])
    elif st == "galleries": sh([PY, HERE / "evidence_galleries.py"])
    elif st == "seed":      # seed coding depends only on the pages and the fixed seed list, so the observation arm's cached codes are reused (identical by construction)
        import shutil; (ARM / "data/analysis_seed/pages").mkdir(parents=True, exist_ok=True)
        for f in (ROOT / "data/analysis_seed/pages").glob("*.json"): shutil.copy2(f, ARM / "data/analysis_seed/pages" / f.name) if not (ARM / "data/analysis_seed/pages" / f.name).exists() else None
        sh([PY, HERE / "seed_pilot.py", "--stage", "all"])
    elif st == "compare": sh([PY, HERE / "compare_seed_vs_codebook.py"])
