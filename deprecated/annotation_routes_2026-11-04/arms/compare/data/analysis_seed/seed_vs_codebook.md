# Seed list vs self-generated codebook
79 seed items (external glossaries), 284 codebook attributes, 28 pages. No culling applied.

## Seed items: pertinence on these pages
- mentioned by the judges on >= 1 page: 58 of 79; on >= 3 pages: 44; on >= half the pages: 17; on no page: 21
- by kind (mentioned on >= 1 page): component 46/66, page_section 12/13

## Codebook attributes vs the seed list
- ABOUT a seed item: 174 (4 is the item itself, 170 a property/variant of it)
- ADDED by the codebook (not about any seed item): 110 of 284 (39%)
- by family (is_item / property_of_item / none): color: 0/17/14; component: 2/56/20; copy: 0/5/10; decoration: 0/16/10; imagery: 0/8/4; layout: 2/31/22; other: 0/0/1; semantic_dom: 0/13/11; typography: 0/24/18
- seed items no codebook attribute is about: 41 of 79; of those mentioned on >= 3 pages (codebook gaps): 11: Form, Dropdown menu, Modal, Select, Toggle, Contact Sections, Button group, Testimonials, Table, Tabs, Textarea

## Distributions to compare (share of pages where the thing is present)
- seed items (prevalence): median 0.11, mean 0.27
- codebook attributes about the item itself: median 0.04, mean 0.09
- codebook property/variant attributes: median 0.54, mean 0.54
- codebook attributes ADDED (not in seed): median 0.71, mean 0.64
- modal-share bands (shared >= .75 / split / varied): is_item: {'shared': 3, 'split': 1}; property_of_item: {'shared': 78, 'varied': 27, 'split': 65}; none: {'shared': 40, 'split': 58, 'varied': 12}

Figure: seed_vs_codebook.png. Row-level table: seed_vs_codebook.csv. Relation labels are one LLM pass (not human-checked).
