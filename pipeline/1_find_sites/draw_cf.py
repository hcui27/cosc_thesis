"""Draw sites by Cloudflare top-level category from the CURRENT labelled pool (no bucket filling).
usage: python pipeline/1_find_sites/draw_cf.py [--per-category 2] [--seed 0] [--min-confidence 0.6] [--any-language] [--target 30]
--target N tops the draw up to N sites using only the current labelled pool (no new sourcing): first the single qualifying site of each partial category,
then extra sites (next in seeded order) from the categories with the most qualifying sites. Each row records why it was included (base / partial_single / extra).
English-only is the default: the labeler must say language == 'en' AND the extracted copy must be >= 90% English by Lingua
(word-weighted, data/frames/english_scores_v2.json; pages with < 5 usable sentences rely on the labeler's language call).
A site QUALIFIES if (English-only unless --any-language): its category is not excluded (Adult Themes, Child Abuse, Gambling, Questionable Content, Security Risks, Violence),
label confidence >= --min-confidence, and it passed the non-language viability checks in sample_unpopular.csv (HTTP 200 snapshot <= 2021, at the
site root, >=150 words static copy, >=1 heading, >=2 <img>, HTML <= 700KB). 
A category is FULFILLED when it has >= per-category qualifying sites; only fulfilled categories are drawn from (seeded random).
Writes: data/frames/sites_draw_cf.csv (selected), data/frames/replacements_cf.csv (other qualifying, ordered), data/frames/qualifying_sites.md (full report).
"""
import sys, csv, json, random, collections
from label_categories import CF, EXCLUDED
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
PER, SEED, MINC, TARGET = int(g("--per-category", 2)), int(g("--seed", 0)), float(g("--min-confidence", 0.6)), int(g("--target", 0))
S = {r["domain"]: r for r in csv.DictReader(open("data/frames/sample_unpopular.csv"))}
LANGFAIL = ("non-English lang attr", "copy not English", "too few copy sentences")
ANY = "--any-language" in sys.argv
ESC = json.load(open("data/frames/english_scores_v2.json"))  # domain -> [share, n_sentences]

def english(r):
    if r["language"] != "en": return False
    share, n = ESC.get(r["domain"], [0, 0])
    return n < 5 or share >= 0.90

def qualifies(r):
    s = S[r["domain"]]
    if not ANY and not english(r): return False
    if s["ok"] == "True": return True
    if not s["reason"].startswith(LANGFAIL): return False          # failed a non-language check (redirect, HTTP error, too late, ...)
    return int(s["words"]) >= 150 and int(s["headings"]) >= 1 and int(s["imgs"]) >= 2 and int(s["bytes"]) <= 700_000

labels = list(csv.DictReader(open("data/frames/cf_labels.csv")))
cats = [c for c in CF if c not in EXCLUDED]
pool = collections.defaultdict(list)
for r in labels:
    if r["category"] in cats and float(r["confidence"]) >= MINC and qualifies(r): pool[r["category"]].append(r)
rnd = random.Random(SEED); sel, rep, status = [], [], {}
for c in cats:
    items = pool[c][:]; rnd.shuffle(items); n = len(items)
    status[c] = "fulfilled" if n >= PER else ("partial" if n else "missing")
    for i, r in enumerate(items):
        row = {"category": c, "subcategory": r["subcategory"], "site_id": r["domain"].replace(".", "_").replace("-", "_"), "url": f"http://{r['domain']}/",
               "timestamp": S[r["domain"]]["timestamp"], "rank": S[r["domain"]]["rank"], "language": r["language"], "confidence": r["confidence"], "title": r["title"][:70], "order": i + 1, "reason": "base"}
        (sel if status[c] == "fulfilled" and i < PER else rep).append(row)
if TARGET:
    left = collections.defaultdict(list)
    for r in rep: left[r["category"]].append(r)
    for c in cats:                                   # 1) partial categories contribute their single qualifying site
        if status[c] == "partial":
            for r in left.pop(c, []): r["reason"] = "partial_single"; sel.append(r)
    order = sorted((c for c in cats if status[c] == "fulfilled"), key=lambda c: -len(pool[c]))
    while len(sel) < TARGET and any(left[c] for c in order):   # 2) extras from the biggest categories, one per pass
        for c in order:
            if len(sel) < TARGET and left[c]: r = left[c].pop(0); r["reason"] = "extra"; sel.append(r)
    rep = [r for c in left for r in left[c]]
for fn, rows in (("data/frames/sites_draw_cf.csv", sel), ("data/frames/replacements_cf.csv", rep)):
    with open(fn, "w", newline="") as f: w = csv.DictWriter(f, list(sel[0])); w.writeheader(); w.writerows(rows)
L = [f"# Qualifying sites by Cloudflare category (seed {SEED}, {PER} per category)\n",
     f"Qualifies = allowed category, label confidence >= {MINC}, English copy" + ("" if not ANY else " (not required)") + ", passes the non-language Wayback viability checks. ★ = drawn.\n",
     f"**Selected: {len(sel)} sites. Fulfilled: {sum(v == 'fulfilled' for v in status.values())} of {len(cats)} categories.**\n",
     "## Status by category\n", "| Category | Qualifying | Status |", "|---|---|---|"] + [f"| {c} | {len(pool[c])} | {status[c]} |" for c in cats]
L += ["", "## Not fulfilled (fewer than %d qualifying sites)\n" % PER] + [f"- **{c}**: {len(pool[c])} qualifying" + (f" ({', '.join(r['domain'] for r in pool[c])} — not drawn)" if pool[c] else "") for c in cats if status[c] != "fulfilled"]
L += ["", "## Qualifying sites per category\n"]
selset = {(r["category"], r["url"]) for r in sel}
for c in cats:
    L.append(f"### {c} — {status[c]} ({len(pool[c])} qualifying)\n")
    for r in sorted(pool[c], key=lambda r: r["domain"]):
        star = "★" if (c, f"http://{r['domain']}/") in selset else " "
        L.append(f"- {star} {r['domain']} (rank {S[r['domain']]['rank']}, {r['language']}, conf {float(r['confidence']):.2f}) — {r['subcategory']} — {r['title'][:60]}")
    L.append("")
open("data/frames/qualifying_sites.md", "w").write("\n".join(L))
print(f"{len(sel)} selected;", {s: [c for c in cats if status[c] == s] for s in ("partial", "missing")})
print("language of selected:", dict(collections.Counter(r["language"] for r in sel)))
