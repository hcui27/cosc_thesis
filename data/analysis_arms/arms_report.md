# Observation-only arm vs comparison-judge arm (same 28 generated pages)

## Observations
- observation-only: 2379 observations (85 per page). comparison: 2531 (90 per page); sides {'generated': 432, 'both': 1654, 'original': 445}
- comparison observations about the ORIGINAL only (never reach the codebook): 445 (18%)
- relative phrasing (mentions side A/B, original, 'whereas', 'instead of' ...): observation-only 60%, comparison generated/both 99%
- cross-arm coverage within the same page (cosine >= 0.78): 36% of observation-only observations have a comparison counterpart; 43% of comparison generated-side observations have an observation-only counterpart (lowered by relative phrasing)
- tiers, observation-only: {'A': 2087, 'B': 275, 'C': 17}
- tiers, comparison: {'A': 2228, 'B': 274, 'C': 29}

## Codebooks
- attributes: observation-only 314, comparison 284; values 1136 vs 1010
- matched attributes (mutual nearest, cosine >= 0.80 on name+definition): 124; unique to observation-only 190; unique to comparison 160
- unique to observation-only by family: {'color': 17, 'component': 46, 'copy': 23, 'decoration': 13, 'imagery': 21, 'layout': 30, 'other': 2, 'semantic_dom': 18, 'typography': 20}
- unique to comparison by family: {'color': 15, 'component': 48, 'copy': 7, 'decoration': 19, 'imagery': 5, 'layout': 31, 'other': 1, 'semantic_dom': 13, 'typography': 21}
- examples unique to observation-only: hero tagline styling; link label emphasis; eyebrow kicker above headings; card text hierarchy; section heading size and color; font pairing system; heading to body size contrast; heading letter case; announcement bar text styling; pull quote typography; section heading size; section heading text treatment
- examples unique to comparison: icon font usage; button label casing; promo headline treatment; card title weight; card title case; link text case and weight; eyebrow label treatment; accent display face; announcement bar text and link style; copyright text styling; date visual treatment; meta separator

## Matched attributes: do the arms find the same pages the same way?
- 124 matched attributes with codes in both; same band (shared/split/varied) 56%; mean abs difference in modal share 0.14
- band distribution over ALL attributes: observation-only {'shared': 126, 'split': 140, 'varied': 48}, comparison {'shared': 121, 'split': 124, 'varied': 39}
- seed relation, observation-only: {'none': 149, 'property_of_item': 160, 'is_item': 5}; added (none) share 47%; median presence of added attributes 0.82
- seed relation, comparison: {'none': 110, 'property_of_item': 170, 'is_item': 4}; added (none) share 39%; median presence of added attributes 0.71