# Phase 1 Feasibility Verdict: Basecamp landing page (Wayback, 2 June 2021)

**Verdict: feasible, with caveats to fix before Phase 2.** The pipeline ran end to end on one site. Both generators reproduced the content, and the LLM diffs were specific and mostly verifiable. From four regeneration runs the process produced 67 candidate features, 15 of which appeared in all four runs. The weak points are scripting (generation and judging are not yet scripted), judge independence, and the single-sample design.

## What was run
- **Source:** `https://basecamp.com/`, snapshot `20210602032656`. Prompt = `copy.md` (page text) + `images/` (7 files including the footer chart), no style guidance.
- **Generators:** Claude (as subagents in this session; the headless CLI was not logged in), neutral prompt, two variants: single `index.html`, React + Vite + Tailwind.
- **Runs:** v1 (footer chart accidentally omitted from the prompt) and v2 (chart included): 4 generations total.
- **Judging:** a separate Claude agent per pair, desktop only, comparing the original with each regeneration. Observations were then graded by you.

## Answers to the plan's questions
1. **Does each stage run reliably and scriptably?** Partly.
   - Scripted: Wayback fetch, image extraction and copy.md draft (`skeletonize.py`), rendering (`render.py`), gathering renders (`collect.py`).
   - Not scripted: generation and judging (done through subagents), and manual cleanup of the auto-generated `copy.md`.
2. **Did the Wayback fetch and skeleton lose anything important?** One thing, found by the review: the footer growth chart is a CSS background image, and my first hand-built prompt dropped all CSS images. It was fixed in v2 and in `skeletonize.py` (raster CSS backgrounds on real elements are now included, with every drop logged). The auto-generated `copy.md` still contains page boilerplate (hidden sign-in popup, duplicate mobile nav) that needed manual removal. Fonts and layout are deliberately excluded, so the generators had to choose their own.
3. **How faithful were the generations?** Copy and images were present in all four runs on visual inspection, but I did not measure this programmatically. The handwritten caption overlay is misaligned over the screenshot in all four runs (the prompt doesn't say it's an overlay). Neither generator opened its page in a browser.
4. **Are the diff observations concrete, and what was the judge's hit rate?**
   - v1 (partial DOM reading): of non-mobile graded items, 35/38 correct for single-file and 31/36 for framework (3 bad/unsure and 2 unlabeled) (errors were mostly DOM and metadata claims such as h1 counts and page title).
   - v2 (full DOM reading): single-file 37 correct, 1 incorrect (page title), 1 blank assumed correct; framework 37 correct, 5 blank assumed correct.
   - Observations cite evidence, so they can be checked. Page-title and tag-count claims should be computed by script, not judged.
5. **Is landing-page scope right?** Yes for this site: one page, bounded copy, rich visual signal. Risks at scale: JS-rendered pages (Notion's snapshot had no usable copy), redirects and locale changes (Coinbase went to `/fr/`), blocked snapshots (Dropbox 426), and image-heavy pages (Mailchimp 67 images).
6. **Single-file vs. framework?** Both gave usable signal. Differences were systematic: both single-file runs used serif headings and both framework runs used Inter. Framework builds also exposed more semantic and structural features.

## Early results (candidate features, not findings)
- **67 candidate features** from 125 verified observations; 42 appear in both generators; 15 in all four runs.
- **Most stable features** (all four runs, no confound flag): pill-shaped CTA buttons, warm cream page background, testimonials as white rounded cards in a masonry grid, soft drop shadows, em-dash attributions, a round-number social-proof stat, two-column image-left/text-right sections, a product cover with shadow or tilt.
- **Confound flags:** 5 prompt-artifact, 7 original-brand-specific, 4 unclear. Font-choice features are counted as possible signatures (your decision); the generators picked fonts because the original files weren't in the prompt.
- **v1 → v2 variation:** the two single-file runs differ in palette (dark green vs. navy and gold), so one sample per variant is a poor basis for anything beyond "stable features recur".

## Limitations
- **One site, one prompt, four runs.** Stability across runs is not stability across sites or prompts.
- **Generator and judge are the same model family**, so judge bias toward its own style is possible. No second judge model was used.
- **Single human grader**; blank grades were assumed correct (6 items in v2).
- **Subagent generation**, not standalone Claude Code sessions, so the generation setup differs from a real vibe-coding session.
- **Clustering and confound flags** were produced by an agent; only evidence IDs were validated, not that each ID truly supports its feature.
- **Desktop only** (mobile dropped by decision).
- **Original-vs-regeneration differences mix** generator style with 2021-vs-now design trends; there's no post-2023 human control (excluded by decision), so "looks vibe-coded" is inferred, not tested.

## Recommended before Phase 2
1. Script generation and judging (including a CLI run once logged in), and log model ID, prompt, and token cost per call.
2. Pre-compute DOM and metadata claims (tag counts, title, fonts, colors) programmatically and give them to the judge as facts.
3. Add a second judge model and a spot-check of feature-to-evidence links.
4. Add a programmatic copy-fidelity check (does every sentence in `copy.md` appear on the page?).
5. Tell the generator what each image is (for example the overlay), or accept the misalignment as a feature and record it.
6. Run each prompt 3 times per variant on the new sites to separate stable features from run noise.
7. Choose the 30 sites by stratified category, and review `images_manifest.json` drops per site.

## Rough cost
Each generation took about 25–50 seconds and about 42–44k subagent tokens; each judge call about 45–48k tokens and 35–47 seconds. At 30 sites × 2 variants × 3 repeats plus judging, this is roughly 16M tokens (about 180 generations at ~43k plus 180 judge calls at ~47k); budget accordingly.
