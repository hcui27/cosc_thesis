"""Wayback checks for the drawn sites (run AFTER draw_sites.py). Builds each site's prompt inputs and tests they are usable;
a failing site is replaced by the next unused candidate from the SAME purpose (data/frames/replacements.csv, seeded order).
usage: python pipeline/2_build_sites/check_selected.py [draw.csv replacements.csv]  (defaults: the purpose draw)
Usable = skeleton built, 150-3000 words of copy, 2-40 referenced images that downloaded (non-empty). Writes data/sites_check.csv and rewrites data/sites.csv
with the final list (the original draw is kept in data/frames/sites_draw_seed0.csv). Sequential and slow on purpose.
"""
import sys, os, csv, re, pathlib, collections, shutil
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
import requests
from skeletonize import Skeleton

MIN_WORDS, MAX_WORDS, MIN_IMAGES, MAX_IMAGES = 150, 3000, 2, 40  # usable prompt inputs: not a stub page, not an index/blog with hundreds of items

def check(row):
    root = pathlib.Path("data") / row["site_id"]; res = dict(row, ok=False, reason="", copy_words=0, images=0, dropped=0)
    try:
        if root.exists(): shutil.rmtree(root)
        sk = Skeleton(row["url"], row["timestamp"], root); sk.run()
        md = (root / "copy.auto.md").read_text(); words = len(re.sub(r"!\[[^\]]*\]\([^)]*\)|\[([^\]]*)\]\([^)]*\)", r"\1", md).split())
        refs = {m for m in re.findall(r"!\[[^\]]*\]\((images/[^)]+)\)", md) if (root / m).exists() and (root / m).stat().st_size > 0}  # images the copy actually uses
        res.update(copy_words=words, images=len(refs), dropped=len(sk.manifest["dropped"]))
        res["reason"] = ("too little copy" if words < MIN_WORDS else "too much copy" if words > MAX_WORDS else
                         "fewer than 2 images" if len(refs) < MIN_IMAGES else "too many images" if len(refs) > MAX_IMAGES else "")
        res["ok"] = not res["reason"]
    except requests.ConnectionError: raise  # Wayback unreachable: not the site's fault, caller stops the run
    except Exception as e: res["reason"] = f"error: {type(e).__name__}"
    return res

DRAW = sys.argv[1] if len(sys.argv) > 1 else "data/frames/sites_draw_seed0.csv"
REPL = sys.argv[2] if len(sys.argv) > 2 else "data/frames/replacements.csv"
draw = list(csv.DictReader(open(DRAW)))
queue = collections.defaultdict(list)
for r in csv.DictReader(open(REPL)): queue[r["category"]].append(r)
prev = {r["site_id"]: r for r in csv.DictReader(open("data/sites_check.csv"))} if os.path.exists("data/sites_check.csv") else {}
final, log = [], []
def save():
    with open("data/sites_check.csv", "w", newline="") as f: w = csv.DictWriter(f, list(log[0])); w.writeheader(); w.writerows(log)
for row in draw:
    cur = row
    while True:
        if cur["site_id"] in prev:  # resume: reuse earlier definitive result
            r = prev[cur["site_id"]]; r["ok"] = r["ok"] in (True, "True")
        else:
            try: r = check(cur)
            except requests.ConnectionError:
                print("Wayback unreachable (connection errors persisted); stopping. Re-run later to resume.", flush=True)
                if log: save()
                sys.exit(2)
        log.append(r); save(); print(f"{r['category']:20s} {r['site_id']:28s} ok={r['ok']} words={r['copy_words']} imgs={r['images']} {r['reason']}", flush=True)
        if r["ok"]: final.append(cur); break
        if not queue[row["category"]]: print(f"  no replacement left for {row['category']}", flush=True); break
        cur = queue[row["category"]].pop(0); print(f"  -> replacing with {cur['site_id']}", flush=True)
fields = list(log[0])
with open("data/sites_check.csv", "w", newline="") as f: w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(log)
with open("data/sites.csv", "w", newline="") as f: w = csv.DictWriter(f, list(final[0])); w.writeheader(); w.writerows(final)
print(f"{len(final)} usable sites after checks ({len(log)} checked)")
