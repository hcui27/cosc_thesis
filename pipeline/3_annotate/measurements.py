"""Programmatic page measurements computed from render.py's dom.json (ground truth, no LLM).
KEYS documents every measurement; catalog features can name one as a PROXY: {"key": ..., "op": ">=", "value": 1}, which makes the feature
programmatically detectable (ANALYSIS_PLAN.md: programmatic whenever the page facts can compute it).
compute(dom) -> {key: number or None}; check(m, proxy) -> 1 / 0 / None.
"""
import re, colorsys, operator

KEYS = {
 "radius_pill_count": "elements with fully rounded (pill/circle) corners",
 "radius_round_share": "share of elements with border radius >= 8px (incl. pills)",
 "radius_zero_share": "share of elements with square corners",
 "shadow_count": "elements with a box-shadow",
 "shadow_share": "share of elements with a box-shadow",
 "gradient_count": "elements with a gradient background",
 "backdrop_blur_count": "elements with backdrop blur (glassmorphism)",
 "transition_count": "elements with CSS transitions", "animation_count": "elements with CSS animations", "transform_count": "elements with a CSS transform",
 "emoji_count": "emoji characters in the visible text", "emdash_count": "em dashes in the visible text", "exclamation_count": "exclamation marks in the visible text",
 "serif_primary": "1 if the most common font family is a serif face", "sans_primary": "1 if the most common font family is a sans-serif face",
 "font_family_count": "distinct font families among the top families used",
 "h1_size_px": "computed font size of the first h1", "body_size_px": "computed body font size", "h1_body_ratio": "h1 size divided by body size",
 "h1_weight": "font weight of the first h1", "h1_centered": "1 if the first h1 is center aligned",
 "bg_colors_top": "distinct background colors among the 8 most used", "saturated_bg_colors": "of those, colors with saturation > 0.35",
 "body_bg_lightness": "lightness (0-1) of the body background", "body_bg_dark": "1 if the body background is dark (lightness < 0.35)",
 "accent_hue": "hue in degrees of the most used saturated background color", "accent_saturation": "saturation of that color",
 "text_color_lightness": "lightness of the body text color",
 "semantic_tag_count": "header+nav+main+section+article+aside+footer+figure elements", "section_count": "section elements",
 "aria_attr_count": "aria-* attributes", "heading_count": "h1-h4 headings", "h1_count": "h1 elements", "meta_tag_count": "meta tags in head", "jsonld_blocks": "JSON-LD blocks",
 "tailwind_like_fraction": "share of class names that look like Tailwind utilities", "inline_style_attrs": "elements with inline style attributes",
 "script_count": "script elements", "stylesheet_count": "linked stylesheets", "svg_count": "inline svg elements",
 "grid_count": "elements using display:grid", "flex_count": "elements using display:flex",
 "page_height": "full page height in px", "word_count": "visible words", "image_count": "img elements", "anchor_count": "links", "button_count": "button elements",
 "image_overlap_count": "pairs of images whose boxes overlap",
 "primary_button_radius_px": "corner radius of the primary button", "primary_button_pill": "1 if the primary button is fully rounded",
}
SERIFS = {"georgia", "times new roman", "times", "playfair display", "merriweather", "lora", "garamond", "eb garamond", "baskerville", "cambria", "palatino", "crimson text",
          "cormorant garamond", "libre baskerville", "source serif pro", "pt serif", "noto serif", "dm serif display", "bitter", "spectral"}

def _rgb(s):
    m = re.match(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)", s or "")
    return tuple(int(x) / 255 for x in m.groups()) if m else None

def _hls(s):
    c = _rgb(s)
    if not c: return None
    h, l, sat = colorsys.rgb_to_hls(*c); return h * 360, l, sat

def _px(s):
    m = re.match(r"([\d.]+)", str(s or "")); return float(m.group(1)) if m else None

EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\u2B55\u231A-\u23FF]")  # pictographs only: not (c) (R) (TM)

def compute(d, text=None):
    """d = dom.json dict; text = the page's text.txt (optional: lets emoji be recounted without (c)/(R)/(TM))."""
    e, c, ly, t = d.get("effects", {}), d.get("counts", {}), d.get("layout", {}), d.get("text_stats", {})
    rb = e.get("border_radius_buckets", {}); tot = max(sum(rb.values()), 1); n_el = max(sum(d.get("tag_counts", {}).values()), 1)
    fonts = [f for f, _ in d.get("fonts_by_element_count", [])]; main = (fonts[0] if fonts else "").lower()
    h1, bs = _px((d.get("h1") or {}).get("font_size")), _px(d.get("body_font_size"))
    bgs = d.get("colors", {}).get("top_backgrounds", []); hls = [(_hls(k), n) for k, n in bgs]; hls = [(x, n) for x, n in hls if x]
    sat = [(x, n) for x, n in hls if x[2] > 0.35 and 0.1 < x[1] < 0.95]
    top = max(sat, key=lambda a: a[1])[0] if sat else None
    body = _hls(d.get("colors", {}).get("body_bg")); txt = _hls(d.get("colors", {}).get("body_color")); sem = d.get("semantic", {})
    pb = d.get("primary_button") or {}; pr = _px(pb.get("radius"))
    m = {"radius_pill_count": rb.get("bucket_pill", 0), "radius_round_share": (rb.get("bucket_8_15", 0) + rb.get("bucket_16_plus", 0) + rb.get("bucket_pill", 0)) / tot,
         "radius_zero_share": rb.get("bucket_0", 0) / tot, "shadow_count": e.get("box_shadows", 0), "shadow_share": e.get("box_shadows", 0) / n_el,
         "gradient_count": e.get("gradient_backgrounds", 0), "backdrop_blur_count": e.get("backdrop_blur", 0), "transition_count": e.get("transitions", 0),
         "animation_count": e.get("animations", 0), "transform_count": e.get("transforms", 0), "emoji_count": (len(EMOJI.findall(text)) if text is not None else t.get("emoji", 0)), "emdash_count": t.get("em_dashes", 0),
         "exclamation_count": t.get("exclamations", 0), "serif_primary": int(main in SERIFS), "sans_primary": int(bool(main) and main not in SERIFS),
         "font_family_count": len({f for f in fonts}), "h1_size_px": h1, "body_size_px": bs, "h1_body_ratio": (h1 / bs) if h1 and bs else None,
         "h1_weight": _px((d.get("h1") or {}).get("font_weight")), "h1_centered": int((d.get("h1") or {}).get("text_align") == "center") if d.get("h1") else None,
         "bg_colors_top": len(bgs), "saturated_bg_colors": len(sat), "body_bg_lightness": body[1] if body else None, "body_bg_dark": int(body[1] < 0.35) if body else None,
         "accent_hue": top[0] if top else None, "accent_saturation": top[2] if top else None, "text_color_lightness": txt[1] if txt else None,
         "semantic_tag_count": sum(sem.get(k, 0) for k in ("header", "nav", "main", "section", "article", "aside", "footer", "figure")), "section_count": sem.get("section", 0),
         "aria_attr_count": c.get("aria_attrs", 0), "heading_count": len(d.get("heading_outline", [])), "h1_count": d.get("h1_count", 0), "meta_tag_count": len(d.get("meta_names", [])),
         "jsonld_blocks": d.get("jsonld_blocks", 0), "tailwind_like_fraction": d.get("classes", {}).get("tailwind_like_fraction", 0), "inline_style_attrs": c.get("inline_style_attrs", 0),
         "script_count": c.get("scripts", 0), "stylesheet_count": c.get("stylesheets", 0), "svg_count": c.get("svgs", 0), "grid_count": ly.get("display_grid", 0), "flex_count": ly.get("display_flex", 0),
         "page_height": ly.get("page_height"), "word_count": t.get("words", 0), "image_count": c.get("images", 0), "anchor_count": c.get("anchors", 0), "button_count": c.get("buttons", 0),
         "image_overlap_count": len(d.get("image_overlaps", [])), "primary_button_radius_px": pr, "primary_button_pill": int(pr >= 999 or pr >= 24) if pr is not None else None}
    return m

OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq}

def check(m, proxy):
    """Evaluate a proxy {"key","op","value"} on measurements m -> 1 / 0 / None (unknown or malformed)."""
    try:
        v = m.get(proxy["key"]); f = OPS[proxy["op"]]
        return None if v is None else int(f(v, float(proxy["value"])))
    except Exception: return None
