"""Offline review of the English threshold using the HTML saved by build_frame.py.
usage: python pipeline/1_find_sites/review_english.py [--html-dir data/frames/html] [--out data/frames/english_review.md] [--threshold 0.90] [--band 0.6,0.98]
Writes a markdown sheet: share histogram, then every page whose English share is inside the band (the ones where the threshold matters),
sorted by share, with the sentences Lingua judged NON-English so you can see why. Mark each verdict keep or exclude (mixed-language pages are excluded) and re-tune the threshold.
"""
import sys, os, pathlib, collections
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from skeletonize import Skeleton
import english
from lingua import Language

g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
hd, out, thr = pathlib.Path(g("--html-dir", "data/frames/html")), g("--out", "data/frames/english_review.md"), float(g("--threshold", 0.90))
lo, hi = map(float, g("--band", "0.6,0.98").split(","))
det = english._detector(); rows = []
for f in sorted(hd.glob("*.html")):
    md = Skeleton(f"http://{f.stem}/", "20210601000000", ".", fetch=False).to_markdown(f.read_text(errors="ignore"))
    share, n = english.english_share(md)
    bad = [(s, det.detect_language_of(s)) for s in english._sentences(md)]
    bad = [(s, l.name.title()) for s, l in bad if l is not None and l != Language.ENGLISH]
    rows.append((f.stem, share, n, bad))
bins = collections.Counter(min(int(r[1] * 10), 9) / 10 for r in rows)
L = [f"# English threshold review (threshold {thr}, {len(rows)} pages)\n", "## Share histogram (word-weighted English share of prompt copy)\n"]
L += [f"- {b:.1f}–{b + .1:.1f}: {bins.get(b, 0)} pages {'#' * bins.get(b, 0)}" for b in [i / 10 for i in range(10)]]
L.append(f"\n- passing at {thr}: {sum(r[1] >= thr and r[2] >= 5 for r in rows)}; failing: {sum(r[1] < thr or r[2] < 5 for r in rows)}\n")
L.append(f"## Pages in the band {lo}–{hi} (decide: should this page count as English?)\n")
for dom, share, n, bad in sorted((r for r in rows if lo <= r[1] <= hi), key=lambda r: r[1]):
    L.append(f"### {dom}: share {share:.2f} over {n} sentences — {'PASS' if share >= thr else 'FAIL'} at {thr}\n- verdict (keep = prompt copy is English; exclude = mixed or other language): \n")
    L += [f"  - [{lang}] {s[:140]}" for s, lang in bad[:8]]; L.append("")
pathlib.Path(out).write_text("\n".join(L)); print(f"{len(rows)} pages -> {out}")
