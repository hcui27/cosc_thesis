# Pipeline 3: annotation

Runner `run_annotation.py`; its docstring is reproduced here.

```
PIPELINE 3: annotation (judging, observations -> features, detection, variation analysis). Runner.
usage: python pipeline/3_annotate/run_annotation.py [--stages judge,collate,tier,features,merge,collage,codebook,code,attributes,galleries,detect,adequacy,analyze] [--judges claude-sonnet-5-5,claude-opus-5-5] [--dry-run]
  judge     judge.py                        two LLM judges compare each original with its generated page -> data/<site>/diffs/original_vs_r1_free.<judge>.json   (about $0.65 per site)
  collate   collate_sites.py                sites table + flat observation table -> data/analysis/
  tier      check_observations.py           judge agreement + fact check -> tiers A/B/C                                                                         (about $0.11 per site)
  features  observations_to_features.py     observations -> per-site features -> canonical catalog -> data/analysis/features_catalog.json                      (about $2.50)
  merge     embed_merge.py                  embeddings (fastembed, BGE-small) merge each site's observation sheet with the most similar sheets until one master list remains, with the number of sites sharing each observation; an LLM then splits entries whose members state different values (about $1-2)
  collage   feature_collages.py             for every shared observation, locate it on each relevant site's screenshot (one vision call per site, about $0.2) and tile the crops into one collage per observation
  codebook  build_codebook.py               ATTRIBUTE-AND-VALUE scheme: embeddings find topics, an LLM defines attributes with closed value sets and codes the observations (about $5)
  code      code_pages.py                   code EVERY generated page to a value for EVERY attribute (vision + measurements; about $8); --which original codes the 2021 originals too
  attributes analyze_attributes.py          offline: value distribution per attribute, modal share, entropy, pages more alike than chance?
  galleries attribute_galleries.py          EXHAUSTIVE galleries: one per attribute value, every page coded with it, every located instance (about $11)
  detect    detect_features.py              programmatic measurements + vision checklist per page -> data/analysis/feature_matrix_generated.csv               (about $0.20 per page)
  adequacy  adequacy.py                     is the catalog adequate? (offline)
  analyze   analyze_variation.py            prevalence, homogenization, paired comparisons, inheritance, drivers (offline)
Not in the default run: contamination_probe.py (--stages probe), detect_features.py --which original (lift vs originals), human grading (deferred), repeat-run noise.
Input from pipeline 2: data/sites.csv, data/sites_check.csv, data/<site>/original/, data/<site>/generated_cli/r1/free/render/. Every stage is resumable.
```

Files in this folder:
- `adequacy.py`
- `agree.py`
- `analyze_attributes.py`
- `analyze_variation.py`
- `attribute_galleries.py`
- `build_codebook.py`
- `check_observations.py`
- `code_pages.py`
- `collate_sites.py`
- `contamination_probe.py`
- `detect_features.py`
- `embed_merge.py`
- `feature_collages.py`
- `judge.py`
- `measurements.py`
- `observations_to_features.py`
- `run_annotation.py`
- `spotcheck.py`

See the top-level `PLAN.md` for decisions, status and open items, `ANALYSIS_PLAN.md` for the detailed plan and `DESIGN_DECISIONS.md` for the critiques.
