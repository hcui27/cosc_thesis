# Attribute-value variation across 28 generated pages
278 attributes coded on at least 15 pages. Bands by modal-value share: shared (>= 0.75) 118, split (0.5-0.75) 116, varied (< 0.5) 44.

Pairwise agreement between pages over all attributes: mean **0.573** (descriptive only: it equals what independent coding with the same value frequencies would give, so it measures how concentrated the choices are, not clustering). Spread across page pairs: SD 0.0473 vs permutation null 0.0269 (95% of nulls 0.0239-0.0298): some pages resemble each other MORE than independent coding would give (structure / clusters).

By modal value type: shared presence (modal share >= 0.75, a feature is there) 58; shared absence/other (the modal value says the feature is absent or not applicable) 60.

## Bands by family
- color: {'shared': 7, 'split': 16, 'varied': 11}
- component: {'shared': 36, 'split': 28, 'varied': 10}
- copy: {'shared': 5, 'split': 12, 'varied': 6}
- decoration: {'shared': 8, 'split': 6, 'varied': 2}
- imagery: {'shared': 1, 'split': 3, 'varied': 4}
- layout: {'shared': 28, 'split': 12, 'varied': 9}
- semantic_dom: {'shared': 16, 'split': 15, 'varied': 2}
- typography: {'shared': 17, 'split': 24}

## Most shared PRESENT values (modal share, modal value is not an absence/other value)
| attribute | modal value | share | coded | normalised entropy |
|---|---|---|---|---|
| ARIA accessibility attributes | present | 1.0 | 28 | 0.0 |
| content container constraint | constrained container | 1.0 | 28 | 0.0 |
| content horizontal alignment | centered container | 1.0 | 28 | 0.0 |
| microcopy_length_style | concise_short_labels | 1.0 | 28 | 0.0 |
| section title heading level | h2 | 1.0 | 28 | 0.0 |
| semantic landmark usage | broad landmark set | 1.0 | 28 | 0.0 |
| side margin generosity | generous side margins | 1.0 | 28 | 0.0 |
| text line length in containers | comfortable measure | 1.0 | 28 | 0.0 |
| DOM leanness | lean | 0.964 | 28 | 0.222 |
| band container treatment | full-width band | 0.964 | 28 | 0.222 |
| card and item title heading level | h3 | 0.964 | 28 | 0.222 |
| image embedding method | img elements | 0.964 | 28 | 0.222 |
| layout system | grid and flex | 0.964 | 28 | 0.222 |
| left edge consistency | consistent shared left edge | 0.964 | 28 | 0.222 |
| link group markup | ul/li list | 0.964 | 28 | 0.222 |
| main column width | wide | 0.964 | 28 | 0.222 |
| overall page structure | stacked full-width sections | 0.964 | 28 | 0.222 |
| CSS class naming approach | handwritten semantic classes | 0.929 | 28 | 0.371 |
| card text alignment | left-aligned | 0.929 | 28 | 0.371 |
| form and control quantity | minimal | 0.929 | 28 | 0.279 |
| gradient_and_motion_usage | minimal | 0.929 | 28 | 0.371 |
| heading rendering | live styled text | 0.929 | 28 | 0.279 |
| primary CTA fill style | solid filled | 0.929 | 28 | 0.279 |
| call-to-action button presence | present | 0.893 | 28 | 0.491 |
| card grid arrangement | multi-column grid | 0.893 | 28 | 0.372 |
| card text alignment | left aligned | 0.893 | 28 | 0.372 |
| footer link presentation | plain text links | 0.893 | 28 | 0.372 |
| heading markup for non-title text | headings only for titles | 0.893 | 28 | 0.491 |
| marketing_microcopy_presence | concise_marketing | 0.893 | 28 | 0.491 |
| transition richness | hover_transitions_defined | 0.893 | 28 | 0.491 |

![top](attribute_modal_share.png)

## Most varied attributes (lowest modal share)
| attribute | modal value | share | values used |
|---|---|---|---|
| accent color hue | red | 0.286 | 6 |
| hero background treatment | photo | 0.321 | 5 |
| primary button fill color | other accent | 0.357 | 6 |
| link color | other accent | 0.357 | 5 |
| intro section column structure | single column | 0.357 | 4 |
| image alt text quality | partially missing or generic | 0.357 | 5 |
| icon implementation type | SVG or image icons | 0.357 | 4 |
| hero layout | two-column split | 0.357 | 5 |
| hero imagery | gradient or artwork only | 0.357 | 5 |
| header composition | multi-row or tiered header | 0.357 | 3 |
| content grid column count | three columns | 0.357 | 4 |
| badge color treatment | other | 0.357 | 4 |
| section background treatment | tinted solid | 0.393 | 4 |
| quick-link item style | other | 0.393 | 5 |
| promo block background | dark or grey flat | 0.393 | 5 |

## Against the originals
Not computed: run code_pages.py --which original (about the same cost as the generated run).

## Coder reliability (vision coder vs values coded from the judges' observations)
Overall 72% over 1421 comparisons; by family: color 74%, component 72%, copy 56%, decoration 64%, imagery 55%, layout 76%, semantic_dom 76%, typography 74%. Neither side is ground truth.
