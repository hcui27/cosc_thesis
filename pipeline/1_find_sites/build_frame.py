"""Draw a seeded random sample from a Tranco list (rank floor dropped 2026-11-04: default --min-rank 1; the 30 sites drawn so far used --min-rank 100001. Pass --min-rank 100001 to reproduce that draw) and check each domain's Wayback homepage.
usage: python pipeline/1_find_sites/build_frame.py [--n 300] [--seed 0] [--min-rank 1] [--target 20210601] [--out data/frames/sample_unpopular.csv]
Resumable: domains already in the output CSV are skipped. Fetches one page at a time (Wayback rate-limits parallel requests).
A row is 'viable' when the snapshot is from <= 2021, HTTP 200, still at the site root, the html lang is not another language,
the extracted prompt copy is English (Lingua, word-weighted share >= --min-english, default 0.90, over >=5 sentences),
with >=150 words of static copy, >=1 heading, >=2 <img>, HTML <= 700KB. Fetched HTML is kept in data/frames/html/ so filters can be re-run offline.
"""
import sys, re, csv, os, random, time, urllib.parse, pathlib
import requests
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from skeletonize import Skeleton
from english import english_share

g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
N, SEED, MINRANK, TARGET, OUT = int(g("--n", 300)), int(g("--seed", 0)), int(g("--min-rank", 1)), g("--target", "20210601"), g("--out", "data/frames/sample_unpopular.csv")
MINENG = float(g("--min-english", 0.90)); HTML_DIR = pathlib.Path("data/frames/html")
FIELDS = ["rank", "domain", "ok", "reason", "timestamp", "final_url", "lang_attr", "english_share", "copy_sentences", "words", "imgs", "headings", "bytes"]

def fetch(url):
    for attempt in range(4):
        try: return requests.get(f"https://web.archive.org/web/{TARGET}id_/{url}", timeout=60, allow_redirects=True)
        except requests.RequestException:
            if attempt == 3: raise
            time.sleep(5 * (attempt + 1))

def check(rank, dom):
    r = dict(rank=rank, domain=dom, ok=False, reason="", timestamp="", final_url="", lang_attr="", english_share=0, copy_sentences=0, words=0, imgs=0, headings=0, bytes=0)
    try:
        resp = fetch(f"http://{dom}/")
        if resp.status_code == 404: resp = fetch(f"http://www.{dom}/")
        m = re.search(r"/web/(\d{14})id_/(.+)$", resp.url); ts, final = (m.group(1), m.group(2)) if m else ("", "")
        h = resp.text if resp.status_code == 200 else ""
        body = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", "", h); words = re.sub(r"<[^>]+>", " ", body).lower().split()
        lang = (re.search(r"<html[^>]*\blang=[\"']?([a-zA-Z-]+)", h) or [None, ""])[1]
        if h: HTML_DIR.mkdir(parents=True, exist_ok=True); (HTML_DIR / f"{dom}.html").write_text(h)
        share, nsent = (english_share(Skeleton(f"http://{dom}/", ts, ".", fetch=False).to_markdown(h)) if h else (0, 0))
        r.update(timestamp=ts, final_url=final[:80], lang_attr=lang, english_share=round(share, 3), copy_sentences=nsent, words=len(words),
                 imgs=len(re.findall(r"<img\b", h)), headings=len(re.findall(r"<h[1-3]\b", h)), bytes=len(resp.content))
        fp = urllib.parse.urlparse(final)
        base = lambda n: n.lower().removeprefix("www.")
        if resp.status_code != 200: r["reason"] = f"HTTP {resp.status_code}"
        elif not ts or ts > "20211231235959": r["reason"] = f"snapshot too late ({ts})"
        elif fp.path.strip("/") != "" or base(fp.netloc) != base(dom): r["reason"] = "redirected away from root/domain"
        elif lang and not lang.lower().startswith("en"): r["reason"] = f"non-English lang attr ({lang})"
        elif nsent < 5: r["reason"] = "too few copy sentences to identify language"
        elif share < MINENG: r["reason"] = f"copy not English (share {share:.2f})"
        elif r["words"] < 150: r["reason"] = "too little static copy"
        elif r["headings"] < 1: r["reason"] = "no headings"
        elif r["imgs"] < 2: r["reason"] = "fewer than 2 img tags"
        elif r["bytes"] > 700_000: r["reason"] = "large HTML"
        else: r["ok"] = True
    except Exception as e: r["reason"] = f"fetch error: {type(e).__name__}"
    return r

if __name__ == "__main__":
    doms = [(i + 1, l.strip().split(",", 1)[1]) for i, l in enumerate(open("data/frames/tranco_2021/tranco_2021-06-01.csv"))]
    pool = [x for x in doms if x[0] >= MINRANK]; random.Random(SEED).shuffle(pool); pool = pool[:N]
    out = pathlib.Path(OUT); out.parent.mkdir(parents=True, exist_ok=True)
    done = {r["domain"] for r in csv.DictReader(open(out))} if out.exists() else set()
    new = not out.exists()
    with open(out, "a", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        if new: w.writeheader()
        for k, (rank, dom) in enumerate(pool, 1):
            if dom in done: continue
            r = check(rank, dom); w.writerow(r); f.flush(); time.sleep(3)
            print(f"{k}/{len(pool)} {dom} ok={r['ok']} {r['reason']}", flush=True)
