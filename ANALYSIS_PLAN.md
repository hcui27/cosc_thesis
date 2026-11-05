# Analysis plan: feature variation across the generated sites

*Drafted 2026-10-18; updated 2026-10-23 (Stages 1-4 and the attribute-and-value route have run on the 28 seed sites; results are summarised in "Status" below and in DESIGN_DECISIONS.md 3.8-3.10).* Applies to the 28 generations and their judge observations. The goal (see PLAN.md) is to learn what an agent naturally builds on less-popular sites, and which features are **inherent to vibe-coded sites** (they recur regardless of the source site) versus **site-specific** (they depend on the original, its category, or run-to-run noise). Nothing is judged for quality.

## These sites are the seed set
The 28 usable sites (the 30-site draw lost 2 to failed checks: Real Estate had none and Vehicles ended with 1) are the **seed set**: the features we look for later are *discovered from them*. The analysis therefore has two linked goals: (1) build a feature catalog from what these sites show, and (2) use the **variation in observations between just these sites** to decide how much more feature engineering is needed before the catalog is trusted or applied to a larger sample. Everything in Stage 3 and the new Stage 3b serves that decision.

## Current scope: build the shared features first
Right now the aim is only to **build a catalog of features that are shared across these sites** and to check it is adequate. Calling a feature an "inherent signature" is **not being done now**: no signature thresholds, and comparisons against the human originals are deferred. In scope: Stages 1-4 and Stage 3b, plus Stage 5 items 1 and 4 (prevalence and homogenization among the generated pages). Deferred (kept below for later, marked *Later*): lift against the originals, inheritance versus invention, paired comparisons, drivers of variation, run-to-run noise, and the contamination probe. **Phase 1 (Basecamp) features are not used as seeds**: the catalog is built only from these sites' observations.


## The central problem
Judge observations only say what a judge happened to **mention**. A feature absent from a list is not necessarily absent from the page. Variation needs a complete **site x feature matrix** with an explicit present/absent (or amount) value for every site, so observations are used to *discover* features, and separate detectors fill the matrix.

## Inputs per site
Original and generated `dom.json` facts (fonts, colors, radii, shadows, gradients, semantic tags, class stats, headings), screenshots, `text.txt`, `fidelity.json`, `format.json`, two judge files (Sonnet, Opus; about 40-55 observations each), plus metadata: Cloudflare category, rank, language, copy length, image count, cost.

## Stage 1: Freeze and inventory
- Collect one row per site (`data/analysis/sites_table.csv`): category, status of every stage, stack (so far all static HTML), fidelity, copy words, images, cost.
- Record failures and exclusions (e.g. unrenderable output) with reasons. Report n actually analysed; do not silently drop sites.

## Stage 2: Make the observations trustworthy (no human grading for now)
~28 sites x 2 judges x ~50 = ~2,800 observations: too many to grade fully.
1. **Agreement filter.** Use the agreement script per site: an observation made by both judges is high-confidence; single-judge items are flagged. (Earlier agreement on one site was 95-96%, same model family, so it is a necessary check but not proof.)
2. **Fact cross-check.** Any claim a fact can verify (title, h1 count, fonts, radii, shadows, tag counts) is checked programmatically; contradictions are dropped. In Phase 1 the errors clustered in exactly these claims.
3. *Later:* **Stratified human grading.** Not being done now. When it is added: grade a sample (suggest ~10 observations per site, stratified by observation type) to estimate precision per type. Until then "verified" in this plan means *passed the agreement filter and the fact cross-check*, and every result should be labelled as not human-verified. The only precision evidence so far is Phase 1: with full DOM facts in the judge prompt, graders marked 38/39 and 42/42 observations correct (Basecamp, v2), against about 80% earlier without them.
4. **Confidence tiers instead of grades.** Tier A = made by both judges and not contradicted by a fact; tier B = made by one judge and not contradicted; tier C = contradicted by a fact (dropped). Feature discovery uses tier A first; tier B observations can only add features that a detector later confirms on at least one other site.

## Stage 3: Build the feature catalog
- **Bottom-up (discovery):** convert each tier-A (or detector-confirmed tier-B) observation about the generated side into a site-independent feature statement ("CTAs are pill-shaped", not "AEP's button is blue"). Cluster per site, then merge across sites (embedding similarity plus an LLM merge pass; this is the first route, run as `embed_merge.py` and the LLM catalog; **Stage 3c replaces it for deciding what is shared**, because merging cannot tell opposite values apart). Human review of the merged list is still pending. Err toward inclusion; keep rare features with counts.
- **Discover on a discovery split, test on a hold-out: 24 discovery / 4 hold-out, repeated over 20 seeded random splits (decided).** Each split draws 4 hold-out sites (in different categories where possible) and builds the catalog from the other 24. With 20 splits of 4, each site is held out about 3 times on average; no site is exempt. After the adequacy check, the final catalog is rebuilt on all 28.
  - **Keep it cheap:** extract each observation into a canonical feature statement **once** (per-observation step, not per split). Each split then only repeats the clustering/merge on its 24 discovery sites, using embeddings (and an LLM merge only if needed), so 20 splits cost little.
  - **Define "covered" before running:** a hold-out observation is covered if it matches a catalog feature (embedding similarity above a fixed threshold, confirmed by an LLM match on a sample). Fix the threshold using the discovery sites only.
- Each feature gets: name, family (typography, color, layout, component, decoration, imagery, copy, semantic/DOM), a testable definition, and a detector type (dom, css, vision, text). Keep the existing confound flags (prompt artifact, original-brand-specific).


## Stage 3b: Is the seed catalog adequate? (variation in observations between these sites)
Use only the observation-level data from the seed sites to decide whether more feature engineering is needed. Metrics, each with a pre-stated reading:
1. **Discovery curve.** Add sites one at a time (many random orders, report the mean and band) and plot the number of *new* canonical features each new site contributes. A curve still rising steeply at site 28 means the catalog is incomplete; a plateau (e.g. < 1 new feature per added site over the last 8 sites) means the common features are captured.
2. **Singleton share.** Fraction of canonical features seen on exactly one site, and fraction of raw observations that map to no recurring feature. A high share (suggest > 40% of features, or > 30% of observations) means observations are site-specific or too concrete, so the abstraction is wrong, not necessarily that variation is real.
3. **Recurrence profile.** Histogram of "number of sites per feature" (1, 2-3, 4-9, 10-19, 20+). The shape shows how much of the page-to-page variation is shared structure versus one-offs. Report the mix by feature family.
4. **Between-site overlap of observations.** For each pair of sites, the Jaccard overlap of their feature sets (both judges combined), summarized as a distribution and by category. Low overlap with high judge agreement means real variation; low overlap with low judge agreement means judge noise.
5. **Judge consistency.** Per feature and per family: recall of Sonnet's observations by Opus and vice versa. Families where the two judges disagree are not yet reliable to engineer from.
6. **Hold-out coverage across 20 splits.** Fraction of each split's 4 hold-out sites' verified observations that the 24-site catalog already covers. Report the mean, the min-max range, the share of splits at or above 80%, and coverage per site (which sites are consistently poorly covered, i.e. unusual). Mean >= 80% with a narrow range means the catalog generalizes; a wide range means it depends on which sites are held out.
7. **Detector agreement.** For features that both a programmatic detector and a vision/LLM checklist can score, report agreement. Disagreement points to a definition that needs tightening.

**Decision rule and the conditional work plan.** Read the metrics together and take the matching actions:
| Finding | Meaning | Feature-engineering work to do next |
|---|---|---|
| Discovery curve still rising, hold-out coverage low | catalog incomplete | more seed sites (stratified toward thin categories), or a second discovery pass with a prompt that asks for structured per-site features, not free-form differences |
| Plateau, high hold-out coverage | common features captured | freeze the catalog, move to detection on all sites and the variation statistics (Stages 4-5) |
| High singleton share | features too concrete | merge pass: abstract by family (e.g. "icon style", "card treatment"), define parameterized features (a value, not yes/no) |
| Low judge consistency in a family | observations unreliable there | replace judged observations with programmatic detectors for that family, or add ground-truth facts to the judge prompt |
| Low detector agreement | definition ambiguous | rewrite the feature definition with a worked example per site and re-label a sample by hand |
| Many features measurable only by vision | detection cost and noise | build programmatic proxies (e.g. from computed styles) and validate them against the vision labels |
Also keep a short list of *unmeasured* features (observed but with no detector yet), since those are the most likely engineering gaps.

## Stage 3c: Attribute-and-value coding with cited evidence (added 2026-10-22/23; now the main route to shared features)
Why: the embedding merge (3.8) grouped observations by topic and mixed opposite values (square vs rounded corners), and counts of "sites sharing a feature" depended on a merge that cannot tell values apart. Instead, **features become attributes with closed value sets, and every page is coded for every attribute**, so "shared" means "most pages choose the same value".
1. **Topics:** `embed_merge.py` embeds each site's observation statements (fastembed BGE-small) and merges them into a master list (verified by an LLM pass); `build_codebook.py` clusters the 733 statements into topics with embeddings (cosine < 0.32, at most 40 per topic).
2. **Codebook:** an LLM defines attributes with closed value sets per topic, codes the statements, and consolidates per family: 278 attributes, 1,039 values, 1,530 observation codes. Conditional attributes get a `not_applicable` escape.
3. **Page coding with evidence:** `element_map.py` numbers each page's visible elements; `code_pages_evidence.py` codes every page for every attribute from the screenshot slices, page text, programmatic measurements and the element list, and **cites the element ids that show each value** (or marks it page-wide) in the same call. A value with no cited evidence is a low-confidence flag.
4. **Variation:** `analyze_attributes.py --codes-dir data/analysis/codebook_evidence`: modal share and normalised entropy per attribute, bands (shared >= 0.75, split >= 0.5, varied), shared presence vs shared absence/other, pairwise page agreement (SD against a permutation null; the mean is fixed by the marginals and only descriptive), coder-vs-judge agreement, and, once originals are coded, the modal value against the originals.
5. **Galleries:** `evidence_galleries.py` builds one gallery per attribute value from the cited evidence (every page coded with it, every cited element, real box plus context, red outline); no LLM calls, so re-grouping values later is free. This replaced a separate vision locator (`attribute_galleries.py`, superseded) that located 91% of pairs with unverified boxes.
Stage 3b's discovery/hold-out adequacy test still applies to the LLM feature catalog; it has not been repeated on the codebook (the codebook is built from the same 28 sites it describes, with no hold-out; see DESIGN_DECISIONS.md 3.9).

## Stage 4: Detect every feature on every generated page (originals later)
- **Programmatic detectors** from `dom.json` and computed styles for everything measurable: radius buckets, pill buttons, shadow and gradient counts, backdrop blur, font families and sizes, emoji and em-dash counts, Tailwind-like class share, semantic tag use, heading outline, grid/flex use, page height, color palette (hue, saturation, count of distinct accents).
- **Vision/LLM checklist** for the rest (card grids, hero pattern, eyebrow labels, icon style, section rhythm, testimonial treatment), run per page with the screenshot and a fixed yes/no/degree schema, using a different model from the generator where possible. *Later:* apply the same checklist to the original pages to get a human baseline per site.
- Output: `site_feature_matrix.csv` (sites x features, generated pages; original-page columns added later) with a detector-agreement column wherever two detectors cover the same feature. The Stage 3c matrix (`data/analysis/codebook_evidence/page_codes_generated.csv`, 28 x 278, with cited evidence in `evidence.csv`) is the second site x feature matrix; the two are not yet reconciled.

## Stage 5: Measure variation (items 1 and 4 now; the rest *Later*)
1. **Prevalence** of each feature across generated sites (for Stage 3c attributes: modal share and bands, done in `analyze_attributes.py`), with Wilson 95% intervals (n=28 gives roughly +/-18 points, so only large effects are readable). Bands: universal (>=90%), common, occasional, rare.
2. *Later:* **Lift versus the human originals:** prevalence in generated minus prevalence in originals, per feature. **Inherent-signature candidates** = high in generated, low in originals. Features high in both are the era/web baseline, not signatures.
3. *Later:* **Paired comparisons** (site by site) for continuous features, e.g. radius share, shadows, gradients, palette saturation (Wilcoxon signed-rank; report effect sizes, not only p-values).
4. **Homogenization:** mean pairwise distance (Jaccard on binary features, Gower on mixed) among generated pages versus among the originals. Do the generated pages converge on a common look while the originals were diverse? Visualize with a clustered heatmap and a 2-D embedding.
5. *Later:* **Inheritance versus invention:** per site, how much of the generated look is explained by the original (similarity of palette, layout metrics, type scale between original and generated)? Features the agent invents against the original are stronger signature evidence than those it copies.
6. *Later:* **Drivers of variation:** does feature prevalence differ by category, language, copy length, image count, or fidelity? With ~2 sites per category, treat category effects as descriptive and exploratory (exact tests, no strong claims).
7. *Later:* **Run-to-run noise:** one run per site cannot separate signal from noise. Repeat a subset (e.g. 5 sites x 3 runs) and compute within-site versus between-site variance (ICC) per feature; features with high within-site variance are down-weighted.

## Stage 6: Validity checks
- Re-run detectors with a second model on a subset and report agreement.
- (Removed 2026-10-26: the fidelity check. Which copy the agent keeps is data, not a confound to control.)
- Contamination probe on a sample of sites (give the model only the copy and ask which site it is); report the hit rate.
- Confounds to report explicitly: generator and judges are the same model family; only one generator; Wayback survivorship; fonts were not provided, so font choice is a possible signature but also a missing-asset effect.

## Deliverables
Feature catalog (CSV/JSON with definitions, detectors, prevalence, CI, category breakdown; lift against the originals added later), the site x feature matrices, figures (prevalence bars, lift plot, clustered heatmap, original-versus-generated paired plots), a data dictionary, and a short write-up with the limitations above.

## Scripts (pipeline 3: all in `pipeline/3_annotate/`, shared helpers in `pipeline/shared/`; built 2026-10-18)
Run them in this order, or all at once with `python pipeline/3_annotate/run_annotation.py` (`--dry-run`, `--stages`; stages: judge, collate, tier, features, merge, collage, codebook, elements, code, attributes, galleries, detect, adequacy, analyze). The runner also performs the judging step, which comes before Stage 1 (judge.py, about $0.65 per site).
| Stage | Script | Notes |
|---|---|---|
| 1 | `collate_sites.py` | sites table, flat observation table, exclusions |
| 2 | `check_observations.py` | one LLM call per site: judge agreement plus fact check -> tiers A/B/C (about $0.11 per site) |
| 3 | `observations_to_features.py` | per-site feature statements, then canonical grouping per family into `features_catalog.json` (statements carry an optional programmatic proxy from `measurements.py`) |
| 3b | `adequacy.py` | offline: discovery curve, singleton share, recurrence, overlap, judge consistency, 20 repeated 24/4 splits, readout against the decision table |
| 3 (merge) | `embed_merge.py`, `feature_collages.py` | embedding merge of site observation sheets into a master list, LLM verification, collages for shared visual entries (first route, superseded by 3c for counting shared features) |
| 3c | `build_codebook.py` | embeddings find topics; LLM defines attributes with closed value sets and codes the observations (about $5.7) |
| 3c | `element_map.py` | number each page's visible elements (free) |
| 3c | `code_pages_evidence.py` | code every page for every attribute and cite element ids (about $20; `code_pages.py` is the earlier evidence-free coder, kept for comparison and for coding originals) |
| 3c | `analyze_attributes.py` | offline: bands, entropy, presence vs absence, pairwise agreement vs null, coder reliability |
| 3c | `evidence_galleries.py` | galleries from cited evidence (free); `attribute_galleries.py` is the superseded locator version |
| 4 | `detect_features.py` | programmatic measurements plus vision checklist per page; a proxy that agrees with the checklist on < 70% of pages falls back to the checklist (about $0.20 per page) |
| 5 | `analyze_variation.py` | offline: prevalence with Wilson intervals, homogenization, plus the Later items that need no new data (paired comparisons, inheritance, drivers); lift appears once an original-page matrix exists |
| 6 | `contamination_probe.py` | built, not run (Later) |
Shared: `measurements.py` (50 programmatic page measurements), `llm.py`, `ledger.py`. Outputs land in `data/analysis/`.

## Status (2026-10-23)
- Stages 1-4 and 3b ran: tiers A 2,263 / B 303 / C 26 of 2,592 observations; LLM catalog 188 features (36% singletons); hold-out coverage 0.897 (0.817-0.984) but the discovery curve has not plateaued (about 2.8 new features per added site over the last 8).
- Stage 3c ran: 28 pages x 278 attributes, evidence cited on 96% of non-absence codes, 9,472 gallery crops in 610 galleries. Bands 118 shared / 116 split / 44 varied (58 shared presence, 60 shared absence/other); page-pair structure beyond independent coding (SD 0.047 vs null 0.027).
- Coding noise (two runs, same model, different prompts): 83% of cells agree, 80% of attributes keep their band, shared-set Jaccard 0.74; so quote the intersection of the runs, not one run. Coder-vs-judge agreement 72% (copy 56%, imagery 55%).
- Stage 5 items 1 and 4: generated pages are more alike than the originals in measured style; accent hue is closer to the original than chance; copy length drives the feature count.
- Not done: any human validation (crops, codes, tiers), a second coder from another model family, coding the originals (lift), run-to-run noise on regenerated pages, contamination probe, hold-out test of the codebook.
- Spend: all pipelines $109.84, pipeline 3 about $99.1.

## Decisions
- DECIDED (2026-10-22): shared features are found by attribute-and-value coding of every page, not by counting merged observations; embeddings are used only to find topics.
- DECIDED (2026-10-23): evidence is cited at coding time (element ids), replacing the separate locator; galleries are built from it.
- DECIDED: 24 discovery / 4 hold-out, repeated over 20 seeded random splits.
- DECIDED: adequacy thresholds as suggested in Stage 3b (plateau: < 1 new feature per added site over the last 8 sites; singleton share: > 40% of features or > 30% of observations means too concrete; hold-out coverage >= 80%).
- DECIDED: Phase 1 / Basecamp features are not used as seeds.
- DEFERRED: any threshold for calling a feature an "inherent signature".
- DEFERRED: human grading (none for now; confidence tiers and fact checks stand in).
- DEFAULT (no input from you, so left to my judgment): a feature is detected **programmatically** whenever it can be computed from the page facts or computed styles (radii, pill buttons, shadows, gradients, fonts and sizes, palette, emoji and em-dash counts, semantic tags, heading outline, class-name patterns, page and section metrics); everything that needs looking at the page (card grids, hero pattern, icon style, section rhythm, decorative treatment) goes to the **vision/LLM checklist**. The split is revisited using detector-agreement results: a vision feature with a reliable programmatic proxy moves to programmatic, and a programmatic feature that disagrees with the vision label gets its definition tightened.
- LATER: size of a repeat-run subset (5 sites x 3 runs is about $10-12 with judges).
