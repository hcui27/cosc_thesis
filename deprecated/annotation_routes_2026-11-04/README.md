# Archived 2026-11-04: the three feature-building routes and the two judge arms

Why: the annotation pipeline was redesigned (see PLAN.md, pipeline 3). Observations are now made on the ORIGINAL and the vibe-coded page separately (one Sonnet judge each), a third (Opus) judge combines them into general / changed / vibe-coded-only / original-only observations, each observation is tagged with attribute and value, one diff file per site is written, and a hierarchical master list is built; the seed list (v1.3) is matched against that master list at the very end.

What is here (nothing deleted, all resumable only by moving files back):
- `pipeline_3_annotate/`: the three routes that turned observations into features (features catalog: observations_to_features, detect_features, adequacy, analyze_variation; embedding master list: embed_merge, feature_collages; attribute-value codebook: build_codebook, code_pages(_evidence), analyze_attributes, attribute/evidence_galleries, element_map), the judge scripts (judge.py comparison judge, observe_single.py observation-only judge, check_observations.py tiering, collate_sites.py), the seed pilot (seed_pilot.py observation match, seed_pilot_vision.py), compare_seed_vs_codebook.py, compare_arms.py, run_compare_arm.py, ab_judges.py, the old run_annotation.py and README.
- `data/`: analysis (observation-only arm: tiers, features, codebook 314 attributes, evidence coding, galleries), analysis_seed (seed pilot, v1.1 results), analysis_ab (4-site judge A/B), logs.
- `arms/compare/`: the comparison-judge arm (284-attribute codebook) and its analysis.
- `observations_by_site/<site>/observations/`: the 56 observation-only judge files of the observation-only arm.
Reference results: the observation-only vs comparison arm report is `data/analysis/../analysis_arms/arms_report.md` inside `data/analysis_arms` (moved with `data/analysis`).
Not archived: the seed lists (`seed_attributes/`, v1.3 is current), measurements.py, agree.py, spotcheck.py, contamination_probe.py, pipelines 1 and 2, and data/<site>/{original, generated_cli, prompt}.

**Restored the same day (2026-11-04, your request):** `element_map.py`, `evidence_galleries.py` and `feature_collages.py` were copied back to `pipeline/3_annotate/` (copies remain here): the screenshot scripts that show what common features look like on the vibe-coded pages stay part of the new pipeline, to be pointed at the new master list.
