"""DESIGNER-BRIEF layer between the sanitized copy and the generator (added 2026-11-04).
usage: python pipeline/2_build_sites/brief.py <site_dir> [--model claude-sonnet-5-5]
Reads data/<site>/prompt/copy.md (skeleton copy after sanitize.py: verbatim text with neutral image references) and rewrites it as the CONTENT BRIEF a designer would hand to someone building the site:
the same facts, names, offerings, numbers, contact details and URLs, restated in new words and translated to English if needed, NOT the original sentences. Content only: no layout, style, placement or purpose/audience
statements. Each image reference ![](images/x) is kept exactly once, next to the content it accompanies. Why: the generator no longer sees the page's own wording, so memorised pages cannot be reproduced
and the Tranco rank > 100k exclusion is no longer needed for contamination.
Writes data/<site>/prompt/brief.md (what generate.py gives the agent) and keeps the verbatim text in data/<site>/copy_verbatim.md (never shown to the generator); removes prompt/copy.md. Resumable: skips if brief.md exists.
"""
import sys, re, pathlib, shutil
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]
from llm import ask_text

PROMPT = """You are a designer's assistant. Below is the text content of a website's home page, in markdown, with image references like ![](images/name.jpg).
Write the CONTENT BRIEF a designer would give to a person who will build this website. Rules:
- Restate ALL the substantive content in your own words: who or what the organisation is, what it offers, names, products, services, prices, numbers, dates, addresses, phone numbers, emails and URLs (keep these exact), lists of items, quotes' meaning, calls to action.
  Do NOT copy sentences or headlines verbatim (names, numbers, URLs, and short product or service names stay as they are). If the text is not in English, write the brief in English.
- Content only. Do NOT describe layout, order of sections on the page, colours, fonts, style, mood, branding feel, target audience, or the purpose of the site, and do not suggest any design. Avoid words such as hero, banner, header, footer, section, sidebar, above the fold, top of the page.
- Keep every image reference EXACTLY as written (![](images/...)), each exactly once, placed next to the piece of content it accompanies. Do not describe the images.
- Plain markdown, grouped by topic with simple headings you invent from the content. No preamble and no closing remarks.

TEXT:
{text}"""

def brief(site_dir, model="claude-sonnet-5-5"):
    root = pathlib.Path(site_dir); pr = root / "prompt"; out = pr / "brief.md"
    if out.exists(): return {"skipped": True}
    src = (pr / "copy.md").read_text(); refs = re.findall(r"!\[\]\((images/[^)]+)\)", src)
    for attempt in range(2):
        txt = ask_text(PROMPT.format(text=src), model, "designer_brief", site=root.name, words_in=len(src.split()))
        txt = re.sub(r"^```(?:markdown)?\n|\n```$", "", txt).strip() + "\n"
        got = re.findall(r"!\[\]\((images/[^)]+)\)", txt)
        if sorted(got) == sorted(refs): break
    else:
        miss = [r for r in refs if r not in got]; txt += "\n" + "\n".join(f"![]({r})" for r in miss) + "\n"     # last resort: append any image the rewrite dropped; extras are removed below
        txt = re.sub(r"!\[\]\((images/[^)]+)\)", lambda m: m.group(0) if m.group(1) in refs else "", txt)
    shutil.copy2(pr / "copy.md", root / "copy_verbatim.md"); out.write_text(txt); (pr / "copy.md").unlink()
    return {"words_in": len(src.split()), "words_brief": len(txt.split()), "images": len(refs)}

if __name__ == "__main__":
    print(brief(sys.argv[1], sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-sonnet-5-5"))
