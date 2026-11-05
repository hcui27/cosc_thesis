"""Feature distribution plot from the master list: how many of the vibe-coded pages show each attribute.
usage: python pipeline/3_annotate/plot_distribution.py [--master data/master/master_list.json] [--out data/master/feature_distribution.png] [--top 30]
Prevalence of an attribute = number of sites whose GENERATED page has any value of it (kept, changed or added). Left: histogram over all attributes. Right: the most common attributes, family in grey.
Also writes <out>.csv (family, attribute, sites on the generated page, sites in the diff at all)."""
import sys, json, csv, pathlib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
ML = json.load(open(g("--master", "data/master/master_list.json"))); OUT = pathlib.Path(g("--out", "data/master/feature_distribution.png")); TOP = int(g("--top", 30))
rows = [(fam, a["attribute"], len({s for v in a["values"] for s in v["generated_sites"]}), a["n_sites"]) for fam, F in ML["families"].items() for a in F["attributes"]]
N = ML["n_sites"]; rows.sort(key=lambda r: (-r[2], r[0], r[1]))
with open(OUT.with_suffix(".csv"), "w", newline="") as f: w = csv.writer(f); w.writerow(["family", "attribute", "n_sites_generated", "n_sites_in_diff"]); w.writerows(rows)
INK, MUTED, GRID, BAR, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6", "#fcfcfb"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "text.color": INK, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": INK})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 9), gridspec_kw={"width_ratios": [1, 1.5]}, facecolor=SURF)
bins = [(1, 1), (2, 3), (4, 7), (8, 14), (15, 21), (22, N)]; lab = [f"{a}" if a == b else f"{a}-{b}" for a, b in bins]
cnt = [sum(a <= r[2] <= b for r in rows) for a, b in bins]
ax1.bar(range(len(bins)), cnt, color=BAR, width=0.7); ax1.set_xticks(range(len(bins))); ax1.set_xticklabels(lab)
for i, c in enumerate(cnt): ax1.text(i, c + 1, str(c), ha="center", color=INK)
ax1.set_ylim(0, max(cnt) * 1.12); ax1.set_xlabel(f"number of the {N} vibe-coded sites that show the attribute"); ax1.set_ylabel("number of attributes"); ax1.set_title(f"How widely shared are the {len(rows)} attributes?", loc="left", fontsize=12, fontweight="bold")
top = rows[:TOP][::-1]; y = range(len(top))
ax2.barh(list(y), [r[2] for r in top], color=BAR, height=0.65); ax2.set_yticks(list(y)); ax2.set_yticklabels([r[1][:38] for r in top], fontsize=9)
for i, r in enumerate(top):
    ax2.text(r[2] + 0.3, i, str(r[2]), va="center", color=INK, fontsize=9); ax2.text(-0.5, i, "", va="center")
    ax2.text(N + 2.2, i, r[0], va="center", color=MUTED, fontsize=8.5)
ax2.set_xlim(0, N); ax2.set_xlabel(f"sites (of {N}) whose vibe-coded page shows it"); ax2.set_title(f"The {TOP} most widespread attributes", loc="left", fontsize=12, fontweight="bold")
for ax in (ax1, ax2):
    ax.set_facecolor(SURF); [ax.spines[s].set_visible(False) for s in ("top", "right", "left")]; ax.spines["bottom"].set_color(GRID); ax.tick_params(length=0)
    ax.grid(axis="x" if ax is ax2 else "y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
fig.subplots_adjust(left=0.05, right=0.88, wspace=0.6, top=0.92, bottom=0.08); fig.savefig(OUT, dpi=160, facecolor=SURF)
print(f"{len(rows)} attributes; {sum(r[2] == N for r in rows)} on all {N}; {sum(r[2] >= 2 for r in rows)} on >=2; wrote {OUT}")
