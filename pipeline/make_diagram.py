"""Draw the three-pipeline overview figure -> pipeline_diagram.png (project root). usage: python pipeline/make_diagram.py"""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
INK, MUT, LINE, SURF = "#0b0b0b", "#52514e", "#c9c8c2", "#fcfcfb"
C = {"data": ("#eef2f8", "#2a78d6"), "llm": ("#fdf0e8", "#eb6834"), "code": ("#eef7f2", "#1baf7a"), "new": ("#fff6dc", "#c98500")}
fig, ax = plt.subplots(figsize=(17, 11.6), facecolor=SURF); ax.set_xlim(0, 170); ax.set_ylim(0, 116); ax.axis("off")
def box(x, y, w, h, title, sub="", kind="code", bold=True):
    f, e = C[kind]; ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2", fc=f, ec=e, lw=1.6))
    ax.text(x + w / 2, y + h - 2.4, title, ha="center", va="top", fontsize=9.6, fontweight="bold" if bold else "normal", color=INK)
    if sub: ax.text(x + w / 2, y + h - 6.6, sub, ha="center", va="top", fontsize=7.6, color=MUT, linespacing=1.3)
def arrow(a, b, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13, lw=1.4, color=MUT, connectionstyle=f"arc3,rad={rad}", linestyle=ls))
def lane(y, h, label, sub):
    ax.add_patch(FancyBboxPatch((1, y), 168, h, boxstyle="round,pad=0.2,rounding_size=1.5", fc="none", ec=LINE, lw=1.2))
    ax.text(3, y + h - 2.2, label, fontsize=12, fontweight="bold", va="top", color=INK); ax.text(3, y + h - 6.3, sub, fontsize=8.4, va="top", color=MUT)
def lane(y, h, label, sub):
    ax.add_patch(FancyBboxPatch((1, y), 168, h, boxstyle="round,pad=0.2,rounding_size=1.5", fc="none", ec=LINE, lw=1.2))
    ax.text(3, y + h - 2.4, label, fontsize=12, fontweight="bold", va="top", color=INK); ax.text(70, y + h - 3.1, sub, fontsize=8.6, va="top", color=MUT)
def hand(x, y0, y1, text):
    arrow((x, y0), (x, y1)); ax.text(x + 2, (y0 + y1) / 2, text, fontsize=8.2, va="center", color=MUT, style="italic")
# Lane 1
lane(88, 26, "Pipeline 1: find the websites", "unchanged; the 30 sites were drawn with the old rank floor")
xs = [4, 32, 60, 88, 116, 144]; w = 24
T = [("Tranco 2021 list", "random domains; rank\nfloor dropped 2026-11-04", "data"), ("Wayback homepage", "snapshot <= 2021,\nrendered text", "code"), ("English filter", "labeller says en AND\nLingua >= 0.90", "code"),
     ("LLM category", "Cloudflare top-level,\n20 categories used", "llm"), ("Draw", "2 per category, label\nconfidence >= 0.6", "code"), ("30 sites", "28 usable after\nthe checks", "data")]
for x, (t, s_, k) in zip(xs, T): box(x, 90, w, 16, t, s_, k)
for a_, b_ in zip(xs, xs[1:]): arrow((a_ + w + 0.3, 98), (b_ - 0.3, 98))
hand(156, 89.3, 85.2, "handoff: the draw, data/frames/sites_draw_cf.csv")
# Lane 2
lane(56, 29, "Pipeline 2: build the vibe-coded page", "per site; the generator sees only the brief and the images")
xs2 = [4, 32, 60, 88, 116, 144]; w2 = 22
T2 = [("Skeleton", "Wayback HTML ->\ncopy + images", "code"), ("Sanitize", "strip placement words,\nalt text, dividers", "code"), ("Designer brief", "LLM restates content only;\nnames, numbers, URLs kept", "new"),
      ("Generate", "Claude Code, no style\nor format instruction", "llm"), ("Render", "vibe-coded page,\n1440 px screenshot", "code"), ("Original render", "archived 2021 page,\nsame viewport", "data")]
for x, (t, s_, k) in zip(xs2, T2): box(x, 58, w2, 17, t, s_, k)
for a_, b_ in list(zip(xs2, xs2[1:]))[:4]: arrow((a_ + w2 + 0.3, 66.5), (b_ - 0.3, 66.5))
hand(127, 55.3, 51.2, "handoff: data/<site>/original/ and generated_cli/r1/free/render/")
# Lane 3
lane(2, 48, "Pipeline 3: annotate", "per site, then across sites")
box(4, 26, 28, 16, "Observe: original", "Sonnet judge, original\npage alone", "llm"); box(4, 6, 28, 16, "Observe: vibe-coded", "Sonnet judge, generated page alone;\ncites element ids (element map)", "llm")
box(40, 14, 28, 20, "Combine", "Opus judge: general, changed,\ngenerated_only, original_only", "llm")
box(76, 14, 28, 20, "Tag", "attribute = UI/UX feature,\nvalue = what happens to it,\nfamily, shared vocabulary", "llm")
box(112, 26, 26, 16, "Diff list per site", "n sites -> n diff lists\n(1,274 items for 28 sites)", "data")
box(112, 5, 26, 16, "Master list", "embedding pre-grouping + LLM\nfamily > attribute > value", "new")
box(143, 26, 25, 16, "Galleries + collages", "what each common feature\nlooks like on vibe-coded pages", "code")
box(143, 5, 25, 16, "Seed match, at the end", "120-item seed list against\nthe master list (corpus)", "new")
arrow((32.3, 34), (39.7, 27), rad=0.0); arrow((32.3, 14), (39.7, 21), rad=0.0); arrow((68.3, 24), (75.7, 24)); arrow((104.3, 26), (111.7, 33)); arrow((125, 25.7), (125, 21.3))
arrow((138.3, 13), (142.7, 13)); arrow((138.3, 19), (142.7, 28))
ax.text(168, 0.2, "yellow = new in the 2026-11-04 redesign   orange = LLM step   green = code   blue = data", ha="right", fontsize=8.2, color=MUT)
fig.savefig("pipeline_diagram.png", dpi=150, facecolor=SURF, bbox_inches="tight"); print("wrote pipeline_diagram.png")
