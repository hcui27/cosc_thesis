"""Cheap text signals for one saved homepage (domain, title, meta description, headings, first ~350 words of copy, language flags).
Used by the LLM labelling scripts. No network."""
import re
from bs4 import BeautifulSoup
from skeletonize import Skeleton

def features(f):
    h = f.read_text(errors="ignore"); soup = BeautifulSoup(h, "html.parser")
    meta = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    heads = [x.get_text(" ", strip=True)[:80] for x in soup.find_all(["h1", "h2"])][:8]
    md = Skeleton(f"http://{f.stem}/", "20210601000000", ".", fetch=False).to_markdown(h)
    text = " ".join(re.sub(r"!\[[^\]]*\]\([^)]*\)|\[([^\]]*)\]\([^)]*\)", r"\1", md).split()[:350])
    langs = sorted({m.lower() for m in re.findall(r'\blang=["\']?([a-zA-Z-]+)', h)})
    return {"domain": f.stem, "title": (soup.title.get_text(strip=True)[:120] if soup.title else ""),
            "description": (meta.get("content", "")[:200] if meta else ""), "headings": heads, "copy_start": text,
            "_hreflang": len(re.findall(r"hreflang=", h)), "_lang_attrs": ";".join(langs)}
