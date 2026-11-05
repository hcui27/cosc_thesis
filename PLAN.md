# Plan and status: the stylistic signature of vibe-coded websites

*Last updated 2026-11-04 (annotation pipeline redesigned and designer-brief layer added; see "Redesign of 2026-11-04" below).* All three pipelines have run end to end once on the seed set (28 sites). Code lives in `pipeline/1_find_sites`, `pipeline/2_build_sites`, `pipeline/3_annotate` (+ `pipeline/shared`); each folder has a README and a runner. The detailed plan for pipeline 3 is [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md). The design decisions made in each pipeline, with the critiques and open questions they invite, are in [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md).

## Goal
**The goal is NOT good websites.** We want to know what a coding agent *naturally* produces on its own, with no style guidance and no format instruction, for **less-popular sites** (unlikely to be memorised), in order to identify features that may be inherent to vibe-coded websites. Take pre-2022 homepages from the Wayback Machine, give the agent only their copy and images, let it build whatever it chooses, then catalogue the traits of what it built (compared with the human original). Nothing is judged for quality, and generated pages are never "improved" or corrected; the judges describe differences neutrally.

## The three pipelines
```
 PIPELINE 1  find the websites          PIPELINE 2  build the sites                    PIPELINE 3  annotate
 Tranco 2021 list -> homepage text ->   Wayback skeleton (copy+images) -> sanitize -> designer brief -> observe original | observe vibe-coded -> combine -> tag attrs/values
 -> LLM category label -> draw          -> Claude Code builds it (agent's choice) -> render                  -> n diffs -> master list -> match to seed list
        |                                     |                                                                  |
        +-- handoff: sites_draw_cf.csv        +-- handoff: sites.csv, original/, render/        +-- data/analysis/
            replacements_cf.csv
```
| | Pipeline 1: find sites | Pipeline 2: build sites | Pipeline 3: annotate |
|---|---|---|---|
| Question | Which sites, spread across what kinds of site? | What does the agent build from a designer-style brief of a site's content plus its images? | What is common on what it built, and how does it differ from the originals? |
| Code | `pipeline/1_find_sites/` | `pipeline/2_build_sites/` | `pipeline/3_annotate/` |
| Runner | `run_find_sites.py` | `run_build_sites.py` (per-site worker `run_site.py`) | `run_annotation.py` |
| Reads | Tranco list | the draw from pipeline 1 | `data/sites.csv`, `data/<site>/original/`, `data/<site>/generated_cli/r1/free/render/` |
| Writes | `data/frames/` | `data/sites.csv`, `data/sites_check.csv`, `data/<site>/` (incl. `prompt/brief.md`) | `data/<site>/diff/`, `data/master/` |
| Spend so far | about $2.65 (labelling) | about $5.57 (28 generations) | about $99.1 (judges $20.49, tiering/features/checklist $11.61, merge verification and collage locator $4.75, codebook $5.67, first page coding $22.39, locator galleries $13.40, evidence-at-coding $20.45); all pipelines $109.84 |

Shared code: `pipeline/shared/` (`llm.py`, `ledger.py`, `net.py`). Every scripted LLM call is logged to `data/ledger.jsonl`. One cross-pipeline dependency: pipeline 1 uses pipeline 2's skeletonizer in text-only mode to extract page copy for language checks and labels.

## Decisions in force (all pipelines)
| Item | Decision |
|---|---|
| Scope | **Desktop only** (1440px). Mobile is out of scope everywhere. No post-2023 control group |
| Human grading | **None for now** (deferred); confidence tiers and fact checks stand in. Phase 1 features / Basecamp are not seeds |
| Signatures | No threshold for calling a feature an "inherent signature" for now: the aim is to build shared features first. Generator-chosen fonts count as a possible signature; misplaced overlay images are recorded as a feature |
| Study size | 30 sites drawn; 28 usable after checks. First runs only, fewer than 40 |

---

## Pipeline 1: finding the websites
**Scripts** (`pipeline/1_find_sites/`): `build_frame.py` (sample + Wayback fetch), `english.py` + `review_english.py` (language), `page_features.py` + `label_categories.py` (LLM category labels), `draw_cf.py` (the draw), runner `run_find_sites.py`.

**Decisions**
- **Frame:** Tranco list of 2021-06-01 (id QXW4), ranks **> 100,000** for the 30 sites drawn so far. **The rank > 100,000 rule is no longer a requirement (2026-11-04):** contamination is now handled by the designer-brief layer in pipeline 2 (the generator never sees the page's wording), so the rank floor is not needed to limit exposure. The site list stays exactly as drawn; the rule only matters if the frame is ever redrawn. Seeded random sample of 300 domains; homepage fetched from the Wayback snapshot nearest 2021-06-01 (must be <= 2021, HTTP 200, still at the root). 268 domains had a usable page (saved in `data/frames/html/`).
- **Categories:** Cloudflare's 26 top-level content categories, **applied by an LLM** to each 2021 page (not Cloudflare's own labels). Excluded: Adult Themes, Child Abuse, Gambling, Questionable Content, Security Risks, Violence (20 categories remain).
- **Language:** study sites must be English: the labeller says `en` AND the extracted copy is >= 0.90 English by Lingua (pages with < 5 usable sentences use the labeller's call). The threshold was reviewed against 52 human verdicts: no cutoff gets fewer than 9 of 52 wrong, so 0.90 was kept.
- **Draw:** English only, label confidence >= 0.6, passes the non-language viability checks. 2 per fulfilled category (24) + the single qualifying site of each of 3 partial categories + 3 extras from the largest categories = **30**, with 51 replacement candidates.

**Status:** done. Output: `data/frames/sites_draw_cf.csv`, `replacements_cf.csv`, `qualifying_sites.md`.
- Empty categories (0 qualifying): Ads, Information Technology, Miscellaneous, Religion, Weather. Noted, not filled.
- Final coverage after pipeline 2: Real Estate ended with 0 sites; Vehicles, Job Search & Careers and Social & Family with 1 each.

**Limits:** a balanced sample for comparing categories, not representative of the web; the category labels are unreviewed LLM labels (a few look doubtful, e.g. `widro.com`, `thync.com`, `cbdoilcreamnk.com`); Wayback survivorship; Tranco ranks do not reach the unranked tail.

**Open:** spot-check the labels of the drawn sites; fill the empty categories (e.g. keyword search of Tranco domain names); consider Common Crawl for the unranked tail.

---

## Pipeline 2: scraping / skeletonizing, then vibe-coding
**Scripts** (`pipeline/2_build_sites/`): `check_selected.py` (per drawn site: fetch, skeletonize, test usable, replace failures), `skeletonize.py`, `sanitize.py`, `generate.py`, `formats.py` + `render.py` (render whatever was built; the copy-fidelity check was removed 2026-10-26), per-site worker `run_site.py`, runner `run_build_sites.py`.

**Decisions**
- **Skeleton:** raw Wayback HTML (`id_`), images via `im_`. Included: `<img>` (real source from `data-src`/`src`/`srcset`), desktop `<picture>` sources, titled inline SVGs, raster CSS backgrounds from stylesheets, `<style>` blocks and inline styles. Excluded: scripts, comments, hidden or `display:none` elements (media queries evaluated at 1440px), boilerplate by class name, mobile-only sources. Every drop is logged in `images_manifest.json`.
- **Usable inputs:** 150-3000 words of copy and 2-40 referenced images that downloaded; a failing site is replaced from the same category.
- **Sanitize** (writes `data/<site>/prompt/`, the only thing the generator sees): removes placement labels, **all image alt text**, divider rules, "(mobile version ...)" notes and images the copy does not reference. Keeps image file names, link addresses, emphasis and heading levels, the images, section order. Raw `copy.md` and `images/` are kept in the site folder.
- **Generator:** Claude Code (`claude -p`, Sonnet 5.5), prompt exactly: "Build a website landing page from this content. copy.md has the text and images/ has the images." No style guidance, **no output-format instruction**; the agent chooses its stack. One `free` run per site; the stack is recorded (`meta.json`, `format.json`) and treated as data.

**Status:** done on all drawn sites. 37 sites checked, **28 usable**, 9 excluded (too many images, too little copy, fewer than 2 images, or no replacement left). 28 generations (about $5.57, about 1 minute each), all rendered.
- **Result:** every agent built a single static HTML page (27 plain, 1 loading Alpine.js from a CDN); none chose React, Vue, Tailwind or a build tool.
- **Copy fidelity** (old runs, check now removed): mean 76%, range 33-100%. Which copy the agent keeps is now treated as data, not checked.
- **Prompt change (2026-10-26, not yet run):** the generator prompt no longer says "landing page" (`Build a website from this content. copy.md has the text and images/ has the images.`), and `sanitize.py` strips placement words from image file names (`footer-graph.png` becomes `graph.png`). The 28 existing sites were generated and sanitized under the old protocol, so regenerating is needed before the data are consistent.

**Known gaps:** a stylesheet Wayback cannot serve (e.g. a 500) disables CSS-based hiding and background capture for that site; tables flatten; the boilerplate filter is a substring match; specificity is ignored when resolving `display`; the auto-built copy of the 28 sites was not hand-reviewed.

**Open:** repeat runs on a subset (e.g. 5 sites x 3) to measure run-to-run noise; a second generator; Phase 1 (Basecamp, two prescribed stacks) is history and stays under `data/basecamp/` ([FEASIBILITY.md](data/basecamp/FEASIBILITY.md)).

---

## Pipeline 3: annotation

**Redesign of 2026-11-04 (replaces the judge/feature-building description below where they conflict).**
- *Designer-brief layer (pipeline 2).* `brief.py` sits between sanitize and generate: an LLM restates the sanitized copy as the content brief a designer would hand over (same facts, names, numbers, URLs; new wording; English; content only, no layout, style, placement, purpose or audience). Image references are kept once each. The generator receives `brief.md` + `images/`, never the verbatim copy (kept in `data/<site>/copy_verbatim.md`). This reverses the earlier "verbatim copy kept in the prompt" decision and removes contamination as a reason for the Tranco rank floor.
- *New pipeline 3, per site.* (1) one Sonnet judge describes the ORIGINAL page alone; (2) separately, one Sonnet judge describes the VIBE-CODED page alone and cites numbered elements; (3) one Opus judge combines the two lists into observations with status general / changed / generated_only / original_only (the original is included because what is general cannot be told from the vibe-coded page alone); (4) a tagger gives every observation attribute(s) and value(s) (`original_value`, `generated_value`) with a vocabulary shared across sites; the tagged list is the site's diff (n diffs for n sites, `data/<site>/diff/diff.json`).
- *Master list.* `build_master.py` merges attributes and values across sites and summarises hierarchically (family -> attribute -> value), with counts of sites for general, changed and vibe-coded-only, one-line summaries, and element ids per site.
- *Screenshot scripts kept.* `element_map.py` (numbered elements), `evidence_galleries.py` (sheets of what each common feature looks like on the vibe-coded pages, now built from the master list) and `feature_collages.py` (now reads the master list: one collage per attribute, one tile per vibe-coded site, located by one vision call per site; part of the 28-site run as stage `collages`).
- *Seed list at the very end.* `match_seed.py` matches the master list to the closed seed list (v1.3: Component Gallery, Open UI, Tailwind Plus, public CSS frameworks, NN/g glossary; `seed_attributes/`) as a corpus: which seed items the observations corroborate, and what the observations add that the seed list lacks. Culling remains later (see "Seed list: culling, later").
- *Archived.* The three feature-building routes (features catalog, embedding master list, attribute-value codebook), the observation-only and comparison arms and their analyses are in `deprecated/annotation_routes_2026-11-04/` (README there). Their results (e.g. observation-only vs comparison arm report) remain readable.
- *Status.* Code written; pilot on 4 sites (kanienkeha_net, neverskipbrunch_com, insightcentral_net, bathurst12hour_com_au) regenerated from briefs and annotated; the other 24 sites still hold generations from the verbatim-copy protocol and must be regenerated before a full run.
Detailed plan: [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md). **Scripts** (`pipeline/3_annotate/`): `judge.py`, `check_observations.py`, `collate_sites.py`, `observations_to_features.py`, `adequacy.py`, `detect_features.py`, `measurements.py`, `analyze_variation.py`, `agree.py`, `spotcheck.py`, `contamination_probe.py`, `embed_merge.py` + `feature_collages.py` (embedding merge into a master list, then collages), `build_codebook.py` + `element_map.py` + `code_pages_evidence.py` + `analyze_attributes.py` + `evidence_galleries.py` (attribute-and-value coding with cited evidence, the main route to shared features, and the galleries built from that evidence); `code_pages.py` and `attribute_galleries.py` (the first coder and the separate vision locator) are superseded but kept for comparison, runner `run_annotation.py`.

**Decisions**
- **Judges:** Claude Sonnet 5.5 and Opus 5.5, each given both screenshots plus programmatic page facts as ground truth, told this is not a quality review.
- **Tiers instead of human grades:** A = both judges made the point and no fact contradicts it; B = one judge; C = contradicted by a fact (dropped).
- **Feature catalog** built from the seed sites only, with **24 discovery / 4 hold-out sites repeated over 20 seeded splits**; adequacy thresholds: plateau < 1 new feature per added site over the last 8 sites; singletons > 40% of features or > 30% of observations means too concrete; hold-out coverage >= 80%.
- **Detection:** programmatic whenever a page measurement can compute the feature (a proxy that agrees with the vision checklist on < 70% of pages falls back to the checklist); vision checklist for the rest.

**Status:** done on the 28 sites.
- 56 judge files, 2,592 observations (37-57 each; the two judges agree on about 96% of observations). Tiers: A 2,263, B 303, C 26 (1.8% of the fact-checkable claims were contradicted).
- **188 canonical features** (38 with a programmatic proxy, 124 vision, 26 text); 36% appear on one site only, 18 on 10+ sites.
- **Adequacy:** hold-out coverage mean 0.90 (0.82-0.98); the discovery curve has not plateaued (about 2.8 new features per added site over the last 8); singleton share within limits. Readout: catalog provisional.
- **Detection:** 28 x 188 matrix, 90% of cells filled; 9 of 38 proxies fell back to vision.
- **Variation:** 18 features on >= 90% of pages (several only reflect the single-static-HTML choice). The generated pages are more alike than the originals in measured style (spread 3.46 vs 4.71, difference -1.25, 95% CI -2.06 to -0.24). Against the originals: rounded corners 0.6% -> 11% of elements, first heading 36 -> 62px, scripts 40 -> 1, stylesheets 8.5 -> 0, CSS grid 0 -> 7 uses. Accent hue stays close to the original's (34 vs 93 degrees expected by chance). More copy means more features present (rho 0.63); category shows no clear effect.

**Embedding merge + collages (added 2026-10-21, run 2026-10-22):** each site's observation sheet is embedded (fastembed, BGE-small) and the most similar sheets are merged pairwise until one master list remains, with the number of sites sharing each entry. Embeddings group by topic and mixed opposite values (square vs rounded corners), so an LLM verification pass splits such entries: 53 of the 74 multi-site entries were split, giving a **master list of 430 entries, 54 shared by >= 3 sites** (top entry 20 sites; 76% of entries are singletons). Most shared: lean markup (20), clean heading hierarchy (15), descriptive alt text (13), compact header (13), constrained centered container (11), grids of equal cards (11). Near-duplicates remain after verification (e.g. two "semantic landmarks" entries, two "system font" entries), so a second consolidation pass would help. For each of the 44 shared observations in visual families, a vision call located it on every relevant page: 44 collages, 200 of 218 possible crops (`data/analysis/collages/`, index in `index.md`); two collages spot-checked and correct, the rest not yet reviewed. Cost: verification $2.44, locator $2.31. Design notes: DESIGN_DECISIONS.md 3.8.

**Attribute-and-value coding (decided and run 2026-10-22):** embeddings find topics only; an LLM defines attributes with closed value sets and codes the observations (278 attributes, 1,039 values); a vision coder then codes every page for every attribute (7,724 cells). Results: 121 shared / 116 split / 41 varied attributes by modal-value share, of which 61 shared presence and 60 shared absence or "other"; pages show cluster structure (pairwise-agreement SD 0.050 vs null 0.027); coder-vs-judge agreement 68%. Bugs found and fixed on the way (value filter, no "absent" option for conditional attributes, an empty permutation test) are documented in DESIGN_DECISIONS.md 3.9. **Exhaustive galleries** replace the earlier one-crop-per-site collages, which missed about two thirds of the pages with a feature. The first version (`attribute_galleries.py`, a separate vision locator, `data/analysis/galleries/`) located 91% of coded (page, value) pairs and its crops were unverified.

**Evidence-at-coding (added and run 2026-10-23):** the coder now cites its evidence in the same call. `element_map.py` re-renders each page and numbers its visible elements (id, tag, text, pixel box); `code_pages_evidence.py` codes all 278 attributes and returns, per attribute, the value plus the element ids that show it (or page-wide); `evidence_galleries.py` crops each cited element's real box with context and a red outline, with no LLM calls, so re-grouping attributes later only needs a re-run. Results (`data/analysis/codebook_evidence/`, `data/analysis/galleries_evidence/`): 4,638 of 4,852 non-absence (page, value) pairs cite evidence (96%), 9,472 instance crops in 610 galleries, 13 empty galleries (was 17), eyebrow labels on 18 of 18 coded pages with 55 instances (the locator found 10 of 20 pages). Re-run attribute analysis on the new codes: 118 shared / 116 split / 44 varied (58 shared presence, 60 shared absence or other), pairwise-agreement SD 0.047 vs null 0.027, coder-vs-judge agreement 72%. The two coding runs are effectively a test-retest: 83% of cells agree, 241 of 278 attributes keep the same modal value, 222 the same band, and the shared sets overlap with Jaccard 0.74. Cost $20.45 (142 calls). Design notes: DESIGN_DECISIONS.md 3.10.

**Protocol change and seed-list pilot (decided 2026-10-26; run in progress).**
- *New generation protocol:* prompt without "landing page"; image file names stripped of placement words; no copy-fidelity check (which copy the agent keeps is data). Old runs archived in `deprecated/old_protocol_2026-10-26/`.
- *Observation-only judges:* judges now describe the generated page alone (`observe_single.py`), no comparison with the original. A/B on 4 sites (`data/analysis_ab/ab_report.md`, $1.76): comparative judges spend about a fifth of their output on the original and phrase 87% of the rest relatively; observation-only judges agree less with each other (0.48 vs 0.60) but describe the page itself. Originals are not coded for now (no lift).
- *Closed seed list v1* (`seed_attributes/seed_v1.csv`, 82 items: 60 Component Gallery components, 6 extra Open UI names, 16 Tailwind Plus page sections) is kept separate from the codebook-derived list (`seed_attributes/codebook_derived_v0/`, 278 attributes); merging them is version 2.
- *Seed pilot (`seed_pilot.py`):* every generated page is coded for presence of each seed item (with cited elements and a short note). **No culling yet.**
- *Seed list: culling, later.* Once we know from the pilot which seed items are actually present and relevant on these sites, the list will be culled (candidate rule: keep items present on >= 3 of 28 pages, plus any item the codebook also found), and the culled list becomes the coded vocabulary for version 2. Nothing is trimmed in this run; `seed_summary.csv` records prevalence for every item so the cut can be chosen afterwards.
- *Comparison at the end of this run (`compare_seed_vs_codebook.py`, no culling):* (1) how many seed items were pertinent (present on >= 1, >= 3, >= half of the pages); (2) how many codebook attributes were ADDED, i.e. not about any seed item (one LLM pass labels each attribute `is_item`, `property_of_item` or `none`); (3) the two distributions side by side (seed-item prevalence vs presence rate of codebook attributes, split by relation) in `data/analysis_seed/seed_vs_codebook.{md,csv,png}`.
- *This run's chain:* regenerate the 28 sites and observation-only judges (`data/refresh_new_protocol.log`), then collate, tier, features, codebook, elements, evidence coding, attribute analysis, seed coding, comparison (`data/refresh_chain2.log`). Estimated spend: generation about $5, judges about $12, tiering and features about $6, codebook about $6, evidence coding about $20, seed coding about $8, comparison about $1 (total about $58). The pipeline has 28 usable sites, not 30.

**Deferred:** human grading, lift against the originals (needs the checklist run on the original pages, about $6), run-to-run noise (needs repeats), contamination probe (built, not run), signature thresholds.

**Next engineering:** merge duplicate features across families (e.g. "rounded corners on cards" appears under decoration and component); recalibrate the 9 weak proxies; a structured second discovery pass or more seed sites, since the catalog has not plateaued.

---

## Repository map
```
pipeline/1_find_sites  2_build_sites  3_annotate  shared     the three pipelines + shared helpers (each has README.md and a runner)
(the `deprecated/` and `pipeline/deprecated/` folders were removed on 2026-10-23: moved to ~/.Trash/cosc_thesis_deprecated, recoverable until the Trash is emptied)
`deprecated/old_protocol_2026-10-26/`  the 28 old-protocol generations, judge diffs and `data/analysis/` (moved 2026-10-26 when the prompt, image-name and fidelity rules changed; see its README). Pipeline 2 and 3 outputs must be regenerated before the next analysis.
data/frames/        pipeline 1      data/<site>/, data/sites*.csv   pipeline 2      data/<site>/diffs/, data/analysis/   pipeline 3
data/ledger.jsonl   every scripted LLM call (cost, model, prompt hash)             data/basecamp/   Phase 1
```
Run from the project root, in order: `python pipeline/1_find_sites/run_find_sites.py`, `python pipeline/2_build_sites/run_build_sites.py`, `python pipeline/3_annotate/run_annotation.py` (each accepts `--dry-run` and `--stages`).

## Risks
- Wayback rate-limiting and outages, and a laptop that sleeps (the runners wait for the network and resume); survivorship from needing a usable 2021 snapshot.
- LLM category labels, the English filter and the feature catalog are LLM-made and not human-verified.
- Judges, detectors and the generator are the same model family; mitigated by the second judge and fact checks, not by a different model family.
- Unpopular does not guarantee unseen by LLMs; contamination is reduced, not removed (probe not yet run).
- Copyright: keep scraped content private; publish only derived observations.
