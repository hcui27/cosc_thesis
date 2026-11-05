"""Render a URL (or local file) at desktop width: full-page screenshot + programmatic page facts.
usage: python render.py <url-or-path> <out_dir> [--wayback]
Writes desktop.png, dom.json (facts the judge receives as ground truth) and text.txt (visible text).
"""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

VIEWPORT = (1440, 900)
HIDE_WAYBACK = "#wm-ipp-base, #wm-ipp, #donato {display:none !important}"

FACTS_JS = r"""() => {
  const cs = e => getComputedStyle(e), all = [...document.querySelectorAll('body, body *')];
  const count = (sel) => document.querySelectorAll(sel).length;
  const top = (m, n) => Object.entries(m).sort((a,b)=>b[1]-a[1]).slice(0,n);
  const tags = {}; document.querySelectorAll('*').forEach(e => { const t=e.tagName.toLowerCase(); tags[t]=(tags[t]||0)+1; });
  const fam = {}, bg = {}, fg = {}, radius = {bucket_0:0,bucket_1_7:0,bucket_8_15:0,bucket_16_plus:0,bucket_pill:0};
  let shadows=0, gradients=0, blur=0, transitions=0, animations=0, grid=0, flex=0, transforms=0;
  for (const e of all) {
    const s = cs(e); if (s.display === 'none') continue;
    const f = s.fontFamily.split(',')[0].replace(/["']/g,'').trim(); fam[f]=(fam[f]||0)+1;
    if (s.backgroundColor !== 'rgba(0, 0, 0, 0)') bg[s.backgroundColor]=(bg[s.backgroundColor]||0)+1;
    fg[s.color]=(fg[s.color]||0)+1;
    const r = parseFloat(s.borderTopLeftRadius)||0, pill = s.borderTopLeftRadius.includes('%') || r>=999;
    radius[pill?'bucket_pill': r===0?'bucket_0': r<8?'bucket_1_7': r<16?'bucket_8_15':'bucket_16_plus']++;
    if (s.boxShadow !== 'none') shadows++;
    if (s.backgroundImage.includes('gradient')) gradients++;
    if ((s.backdropFilter||'none') !== 'none') blur++;
    if (s.transitionDuration && s.transitionDuration.split(',').some(x=>parseFloat(x)>0)) transitions++;
    if (s.animationName !== 'none') animations++;
    if (s.transform !== 'none') transforms++;
    if (s.display.includes('grid')) grid++; if (s.display.includes('flex')) flex++;
  }
  const classes = all.flatMap(e => [...e.classList]);
  const tw = /^(?:(?:sm|md|lg|xl|2xl|hover|focus|dark):)*(?:-?(?:p|m)[xytblrse]?-|flex|grid|text-|bg-|rounded|w-|h-|gap-|items-|justify-|font-|shadow|border|space-|max-w|min-h|min-w|leading-|tracking-|transition|duration)/;
  const body = document.body, h1 = document.querySelector('h1'), h2 = document.querySelector('h2');
  const btnEl = document.querySelector('a.button--primary, a.btn-primary, .cta a, a.button, button, a[class*="btn"]');
  const rect = e => { const r=e.getBoundingClientRect(); return {x:Math.round(r.left+scrollX), y:Math.round(r.top+scrollY), w:Math.round(r.width), h:Math.round(r.height)}; };
  const imgs = [...document.images].map(i => ({file:(i.currentSrc||i.src).split('/').pop().split('?')[0], alt:i.alt, natural:[i.naturalWidth,i.naturalHeight], rect:rect(i)}));
  const overlaps = [];
  for (let a=0;a<imgs.length;a++) for (let b=a+1;b<imgs.length;b++) {
    const A=imgs[a].rect, B=imgs[b].rect, w=Math.min(A.x+A.w,B.x+B.w)-Math.max(A.x,B.x), h=Math.min(A.y+A.h,B.y+B.h)-Math.max(A.y,B.y);
    if (w>0 && h>0) overlaps.push({a:imgs[a].file, b:imgs[b].file, overlap_px_area:w*h});
  }
  const text = body.innerText;
  const meta = [...document.querySelectorAll('meta')].map(m => m.getAttribute('name')||m.getAttribute('property')||m.getAttribute('charset')&&'charset'||m.getAttribute('http-equiv')).filter(Boolean);
  return {
    title: document.title, lang: document.documentElement.lang, meta_names: meta, jsonld_blocks: count('script[type="application/ld+json"]'),
    tag_counts: tags,
    semantic: Object.fromEntries(['header','nav','main','section','article','aside','footer','figure','figcaption','blockquote','cite'].map(t=>[t,count(t)])),
    h1_count: count('h1'), heading_outline: [...document.querySelectorAll('h1,h2,h3,h4')].map(h=>({level:+h.tagName[1], text:h.innerText.trim().slice(0,80)})),
    counts: {anchors:count('a'), buttons:count('button'), images:count('img'), svgs:count('svg'), scripts:count('script'), stylesheets:count('link[rel~="stylesheet"]'), inline_style_attrs:count('[style]'), aria_attrs:all.reduce((n,e)=>n+[...e.attributes].filter(a=>a.name.startsWith('aria-')).length,0), alt_missing:[...document.images].filter(i=>!i.hasAttribute('alt')).length},
    fonts_by_element_count: top(fam, 6), body_font_size: cs(body).fontSize, body_line_height: cs(body).lineHeight,
    h1: h1 && {text:h1.innerText.trim(), font_size:cs(h1).fontSize, font_weight:cs(h1).fontWeight, font_family:cs(h1).fontFamily, color:cs(h1).color, text_align:cs(h1).textAlign},
    h2: h2 && {font_size:cs(h2).fontSize, font_weight:cs(h2).fontWeight},
    colors: {body_bg: cs(body).backgroundColor, body_color: cs(body).color, top_backgrounds: top(bg, 8), top_text_colors: top(fg, 5)},
    primary_button: btnEl && {text:btnEl.innerText.trim().slice(0,40), bg:cs(btnEl).backgroundColor, color:cs(btnEl).color, radius:cs(btnEl).borderTopLeftRadius, padding:cs(btnEl).padding},
    effects: {border_radius_buckets: radius, box_shadows: shadows, gradient_backgrounds: gradients, backdrop_blur: blur, transitions, animations, transforms},
    layout: {display_grid: grid, display_flex: flex, page_height: document.documentElement.scrollHeight, page_width: document.documentElement.scrollWidth},
    classes: {total: classes.length, unique: new Set(classes).size, tailwind_like_fraction: classes.length ? +(classes.filter(c=>tw.test(c)).length/classes.length).toFixed(3) : 0},
    text_stats: {words: text.split(/\s+/).filter(Boolean).length, emoji: (text.match(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B50}\u{2B55}\u{231A}-\u{23FF}]/gu)||[]).length, em_dashes: (text.match(/—/g)||[]).length, exclamations: (text.match(/!/g)||[]).length},
    images: imgs, image_overlaps: overlaps
  };
}"""

def render(target, out, wayback=False):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    url = target if "://" in target else pathlib.Path(target).resolve().as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": VIEWPORT[0], "height": VIEWPORT[1]})
        pg.goto(url, wait_until="load", timeout=120000)
        try: pg.wait_for_load_state("networkidle", timeout=15000)   # archived pages often never go fully idle; don't wait forever
        except Exception: pass
        if wayback: pg.add_style_tag(content=HIDE_WAYBACK)
        pg.evaluate("async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,150))}window.scrollTo(0,0)}")
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(out / "desktop.png"), full_page=True)
        (out / "dom.json").write_text(json.dumps(pg.evaluate(FACTS_JS), indent=1, ensure_ascii=False))
        (out / "text.txt").write_text(pg.evaluate("document.body.innerText"))
        b.close()

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], "--wayback" in sys.argv)
