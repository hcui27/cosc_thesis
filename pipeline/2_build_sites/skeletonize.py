"""Fetch a Wayback snapshot and build the generator prompt inputs: copy.auto.md + images/ (run sanitize.py afterwards).

usage: python skeletonize.py <url> <wayback_timestamp> <out_dir>

Image rules
  * <img>: the real source is picked in this order: lazy-load attributes (data-src, data-lazy-src, data-original, ...), a normal src,
    then the widest srcset candidate. data: URIs / blank-spacer placeholders / 1x1 tracking pixels are dropped.
  * <picture><source>: desktop sources are saved (sources with a max-width media query are mobile-only and dropped).
  * inline <svg role="img"> with a <title> -> saved as a file (e.g. logos).
  * CSS background images (raster png/jpg/jpeg/gif/webp only) from linked stylesheets, <style> blocks AND inline style="" attributes,
    on elements that exist in the page (no pseudo-elements) -> included, placed in the copy at that element.
  * everything else (SVG patterns, pseudo-element icons, fonts, selectors with no matching element, data: URIs) -> dropped and logged.
Copy rules
  * visible text of <body> in document order, as markdown (headings, paragraphs, lists, quotes, emphasis, links with hrefs, image refs).
  * NOT included: <head>, scripts/styles/noscript/iframes, comments, hidden/aria-hidden elements, boilerplate by class/id (see BOILER),
    and elements hidden on load (the last applicable display declaration is none): inline style="display:none", or a top-level stylesheet rule with display:none that applies at a 1440px desktop width (@media min/max-width evaluated) matching the
    element. A hidden element is kept if it also carries a responsive "show" class (Bootstrap d-md-block, Tailwind md:block, ...).
Everything dropped is logged with its reason in images_manifest.json. CSS/layout/fonts never reach the prompt.
"""
import sys, re, json, time, pathlib, urllib.parse
import requests
from bs4 import BeautifulSoup, NavigableString, Tag, Comment, Doctype, ProcessingInstruction, Declaration, CData

RASTER = (".png", ".jpg", ".jpeg", ".gif", ".webp")
SKIP_TAGS = {"script", "style", "noscript", "head", "template", "iframe"}
BOILER = re.compile(r"mobile-(?:nav|menu)|nav-mobile|hamburger|modal|popup|concierge|cookie|consent|skip|screen-reader|sr-only|visually-hidden|a11y|offscreen|processing-overlay|loading-overlay|preloader|page-loader|spinner|loader-wrapper", re.I)
HASH = re.compile(r"-[0-9a-f]{32,}(?=\.)")
LAZY_ATTRS = ("data-src", "data-lazy-src", "data-original", "data-lazy", "data-hi-res-src")
PLACEHOLDER = re.compile(r"(?:blank|spacer|placeholder|pixel|transparent)[^/]*\.(?:gif|png)$", re.I)
DISPLAY = re.compile(r"(?:^|;)\s*display\s*:\s*([a-z\-]+)", re.I)
RESPONSIVE_SHOW = re.compile(r"(?:^|[:\-])(?:sm|md|lg|xl|2xl|xxl)[:\-](?:block|flex|inline|inline-block|inline-flex|grid|table|show|visible)", re.I)
INLINE_BG = re.compile(r"background(?:-image)?\s*:[^;]*?url\(\s*['\"]?([^'\")]+)", re.I)

def wb(ts, url, flag):  # flag: id_ (raw html/css) or im_ (binary)
    return f"https://web.archive.org/web/{ts}{flag}/{url}"

def get(u, binary=False):
    time.sleep(1.5)  # be polite to Wayback
    for attempt in range(4):
        try: r = requests.get(u, timeout=60); break
        except requests.ConnectionError:
            if attempt == 3: raise
            time.sleep(15 * 2 ** attempt)  # 15s, 30s, 60s
    r.raise_for_status()
    return r.content if binary else r.text

def local_name(url):
    n = HASH.sub("", pathlib.PurePosixPath(urllib.parse.urlparse(url).path).name)
    return n or "image"

def media_applies(cond, width=1440):
    """Does an @media condition hold for a 1440px desktop screen? Unknown features (pixel ratio, orientation, prefers-*) count as not applying."""
    def one(q):
        q = q.strip().lower()
        if not q or "print" in q.split("(")[0] or q.startswith("not "): return False
        feats = re.findall(r"\(\s*([a-z\-]+)\s*(?::\s*([\d.]+)\s*(px|em|rem)?)?\s*\)", q)
        for name, val, unit in feats:
            v = float(val) * (16 if unit in ("em", "rem") else 1) if val else None
            if name == "min-width" and v is not None: ok = width >= v
            elif name == "max-width" and v is not None: ok = width <= v
            elif name in ("color", "hover", "any-hover"): ok = True
            else: ok = False
            if not ok: return False
        return True
    return any(one(q) for q in cond.split(","))

def applicable_rules(css, width=1440):
    """(selector text, declaration body, media/None) for rules that apply at desktop width; recurses into @media/@supports, skips @font-face etc."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S); i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0: break
        head = css[i:j].strip(); depth, k = 1, j + 1
        while k < n and depth: depth += (css[k] == "{") - (css[k] == "}"); k += 1
        body = css[j + 1:k - 1]
        if head.startswith("@media"):
            if media_applies(head[6:], width): yield from applicable_rules(body, width)
        elif head.startswith("@supports"): yield from applicable_rules(body, width)
        elif head and not head.startswith("@"): yield head, body, None
        i = k

def best_srcset(v):
    items = []
    for part in v.split(","):
        bits = part.strip().split()
        if not bits: continue
        m = re.match(r"([\d.]+)[wx]", bits[1]) if len(bits) > 1 else None
        items.append((float(m.group(1)) if m else 0, bits[0]))
    return max(items)[1] if items else None

def pick_src(node):
    """Real image URL for an <img>, or None."""
    for a in LAZY_ATTRS:
        v = (node.get(a) or "").split()
        if v and not v[0].startswith("data:"): return v[0]
    s = node.get("src") or ""
    if s and not s.startswith("data:") and not PLACEHOLDER.search(s): return s
    for a in ("data-srcset", "srcset"):
        if node.get(a):
            b = best_srcset(node[a])
            if b and not b.startswith("data:"): return b
    return None

class Skeleton:
    def __init__(self, url, ts, out, fetch=True):
        self.url, self.ts, self.out, self.fetch = url, ts, pathlib.Path(out), fetch  # fetch=False: text only, no downloads
        if fetch:
            (self.out / "images").mkdir(parents=True, exist_ok=True)
            (self.out / "original").mkdir(exist_ok=True)
        self.manifest = {"included": [], "dropped": []}
        self.saved = {}      # abs url -> local path
        self.hidden = {}     # id() of element hidden on load -> why (rule / inline style)
        self.bg = {}         # id() of element -> [local image paths] (CSS / inline-style backgrounds)

    def save_image(self, src, why):
        absu = urllib.parse.urljoin(self.url, src)
        if absu in self.saved: return self.saved[absu]
        name = local_name(absu); path = self.out / "images" / name
        self.saved[absu] = f"images/{name}"
        if not self.fetch: return self.saved[absu]
        try: path.write_bytes(get(wb(self.ts, absu, "im_"), binary=True))
        except Exception as e: self.drop(absu, f"image download failed ({type(e).__name__})"); return self.saved[absu]
        self.manifest["included"].append({"src": absu, "file": name, "why": why})
        return self.saved[absu]

    def drop(self, src, why):
        self.manifest["dropped"].append({"src": src, "why": why})

    def _add_bg(self, el, u, base, why):
        if u.startswith("data:"): self.drop(u[:40], "data: URI (decorative)"); return
        ext = pathlib.PurePosixPath(urllib.parse.urlparse(u).path).suffix.lower()
        if ext not in RASTER: self.drop(u, f"non-raster background ({ext or 'none'})"); return
        if not self.fetch: return
        self.bg.setdefault(id(el), []).append(self.save_image(urllib.parse.urljoin(base, u), why))

    def _hide_ok(self, el):
        return not RESPONSIVE_SHOW.search(" ".join(el.get("class", [])))

    def scan(self, soup):
        """Find elements hidden on load and elements carrying background images (stylesheets, <style> blocks, inline style)."""
        sheets = [(st.get_text(), self.url) for st in soup.find_all("style")]
        if self.fetch:
            for link in soup.select('link[rel~="stylesheet"][href]'):
                cu = urllib.parse.urljoin(self.url, link["href"])
                try: css = get(wb(self.ts, cu, "id_"))
                except Exception as e: self.drop(cu, f"stylesheet fetch failed: {e}"); continue
                (self.out / "original" / local_name(cu)).write_text(css); sheets.append((css, cu))
        disp = {}  # id(el) -> (hidden?, why): the LAST applicable display declaration wins (source order, specificity ignored)
        for css, base in sheets:
            for head, body, _ in applicable_rules(css):
                dv = DISPLAY.findall(body); urls = re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", body) if "background" in body else []
                if not dv and not urls: continue
                for sel in (s.strip() for s in head.split(",")):
                    if ":" in sel: continue  # pseudo-elements/states: decoration
                    try: els = soup.select(sel)[:50]
                    except Exception: continue
                    for el in els:
                        if dv and self._hide_ok(el): disp[id(el)] = (dv[-1].lower() == "none", f"rule '{sel[:60]}'")
                        for u in urls: self._add_bg(el, u, base, "css-background")
                    if urls and not els: [self.drop(u, "CSS background but selector matches no element in the page") for u in urls]
        for el in soup.find_all(style=True):
            st = el["style"]; dv = DISPLAY.findall(st)
            if dv and self._hide_ok(el): disp[id(el)] = (dv[-1].lower() == "none", "inline style")  # inline style wins over stylesheets
            for u in INLINE_BG.findall(st): self._add_bg(el, u, self.url, "inline-style-background")
        self.hidden = {k: why for k, (h, why) in disp.items() if h}

    # ---- html -> markdown (copy, links, images only) ----
    def md(self, node, out):
        if isinstance(node, (Comment, Doctype, ProcessingInstruction, Declaration, CData)): return  # HTML comments/markup are not copy
        if isinstance(node, NavigableString):
            out.append(re.sub(r"\s+", " ", str(node))); return
        if not isinstance(node, Tag) or node.name in SKIP_TAGS or node.has_attr("hidden") or node.get("aria-hidden") == "true": return
        if id(node) in self.hidden: self.drop(f"<{node.name}> {node.get('class') or node.get('id')}", f"hidden on load (display:none via {self.hidden[id(node)]})"); return
        if BOILER.search(" ".join(node.get("class", [])) + " " + (node.get("id") or "") + " " + " ".join(k for k in node.attrs if k.startswith("data-"))):
            self.drop(f"<{node.name}> {node.get('class')}", "boilerplate element (hidden/mobile/modal/cookie/skip-link)"); return
        for p in self.bg.get(id(node), []): out.append(f"\n\n![background image of <{node.name}>]({p})\n\n")
        n = node.name
        if n == "svg":
            title = node.find("title")
            if node.get("role") == "img" and title:
                fn = re.sub(r"\W+", "-", title.get_text().lower()).strip("-") + ".svg"
                if self.fetch: (self.out / "images" / fn).write_text(str(node))
                self.manifest["included"].append({"src": "inline-svg", "file": fn, "why": "inline svg role=img"})
                out.append(f"![{title.get_text()}](images/{fn})")
            else: self.drop("inline-svg", "inline svg without role=img (decorative)")
            return
        if n == "img":
            src = pick_src(node)
            if (node.get("width"), node.get("height")) in {("1", "1")} or not src: self.drop(node.get("src") or node.get("data-src"), "tracking pixel / placeholder / no usable source"); return
            out.append(f"![{node.get('alt','')}]({self.save_image(src, 'img')})"); return
        if n == "picture":
            im = node.find("img")
            for s in node.find_all("source"):
                if not s.get("srcset"): continue
                if "max-width" in (s.get("media") or ""): self.drop(s["srcset"].split()[0], "mobile-only <source> (mobile is out of scope)"); continue
                self.save_image(best_srcset(s["srcset"]) or s["srcset"].split()[0], "picture source")
            if im: self.md(im, out)
            return
        pre, post = {"h1": ("\n\n# ", "\n\n"), "h2": ("\n\n## ", "\n\n"), "h3": ("\n\n### ", "\n\n"),
                     "h4": ("\n\n#### ", "\n\n"), "p": ("\n\n", "\n\n"), "blockquote": ("\n\n> ", "\n\n"),
                     "li": ("\n- ", ""), "br": ("  \n", ""), "hr": ("\n\n---\n\n", ""),
                     "strong": ("**", "**"), "b": ("**", "**"), "em": ("*", "*"), "i": ("*", "*"),
                     "cite": ("\n> — ", ""), "section": ("\n\n", ""), "footer": ("\n\n---\n\n", "")}.get(n, ("", ""))
        if n in {"div", "header", "nav", "main", "ul", "ol", "figure"}: pre = "\n"
        if n == "a" and node.get("href"):
            out.append("["); [self.md(c, out) for c in node.children]; out.append(f"]({node['href']})"); return
        out.append(pre); [self.md(c, out) for c in node.children]; out.append(post)

    def to_markdown(self, html):
        """Copy markdown (plus image downloads when fetch=True; text-only analysis when fetch=False)."""
        soup = BeautifulSoup(html, "html.parser")
        self.hidden, self.bg = {}, {}
        self.scan(soup)
        out = []; self.md(soup.body, out)
        return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", "".join(out))).strip() + "\n"

    def run(self):
        html = get(wb(self.ts, self.url, "id_"))
        (self.out / "original" / "snapshot.html").write_text(html)
        (self.out / "copy.auto.md").write_text(self.to_markdown(html))
        (self.out / "images_manifest.json").write_text(json.dumps(self.manifest, indent=1))
        print(f"included {len(self.manifest['included'])}, dropped {len(self.manifest['dropped'])}")

if __name__ == "__main__":
    Skeleton(sys.argv[1], sys.argv[2], sys.argv[3]).run()
