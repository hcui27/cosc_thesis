# Master list vs seed list v1_3
120 seed items, 133 master attributes over 28 sites. Nothing culled.

## Seed items corroborated by the observations
- with at least one matched master attribute: 39 of 120; AI-built page shows it on >= 1 site: 38, >= 2: 29, >= half the sites: 10; no match: 81
- by kind (matched): component 30/107, page_section 9/13

## What the observations add beyond the seed list
- master attributes about a seed item: 67 (36 the item itself, 31 a property of it)
- ADDED (not about any seed item): 66 of 133 (49%); of those on >= 2 sites: 49; of all attributes on >= 2 sites: 104
- by family (is_item / property_of_item / none): color: 0/1/6; component: 26/12/18; copy: 5/3/10; decoration: 0/4/4; imagery: 2/2/7; layout: 2/3/4; other: 0/0/1; semantic_dom: 1/2/9; typography: 0/4/7

## Seed items never matched (81): Breadcrumbs, Button group, Checkbox, Color picker, Combobox, Date input, Datepicker, Drawer, Dropdown menu, Empty state, Fieldset, File, File upload, Label, Popover, Progress bar, Progress indicator, Radio button, Rich text editor, Segmented control, Select, Skeleton, Slider, Spinner, Stack, Stepper, Text input, Textarea, Toast, Toggle, Tooltip, Tree view, Visually hidden, text, checkbox group, comment, listbox, feed, Pricing Sections, Bento Grids, Team Sections, Content Sections, Close button, Figure, Media object, Menu, Input group, Floating label, Box, Section, Level, Icon link, Focus ring, Scrollspy, Sticky, Drilldown menu, Accordion menu, 2D-Matrix Input Control, Anchor Link, Back-to-Top Button, Bottom Sheet, Contextual Menu, Control, Expandable Menu, Floating Button, Input Control, Input Stepper, Knob, Lightbox, Megamenu, Menu Bar, Overlay, Picker, Pie Menu, Popup Tip, Ribbon, Scrollbar, Split Button, State-Switch Control, Submenu, Wheel Picker

## Added attributes seen on the most sites
- color palette (color, 28 sites): Nearly every AI-built page changes the overall palette, most often to a navy/blue family, with teal/green, warm cream with orange or rust accents, and dark near-black schemes as the other common outcomes, and only one keeping the original brand palette.
- copy tone (copy, 28 sites): Copy tone was either kept close to the original or flattened into short, plain, sentence-case, non-exclamatory and often third-person text, with no emoji or em dashes.
- corner radius (decoration, 28 sites): Most AI-built pages change the original's square corners to small rounding (often with pill shapes on buttons or tags), while a few go to larger radii and only two keep square corners.
- visual effects (decoration, 28 sites): The AI-built pages mostly reduce effects, with many original transitions cut back or removed and shadows or gradients swapped for flat styling and thin borders, though about a quarter keep an already minimal effect set and a few add header backdrop blur or other effects.
- page layout (layout, 28 sites): Most AI-built pages move to a flex-plus-grid layout, replacing floats, flexbox-only or tables, and many collapse sidebar layouts into single-column or stacked full-width sections.
- dom structure (semantic_dom, 28 sites): On nearly all sites the DOM is slimmed from heavy CMS, plugin or div-laden markup to minimal markup with few custom classes and a single inline stylesheet in place of many scripts and stylesheets.
- heading hierarchy (semantic_dom, 28 sites): Almost all AI-built pages replace flat, irregular or empty heading outlines with a single-h1 structured hierarchy, most often h1–h3 and sometimes h1–h4, with only two sites keeping an out-of-order outline.
- landmark elements (semantic_dom, 28 sites): Most AI-built pages swap generic divs for semantic landmarks (header, nav, main, sections, often footer or articles), while others consolidate repeated headers, navs and sections into single instances.
- body typeface (typography, 28 sites): Body typefaces were replaced on every site, most commonly with a system-ui stack and otherwise with Georgia plus a sans pairing or a Helvetica stack.
- image alt text (semantic_dom, 27 sites): The most common outcome is that missing, empty or generic alt text is replaced with descriptive alts, often with empty alts reserved for decorative images.
- page metadata (semantic_dom, 27 sites): The dominant pattern is that rich social, JSON-LD and platform meta tags are cut to a minimal set, with titles shortened or simplified and empty lang attributes set to en.
- body text size and line height (typography, 27 sites): Body text was almost always normalized to 16–17px with a 1.6–1.65 line height regardless of the original size or spacing.
- section backgrounds (color, 23 sites): Most AI-built pages break the page into alternating full-width section bands, typically white or cream alternating with pale tints or dark navy/slate bands, replacing plain white or the original's differing banding.
- page length (layout, 23 sites): Page height changes on most sites, most often with a very tall page becoming much shorter, while a smaller group becomes taller and a few lose empty gaps above the footer.
- logo (imagery, 22 sites): Logos are most often shrunk or turned into styled text wordmarks, with a minority kept as the original image and a few repositioned.
