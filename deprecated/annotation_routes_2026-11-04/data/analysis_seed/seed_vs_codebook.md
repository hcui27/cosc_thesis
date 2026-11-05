# Seed list vs self-generated codebook
79 seed items (external glossaries), 314 codebook attributes, 28 pages. No culling applied.

## Seed items: pertinence on these pages
- mentioned by the judges on >= 1 page: 56 of 79; on >= 3 pages: 36; on >= half the pages: 17; on no page: 23
- by kind (mentioned on >= 1 page): component 44/66, page_section 12/13

## Codebook attributes vs the seed list
- ABOUT a seed item: 165 (5 is the item itself, 160 a property/variant of it)
- ADDED by the codebook (not about any seed item): 149 of 314 (47%)
- by family (is_item / property_of_item / none): color: 0/13/25; component: 2/60/8; copy: 0/10/20; decoration: 1/12/7; imagery: 0/15/14; layout: 0/33/22; other: 0/0/3; semantic_dom: 2/5/20; typography: 0/12/30
- seed items no codebook attribute is about: 45 of 79; of those mentioned on >= 3 pages (codebook gaps): 8: Blog Sections, Feature Sections, Dropdown menu, Select, Toggle, Button group, Segmented control, feed

## Distributions to compare (share of pages where the thing is present)
- seed items (prevalence): median 0.07, mean 0.25
- codebook attributes about the item itself: median 0.14, mean 0.34
- codebook property/variant attributes: median 0.48, mean 0.53
- codebook attributes ADDED (not in seed): median 0.82, mean 0.71
- modal-share bands (shared >= .75 / split / varied): is_item: {'shared': 4, 'split': 1}; property_of_item: {'split': 61, 'varied': 25, 'shared': 74}; none: {'split': 78, 'shared': 48, 'varied': 23}

Figure: seed_vs_codebook.png. Row-level table: seed_vs_codebook.csv. Relation labels are one LLM pass (not human-checked).
