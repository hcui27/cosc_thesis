"""Number the visible elements of a generated page so a coder can CITE evidence by element id (and the crop is the element's real box).
usage: python pipeline/3_annotate/element_map.py [--sites a,b] [--which generated|original]
Re-renders the page exactly like render.py (1440 px, local http server, scroll for lazy content) and writes <render dir>/evidence/{page.png, elements.json, elements.txt}.
page.png is the screenshot the element boxes belong to (the coder and the gallery must use THIS image, not render/desktop.png, because animations can shift layout between renders).
elements.json: [{id, tag, parent, text, rect:[x,y,w,h] in full-page pixels}]; elements.txt is the compact listing the coder reads.
"""
import sys, json, pathlib, csv
sys.path[:0] = [str(d) for d in pathlib.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ("deprecated", "__pycache__")]
from playwright.sync_api import sync_playwright
import formats
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
MAXEL = 450
JS = r"""(minArea) => {
  const KEEP = new Set(['h1','h2','h3','h4','h5','h6','p','a','button','img','svg','picture','video','li','ul','ol','nav','header','footer','section','article','aside','form','input','select','textarea','label','figure','blockquote','table','details','summary']);
  const vis = e => { const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) return null;
    const r = e.getBoundingClientRect(); const x = r.left + scrollX, y = r.top + scrollY; if (r.width < 14 || r.height < 8 || r.width * r.height < minArea) return null; return [Math.round(x), Math.round(y), Math.round(r.width), Math.round(r.height), s]; };
  const own = e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
  const out = [], idOf = new Map();
  for (const e of document.querySelectorAll('body *')) {
    const t = e.tagName.toLowerCase(); if (['script','style','link','meta','noscript','path','g','br','source','use','defs'].includes(t)) continue;
    if (e.closest('svg') && t !== 'svg') continue;
    const v = vis(e); if (!v) continue; const s = v[4];
    const styled = (s.backgroundColor !== 'rgba(0, 0, 0, 0)' || s.backgroundImage !== 'none' || s.boxShadow !== 'none' || ['Top','Right','Bottom','Left'].some(d => parseFloat(s['border' + d + 'Width']) > 0 && s['border' + d + 'Style'] !== 'none'));
    if (!(KEEP.has(t) || styled || own(e))) continue;
    const kids = [...e.children].filter(c => vis(c));
    if (kids.length === 1 && !own(e) && !['img','svg','a','button'].includes(t)) { const k = vis(kids[0]); if (Math.abs(k[2] - v[2]) < 6 && Math.abs(k[3] - v[3]) < 6 && !styled) continue; }
    let p = e.parentElement; while (p && !idOf.has(p)) p = p.parentElement;
    const id = 'e' + (out.length + 1); idOf.set(e, id);
    let text = (t === 'img' ? ('image ' + ((e.currentSrc || e.src || '').split('/').pop().split('?')[0])) : t === 'svg' ? 'svg graphic' : (e.innerText || '').replace(/\s+/g, ' ').trim()).slice(0, 70);
    out.push({id, tag: t, parent: p ? idOf.get(p) : null, text, rect: [v[0], v[1], v[2], v[3]]});
  }
  return out;
}"""

def run(site, which="generated"):
    root = pathlib.Path(f"data/{site}")
    if which == "generated":
        rd = root / "generated_cli/r1/free"; info = json.load(open(rd / "format.json")); srv = formats._serve(rd / info["root"]); url = f"http://127.0.0.1:{srv.server_address[1]}/"; od = rd / "render" / "evidence"
    else:
        raise SystemExit("original pages need the archived URL; add when originals are coded")
    od.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1440, "height": 900}); pg.goto(url, wait_until="load", timeout=120000)
            try: pg.wait_for_load_state("networkidle", timeout=15000)
            except Exception: pass
            pg.evaluate("async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,150))}window.scrollTo(0,0)}"); pg.wait_for_timeout(800)
            els = []
            for ma in (0, 1500, 4000, 9000):          # raise the minimum area until the listing is a manageable size
                els = pg.evaluate(JS, ma)
                if len(els) <= MAXEL: break
            pg.screenshot(path=str(od / "page.png"), full_page=True); b.close()
    finally: srv.shutdown()
    json.dump(els, open(od / "elements.json", "w"), ensure_ascii=False)
    with open(od / "elements.txt", "w") as f:
        f.write("id | parent | tag | x,y,w,h (page pixels) | text\n")
        for e in els: f.write(f"{e['id']} | {e['parent'] or '-'} | {e['tag']} | {','.join(map(str, e['rect']))} | {e['text']}\n")
    return len(els)

if __name__ == "__main__":
    sites = [s for s in g("--sites", "").split(",") if s] or [r["site_id"] for r in csv.DictReader(open("data/analysis/sites_table.csv"))]
    for s in sites:
        try: print(s, run(s), "elements", flush=True)
        except Exception as e: print(s, "FAILED", type(e).__name__, str(e)[:150], flush=True)
