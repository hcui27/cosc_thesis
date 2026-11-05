"""PIPELINE 3: annotation (judging, observations -> features, detection, variation analysis). Runner.
usage: python pipeline/3_annotate/run_annotation.py [--stages judge,collate,tier,features,merge,collage,codebook,elements,code,attributes,galleries,detect,adequacy,analyze] [--judges claude-sonnet-5-5,claude-opus-5-5] [--dry-run]
  judge     observe_single.py               two LLM judges (Sonnet, Opus) describe each GENERATED page alone, no original -> data/<site>/observations/r1_free.<judge>.json   (about $0.45 per site)
  collate   collate_sites.py                sites table + flat observation table -> data/analysis/
  tier      check_observations.py           judge agreement + fact check -> tiers A/B/C                                                                         (about $0.11 per site)
  features  observations_to_features.py     observations -> per-site features -> canonical catalog -> data/analysis/features_catalog.json                      (about $2.50)
  merge     embed_merge.py                  embeddings (fastembed, BGE-small) merge each site's observation sheet with the most similar sheets until one master list remains, with the number of sites sharing each observation; an LLM then splits entries whose members state different values (about $1-2)
  collage   feature_collages.py             for every shared observation, locate it on each relevant site's screenshot (one vision call per site, about $0.2) and tile the crops into one collage per observation
  codebook  build_codebook.py               ATTRIBUTE-AND-VALUE scheme: embeddings find topics, an LLM defines attributes with closed value sets and codes the observations (about $5)
  elements  element_map.py                  re-render each page and number its visible elements (free)
  code      code_pages_evidence.py          code EVERY generated page to a value for EVERY attribute AND cite the element ids that show it (about $20); originals are not supported yet (code_pages.py --which original is the old route)
  attributes analyze_attributes.py          offline: value distribution per attribute, modal share, entropy, pages more alike than chance?
  galleries evidence_galleries.py           EXHAUSTIVE galleries: one per attribute value, every page coded with it, every cited element, from the coder's own evidence (free, no LLM calls)
  detect    detect_features.py              programmatic measurements + vision checklist per page -> data/analysis/feature_matrix_generated.csv               (about $0.20 per page)
  adequacy  adequacy.py                     is the catalog adequate? (offline)
  analyze   analyze_variation.py            prevalence, homogenization, paired comparisons, inheritance, drivers (offline)
Not in the default run: contamination_probe.py (--stages probe), detect_features.py --which original (lift vs originals), human grading (deferred), repeat-run noise.
Input from pipeline 2: data/sites.csv, data/sites_check.csv, data/<site>/original/, data/<site>/generated_cli/r1/free/render/. Every stage is resumable.
"""
import sys, csv, subprocess, pathlib
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
HERE = pathlib.Path(__file__).resolve().parent; PY = sys.executable; DRY = "--dry-run" in sys.argv
ORDER = "judge,collate,tier,features,merge,collage,codebook,elements,code,attributes,galleries,detect,adequacy,analyze"
run = lambda cmd: (print("  " + " ".join(str(c) for c in cmd), flush=True), None if DRY else subprocess.run([str(c) for c in cmd], check=True))
SIMPLE = {"collate": ["collate_sites.py"], "tier": ["check_observations.py", "--workers", "3"], "features": ["observations_to_features.py", "--workers", "3"],
          "merge": ["embed_merge.py"], "codebook": ["build_codebook.py"], "elements": ["element_map.py"], "code": ["code_pages_evidence.py", "--workers", "4"], "attributes": ["analyze_attributes.py", "--codes-dir", "data/analysis/codebook_evidence", "--out", "data/analysis/codebook_evidence/analysis"], "galleries": ["evidence_galleries.py"], "collage": ["feature_collages.py"], "detect": ["detect_features.py", "--workers", "3"], "adequacy": ["adequacy.py"], "analyze": ["analyze_variation.py"], "probe": ["contamination_probe.py"]}
for st in g("--stages", ORDER).split(","):
    print(f"[{st}]", flush=True)
    if st == "judge":
        sys.path[:0] = [str(HERE.parent / "shared")]
        ok = {r["site_id"] for r in csv.DictReader(open("data/sites_check.csv")) if r["ok"] == "True"}
        for r in csv.DictReader(open("data/sites.csv")):
            s = r["site_id"]; rd = pathlib.Path(f"data/{s}/generated_cli/r1/free/render")
            if s not in ok or not (rd / "desktop.png").exists(): continue
            for m in g("--judges", "claude-sonnet-5-5,claude-opus-5-5").split(","):
                out = pathlib.Path(f"data/{s}/observations/r1_free.{m}.json")
                if not out.exists(): run([PY, HERE / "observe_single.py", out, rd, "--model", m])
    else: run([PY, HERE / SIMPLE[st][0], *SIMPLE[st][1:]])
