"""PIPELINE 3: annotation (redesigned 2026-11-04). Runner.
usage: python pipeline/3_annotate/run_annotation.py [--sites a,b,...] [--stages elements,observe,combine,tag,master,galleries,collages,seed] [--seed v1_3] [--min-sites 2] [--workers 4] [--dry-run]
  elements   element_map.py         number the visible elements of each vibe-coded page (free) -> <render>/evidence/{page.png, elements.json, elements.txt}
  observe    observe_page.py        ONE Sonnet judge describes the ORIGINAL page alone and, separately, the VIBE-CODED page alone (the second cites element ids)  (about $0.25 each)
                                    -> data/<site>/diff/observations_{original,generated}.json
  combine    combine_observations.py   ONE Opus judge merges the two lists into general / changed / generated_only / original_only observations (about $0.5 per site)
                                    -> data/<site>/diff/combined.json
  tag        tag_observations.py    every combined observation gets attribute(s) and value(s) (original_value / generated_value), vocabulary shared across sites (about $0.2 per site)
                                    -> data/<site>/diff/diff.json (the n diffs for n sites), data/diff_vocab.json
  master     build_master.py        hierarchical master list: family -> attribute -> value, counts of sites for general / changed / vibe-coded-only, one-line summaries (about $0.5 per family)
                                    -> data/master/master_list.{json,md}
  collages   feature_collages.py  one vision call per site to locate each common attribute, then one collage per attribute (needs LLM calls) -> data/master/collages/
  galleries  evidence_galleries.py  screenshot sheets of what each common feature looks like on the vibe-coded pages (free) -> data/master/galleries/
  seed       match_seed.py          LAST: match the master list to the closed seed list (the corpus); which seed items the observations corroborate, what they add -> data/master/seed_match_<seed>.{json,csv,md}
Input from pipeline 2: data/sites.csv, data/<site>/original/, data/<site>/generated_cli/r1/free/render/. Every stage is resumable. (Archived routes: deprecated/annotation_routes_2026-11-04/.)
"""
import sys, csv, subprocess, pathlib, concurrent.futures as cf
sys.path[:0] = [str(pathlib.Path(__file__).resolve().parents[1] / "shared")]
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
HERE = pathlib.Path(__file__).resolve().parent; PY = sys.executable; DRY = "--dry-run" in sys.argv; WORKERS = int(g("--workers", 4))
ORDER = "elements,observe,combine,tag,master,galleries,collages,seed"
ok = {r["site_id"] for r in csv.DictReader(open("data/sites_check.csv")) if r["ok"] == "True"}
sites = [s for s in g("--sites", "").split(",") if s] or [r["site_id"] for r in csv.DictReader(open("data/sites.csv")) if r["site_id"] in ok and pathlib.Path(f"data/{r['site_id']}/generated_cli/r1/free/render/desktop.png").exists()]
run = lambda cmd: (print("  " + " ".join(str(c) for c in cmd), flush=True), None if DRY else subprocess.run([str(c) for c in cmd], check=True))
def par(fn, jobs):
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        for j, f in [(j, ex.submit(fn, j)) for j in jobs]:
            try: f.result()
            except Exception as e: print("  FAILED", j, type(e).__name__, str(e)[:150], flush=True)
for st in g("--stages", ORDER).split(","):
    print(f"[{st}] {len(sites)} sites", flush=True)
    if st == "elements": run([PY, HERE / "element_map.py", "--sites", ",".join(sites)])
    elif st == "observe":
        sys.path.insert(0, str(HERE)); from observe_page import observe
        jobs = [(s, side) for s in sites for side in ("original", "generated") if not pathlib.Path(f"data/{s}/diff/observations_{side}.json").exists()]
        print(f"  {len(jobs)} observation calls", flush=True)
        if not DRY: par(lambda j: (observe(*j), print("  observed", *j, flush=True)), jobs)
    elif st == "combine":
        sys.path.insert(0, str(HERE)); from combine_observations import combine
        jobs = [s for s in sites if not pathlib.Path(f"data/{s}/diff/combined.json").exists() and pathlib.Path(f"data/{s}/diff/observations_generated.json").exists() and pathlib.Path(f"data/{s}/diff/observations_original.json").exists()]
        if not DRY: par(lambda s: (combine(s), print("  combined", s, flush=True)), jobs)
    elif st == "tag": run([PY, HERE / "tag_observations.py", "--sites", ",".join(sites)])
    elif st == "master": run([PY, HERE / "build_master.py", "--min-sites", g("--min-sites", 2)])
    elif st == "galleries": run([PY, HERE / "evidence_galleries.py", "--min-sites", g("--min-sites", 2)])
    elif st == "collages": run([PY, HERE / "feature_collages.py", "--min-sites", g("--min-sites", 2), "--workers", WORKERS])
    elif st == "seed": run([PY, HERE / "match_seed.py", "--seed", g("--seed", "v1_3"), "--min-sites", g("--min-sites", 2)])
