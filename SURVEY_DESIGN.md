# Human baseline survey: rough design (draft, 2026-10-31; note added 2026-11-04)

> **Note 2026-11-04.** The annotation pipeline was redesigned (see PLAN.md, pipeline 3): the codebook and the observation-only / comparison arms mentioned below are archived. The human instrument should now be compared with the **master list** (attributes and values, family -> attribute -> value) and the 120-item **seed list v1.3**, not with the old 278-attribute codebook or the 79-item v1.1 list. Where the text says "codebook attribute" read "master-list attribute", and "79 (v1.1)" read "120 (v1.3)". The G1 / G2 groups correspond to the new observe-alone and combine steps. Nothing here has been run.

Purpose: a second, human instrument for the same question the pipeline answers, **which visual features are inherent to vibe-coded websites**. Humans produce their own feature signature of the 28 vibe-coded pages; it is compared with the LLM signature (observation-only arm, comparison arm). It is a baseline, not a grader of the pipeline. Nothing here is run yet; no human subjects work starts before CPHS review.

## Decisions made in this draft (change any of them)
- Headline comparison is **prevalence only** (share of the 28 sites showing a feature), human vs LLM. No lift against human-made sites in the headline, because the originals are not coded with the codebook. Originals are a secondary, human-only contrast (Part D).
- Reviewers are **blind to source** in the main groups (matches the observation-only judges, whose prompt never says the page is AI-made). A small informed group measures the stereotype shift.
- Only **visible** features are compared (typography, color, layout, components, decoration, imagery, copy style). Semantic-DOM attributes are excluded from the human comparison.
- Reviewers see screenshots only (1440 px full page, same render as the judges; no URLs, no browser chrome).

## Groups and stimuli
| Group | Sees | Told source? | Reviewers | Pages each |
|---|---|---|---|---|
| G1 observation-only (main) | one generated page | no | ~10 | 20 of the 28 |
| G2 comparison | original (A) beside generated (B), same page | no | ~10 | 14 of the 28 pairs |
| G3 informed (optional) | one generated page | yes, "built by an AI coding agent" | ~5 | 20 of the 28 |
| Wild check | 10 screenshots from the deprecated wild sites, interleaved into G1 | no | same as G1 | +4 each |

- Assignment: balanced incomplete blocks so every page gets at least 5 G1 ratings and at least 5 G2 ratings. Page order is randomized per reviewer; wild pages are interleaved, never grouped.
- Wild pages must first be re-rendered like the rest, stripped of logos and URLs, and have a provenance note kept outside the survey. The observation-only judges should also be run on them (about $5) so they have LLM observations to compare.
- Reviewer mix: roughly half designers or developers, half laypeople. Record expertise (below).

## Flow (about 55 minutes in two sessions, break every 30 minutes)
**Screen 0. Consent and background.** Consent text (CPHS), then: years of design or web experience (none / under 2 / 2-5 / over 5), role (designer, developer, other technical, non-technical), hours online per day, and "have you used an AI website builder?" (never / tried / regularly). No questions that identify the person.

**Screen 1. Instructions and practice.** One practice page with an example answer. Rules: describe only what you can see; do not guess about code, intent or quality; do not search for the site; if you recognize it, tick the box and continue.

**Part A. Free observation (per page, about 4 minutes).**
- Show the page (scrollable full-page image, zoomable).
- Prompt (G1/G3): "List 8 to 15 specific things you notice about how this page looks and is laid out. One per line. Describe, do not judge."
- Prompt (G2): "List 8 to 15 specific differences between page A and page B. One per line. For each, say which side it is about (A, B, both)."
- Each line has an optional "where on the page" tag (top / middle / bottom / whole page). No box for opinions about quality.
- Checkbox: "I recognize this site" (those ratings are dropped).

**Part B. Closed checklist (per page, about 3 minutes; sees the same page again after finishing Part A, so free text is never primed).**
- 12 attributes from the codebook, drawn so each family appears at least once and the three bands (shared, split, varied) are all represented. Each attribute shows its definition and its value list, with "not present" and "can't tell" options. Choose one.
- Seed items: 15 items from the 120 (v1.3), tick all present. Includes 3 that the judges never mention, as a check.
- Attribute and item draws are rotated across reviewers so every attribute is answered for each page by at least 3 reviewers.

**Part C. Confidence and cues (G3 only).** "How AI-made does this look?" (forced choice AI / human), confidence 1 to 5 (1 guessing, 2 slight lean, 3 moderate, 4 fairly sure, 5 certain), and "what made you think so?" free text. G1 and G2 never see this part, so it can't prime them.

**Part D. Originals contrast (G2 only, at the end).** Five original pages alone, same free-observation prompt as G1. Gives a human-only look at what the original sites have, for the secondary lift analysis.

## Quality controls
- 2 attention pages per session (a page with an obvious, instructed feature such as a bright red banner). Reviewers who miss both are dropped.
- Every reviewer sees 2 pages twice (different positions) to measure self-consistency.
- Time floor per page; flag implausibly fast submissions.
- No decoys here. (Decoys belong to the coder-verification study, which is a separate, smaller task: see the end.)

## What the data looks like
- `responses_free.csv`: reviewer, group, page, line_no, text, side (G2), region.
- `responses_checklist.csv`: reviewer, page, attribute_id or seed item, chosen value or `not_present` / `cant_tell`.
- `reviewers.csv`: expertise and AI-builder familiarity, kept separate from responses and keyed by an anonymous id.

## Turning free text into the same schema
1. A blind coder (LLM, then human adjudication on 20% of lines) maps each free-text line to a codebook attribute and value, a seed item, or "new feature".
2. A second human codes a random 20% for inter-coder agreement (Cohen's kappa; report per family).
3. Lines tagged "new feature" are clustered by hand to find what humans notice that the codebook lacks.

## Analysis
- **Human signature:** for each feature, the share of pages where at least 2 reviewers noted it (free text) or chose its value (checklist). The thresholds are pre-registered.
- **Comparison with the LLM arms:** Spearman correlation of prevalence over all shared visible features; overlap (Jaccard, precision, recall) of the "inherent" sets; both for G1 vs observation-only and G2 vs comparison.
- **Noise ceiling:** split the reviewers randomly into halves, build two human signatures, compute the same agreement; repeat 1,000 times. The LLM-vs-human agreement is interpreted against this ceiling.
- **Stability:** bootstrap over pages and over reviewers.
- **Expertise:** the above split by designer/developer vs layperson.
- **Stereotype shift:** G3 vs G1 on the same pages (features cited more when told it is AI).
- **Wild check:** do the features both instruments call inherent also recur on the 10 wild pages? Per page only; no pooled rates.
- **Disagreements** (LLM-only, human-only features) are reported as findings, not errors.

## Pilot
2 reviewers, 6 pages, full flow. Check time per page, whether the checklist wording is clear, and whether free-text lines map to attributes. Revise before recruiting.

## Open points
- Recruitment source and compensation (needs CPHS).
- Whether to drop G3 to save reviewers.
- Whether to also code the originals with the codebook so the headline gets a lift measure (reverses an earlier decision).
- How to run the DOM attributes (developers with browser tools) if they should be included.

## Separate smaller task: coder verification (not part of the baseline)
Show the coder's evidence crop with a red outline plus the attribute and value; reviewers answer yes / no / can't tell. Include about 20% decoys (same attribute, different value or another page's crop) to catch rubber-stamping. Report precision per family, decoy false-accept rate and kappa. Run it after the checklist, never before, so the LLM labels cannot prime reviewers' own answers.
