# Judge A/B test: compare original vs observe generated page only
4 sites: bathurst12hour_com_au, insightcentral_net, kanienkeha_net, neverskipbrunch_com. Models: claude-sonnet-5-5, claude-opus-5-5. Match = BGE-small cosine >= 0.78.

| site | A total | A about generated | A original-only | B total | A gen relative phrasing | B relative phrasing | B covered by A | A gen covered by B | A judge agreement | B judge agreement |
|---|---|---|---|---|---|---|---|---|---|---|
| bathurst12hour_com_au | 95 | 75 | 20 | 83 | 0.893 | 0.012 | 0.482 | 0.573 | 0.658 | 0.614 |
| insightcentral_net | 92 | 70 | 22 | 78 | 0.857 | 0.0 | 0.359 | 0.429 | 0.602 | 0.335 |
| kanienkeha_net | 97 | 80 | 17 | 89 | 0.863 | 0.022 | 0.225 | 0.287 | 0.665 | 0.465 |
| neverskipbrunch_com | 94 | 72 | 22 | 83 | 0.861 | 0.012 | 0.542 | 0.542 | 0.481 | 0.515 |
| **mean** | 94.5 | 74.25 | 20.25 | 83.25 | 0.869 | 0.011 | 0.402 | 0.458 | 0.602 | 0.482 |

Category mix, comparative: {'component': 46, 'layout': 45, 'typography': 36, 'color': 26, 'imagery': 24, 'decoration': 24, 'DOM/semantic structure': 19, 'copy': 18}

Category mix, observation-only: {'layout': 60, 'component': 47, 'typography': 43, 'color': 27, 'imagery': 27, 'decoration': 26, 'copy': 25, 'dom': 21}

# Unmatched examples (read these)

## bathurst12hour_com_au
Observation-only (B) with no match in comparative generated-side (A):
- ARIA usage is minimal and there is no structured data
- Class naming is sparse and not utility-based
- Only one font family is used across the whole page
- Stylesheet is inline: one style tag, no external stylesheets, one script
- Anchor count is high relative to text content
Comparative generated-side (A) with no match in observation-only (B):
- B adds a location line, 'Mount Panorama, Bathurst', that does not appear in A's header.
- B adds a location line, 'Mount Panorama, Bathurst', that does not appear in A's header.
- A's h1 is empty. B's h1 holds the tagline "AUSTRALIA’S INTERNATIONAL ENDURANCE RACE".
- B labels the partner area with a small 'OUR PARTNERS' heading. A's partner band has no heading.
- The document titles use different separators and punctuation. A uses a hyphen and a straight apostrophe; B uses a pipe and a curly apostrophe.

## insightcentral_net
Observation-only (B) with no match in comparative generated-side (A):
- The page ships with no scripts and no external stylesheets, only one inline style block.
- The copy is short, with no emoji and no em dashes.
- The class vocabulary is small and uses no utility-class (Tailwind-style) naming.
- The H1 is large, bold and centered, and is the only H1.
- The footer has a row of seven text links, then the company address, a platform credit and an affiliation disclaimer.
Comparative generated-side (A) with no match in observation-only (B):
- A has no h1; B has a single h1 hero headline
- Document language attribute differs
- B uses nav and main landmarks and more sections; A has neither nav nor main
- Copy volume differs a lot: A has about 643 words of live forum content (about 25 thread titles with authors and replies). B has about 225 words of marketing-style copy an
- The header treatment differs: A puts the logo, search bar and icons over a full-width car photo banner; B uses a slim dark sticky-style bar with text nav links

## kanienkeha_net
Observation-only (B) with no match in comparative generated-side (A):
- The hero lede asks for donations directly and ends with an exclamation, the only one on the page.
- Illustrations share a flat green and teal style with small human figures, trees and signs.
- There is no structured data and only basic meta tags.
- The markup uses few, mostly custom class names, with almost no Tailwind-style utilities.
- The markup is link- and span-heavy: 94 anchors and 106 spans against 509 words.
Comparative generated-side (A) with no match in observation-only (B):
- B includes images that A's facts do not record: protest-3.png, wearefriends.jpg and longhouse1.jpg.
- A declares the British English locale. B declares generic English.
- A's class naming is large and framework-derived (1581 class uses, 416 unique). B uses a small custom vocabulary (207 uses, 30 unique).
- A's h1 has no text, while B's h1 is a visible headline.
- B adds filter pills above the word grid. A has no equivalent filter.

## neverskipbrunch_com
Observation-only (B) with no match in comparative generated-side (A):
- The copy is written in a first-person, conversational voice and addresses the reader directly.
- The page is about 4777px tall and contains 514 words, with 56 anchor links.
- The hero has a pair of pill-shaped CTAs: one filled near-black with an arrow and one outlined.
- Plus signs and arrows are used as connectors in the copy, as in 'ABOUT + LEARN MORE →' and 'LISTEN + SUBSCRIBE'.
- Class usage is minimal: 54 class attributes, 28 of them unique, with no Tailwind-style utility classes.
Comparative generated-side (A) with no match in observation-only (B):
- B introduces new section headlines that A doesn't have, such as 'fresh off the workbench.' and 'on instagram.'
- B also uses script kickers, but fewer: only 5 elements use Homemade Apple
- The language attribute differs
- The main accent color differs: A uses an orange-gold for text, B uses a hot pink for accent text
- Newsletter forms differ: A has three square fields (first name, last name, email) and a 'GO' button, repeated in two places. B has one rounded email field and a pill 'SUB
