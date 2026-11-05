# Old-protocol run files (archived 2026-10-26)

**Why archived.** On 2026-10-26 the generation protocol changed, so everything produced under the old one is not comparable with new runs:
1. The generator prompt said "Build a website **landing page** from this content..."; it now says "Build a website from this content..." (`pipeline/2_build_sites/generate.py`).
2. Image file names kept placement words (`footer-graph.png`, `hero.jpg`); `sanitize.py` now strips them.
3. The copy-fidelity check was removed: which copy the agent keeps is data, not something to verify.
4. Judge design is under test (see `data/analysis_ab/ab_report.md`); the old judges compared the original with the generated page.

**What is here (moved, not edited).** Mirrors the original layout under `data/`:
- `data/<site>/prompt/`, `generated_cli/` (28 generated sites, renders, `fidelity.json`, `PROMPT.txt`), `diffs/` (comparative judge observations, 2 judges per site) for the 28 seed sites.
- `data/analysis/` (everything pipeline 3 derived: observations, tiers, catalog, merge, codebook, `codebook_evidence/`, galleries, variation, adequacy; 229 MB).

**What stayed in `data/`.** Inputs that do not depend on the protocol: `data/<site>/original/`, `copy.auto.md`, `images/`, `images_manifest.json`, `data/sites.csv`, `data/sites_check.csv`, `data/frames/`, `data/basecamp/`, `data/ledger.jsonl` (full cost history, including the old runs), and `data/analysis_ab/` (the judge A/B on 4 sites, which includes copies of the old comparative observations for those sites).

**Headline numbers of the old run (for reference).** 28 sites, all static HTML; 2,592 judge observations; codebook 278 attributes / 1,039 values; evidence-coded matrix 28 x 278 with 96% evidence coverage; bands 118 shared / 116 split / 44 varied; test-retest 83% of cells; total spend about $109.84 (pipeline 3 about $99).

**To restore.** `mv deprecated/old_protocol_2026-10-26/data/analysis data/analysis` and move each `data/<site>/{prompt,generated_cli,diffs}` back. Note that pipeline scripts will then read old-protocol data again.
