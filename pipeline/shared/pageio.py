"""Shared page helpers for the annotation judges: screenshot slicing, JSON-array parsing, compact DOM facts (moved here from the archived judge.py / check_observations.py)."""
import os, re, json, pathlib
from PIL import Image
CLAUDE = os.path.expanduser("~/.local/bin/claude"); SLICE_H = 1300
KEYS = ["title", "h1_count", "semantic", "counts", "fonts_by_element_count", "body_font_size", "body_line_height", "h1", "h2", "colors", "primary_button", "effects", "layout", "classes", "text_stats", "image_overlaps", "meta_names", "jsonld_blocks", "lang"]

def slices(png, prefix, out):
    im = Image.open(png).convert("RGB"); n = 0
    for y in range(0, im.height, SLICE_H): im.crop((0, y, im.width, min(y + SLICE_H, im.height))).save(pathlib.Path(out) / f"{prefix}_slice_{n:02d}.png"); n += 1
    return n

def parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    i = min([x for x in (text.find("["), text.find("{")) if x >= 0]); j = max(text.rfind("]"), text.rfind("}"))
    return json.loads(text[i:j + 1])

def compact(d):
    o = {k: d.get(k) for k in KEYS}; o["tag_counts_top"] = dict(sorted(d.get("tag_counts", {}).items(), key=lambda kv: -kv[1])[:25])
    o["heading_outline_first12"] = d.get("heading_outline", [])[:12]; o["n_images"] = len(d.get("images", []))
    return o
