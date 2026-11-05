"""Build a static results viewer: data/master/viewer.html (open it in a browser; it links to the images beside it, no server needed).
usage: python pipeline/3_annotate/build_viewer.py [--master-dir data/master] [--seed v1_3]
Tabs: Overview (numbers, distribution plot), Master list (family -> attribute -> value, with the attribute's collage and each value's gallery sheets), Seed list (every seed item and the master attributes matched to it).
Reads master_list.json, galleries/, collages/, seed_match_<seed>.csv and feature_distribution.png; run after run_annotation.py. Re-run it any time the master list changes."""
import sys, re, csv, json, pathlib
g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
D = pathlib.Path(g("--master-dir", "data/master")); SEED = g("--seed", "v1_3")
slug = lambda x: re.sub(r"[^a-z0-9]+", "-", x.lower()).strip("-")[:40]
ML = json.load(open(D / "master_list.json")); GAL, COL = D / "galleries", D / "collages"
gal_dirs = {p.name.split("_")[0]: p for p in GAL.iterdir() if p.is_dir()} if GAL.exists() else {}
col_files = {p.name.split("_")[0]: p.name for p in COL.glob("*.png")} if COL.exists() else {}
fams = []
for fam, F in ML["families"].items():
    attrs = []
    for i, a in enumerate(F["attributes"]):
        aid = f"{fam[:3].upper()}{i + 1:03d}"; gd = gal_dirs.get(aid); sheets = sorted(p.name for p in gd.glob("*.jpg")) if gd else []
        vals = []
        for v in sorted(a["values"], key=lambda v: -v["n_generated"]):
            vs = [f"galleries/{gd.name}/{s}" for s in sheets if s.startswith(slug(v["value"]) + "_p")]
            vals.append({"value": v["value"], "action": v["action"], "n_generated": v["n_generated"], "n_original": v["n_original"], "sites": v["generated_sites"], "example": (v["examples"] or [""])[0], "sheets": vs})
        ng = len({s for v in a["values"] for s in v["generated_sites"]})
        attrs.append({"id": aid, "attribute": a["attribute"], "summary": a["summary"], "n_generated": ng, "n_diff": a["n_sites"], "collage": f"collages/{col_files[aid]}" if aid in col_files else "", "values": vals})
    attrs.sort(key=lambda a: -a["n_generated"]); fams.append({"family": fam, "summary": F["summary"], "attributes": attrs})
seed = list(csv.DictReader(open(D / f"seed_match_{SEED}.csv"))) if (D / f"seed_match_{SEED}.csv").exists() else []
seed_md = (D / f"seed_match_{SEED}.md").read_text() if (D / f"seed_match_{SEED}.md").exists() else ""
nat = sum(len(F["attributes"]) for F in ML["families"].values())
data = {"n_sites": ML["n_sites"], "n_attributes": nat, "families": fams, "seed": seed, "seed_md": seed_md, "seed_name": SEED, "has_plot": (D / "feature_distribution.png").exists()}
HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vibe-coded site signature</title>
<style>
:root{--bg:#fcfcfb;--card:#fff;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3df;--accent:#2a78d6;--chip:#eef2f8}
@media(prefers-color-scheme:dark){:root{--bg:#1a1a19;--card:#232321;--ink:#f0efec;--ink2:#c3c2b7;--line:#3a3a37;--accent:#3987e5;--chip:#2b2f36}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,Helvetica,Arial,sans-serif}
header{padding:20px 24px 0;max-width:1200px;margin:auto}h1{margin:0 0 4px;font-size:22px}.sub{color:var(--ink2);margin:0 0 14px}
nav{display:flex;gap:4px;border-bottom:1px solid var(--line)}nav button{background:none;border:0;padding:10px 16px;font:inherit;color:var(--ink2);cursor:pointer;border-bottom:2px solid transparent}nav button.on{color:var(--ink);border-color:var(--accent);font-weight:600}
main{max-width:1200px;margin:auto;padding:20px 24px 60px}.tab{display:none}.tab.on{display:block}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 16px}.stat b{display:block;font-size:22px}
img{max-width:100%;height:auto;border-radius:6px;border:1px solid var(--line)}
.bar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}input,select{font:inherit;padding:7px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink)}input{min-width:260px}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:8px 0}summary{cursor:pointer;padding:10px 14px;display:flex;gap:10px;align-items:center}summary .n{margin-left:auto;color:var(--ink2);white-space:nowrap}
.pill{display:inline-block;height:8px;border-radius:4px;background:var(--accent);vertical-align:middle}.body{padding:4px 16px 16px}.fam{font-size:17px;margin:22px 0 4px}.muted{color:var(--ink2)}
.val{border-top:1px solid var(--line);padding:10px 0}.chip{display:inline-block;background:var(--chip);border-radius:10px;padding:1px 9px;font-size:12px;margin-right:6px}
.sheets{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}.sheets img{max-width:560px;cursor:zoom-in}.ex{color:var(--ink2);font-size:13.5px;margin:4px 0}
table{border-collapse:collapse;width:100%;background:var(--card)}th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top;font-size:14px}th{cursor:pointer;position:sticky;top:0;background:var(--card)}
#zoom{display:none;position:fixed;inset:0;background:#000d;z-index:9;align-items:center;justify-content:center;cursor:zoom-out}#zoom img{max-width:96vw;max-height:96vh;border:0}

.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(520px,1fr));gap:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}.card h4{margin:0 0 4px;font-size:21px;line-height:1.25}.card .obs{margin:0 0 8px;font-size:16.5px;line-height:1.4;font-weight:500}.card img{width:100%;margin-top:8px;cursor:zoom-in}
.acard{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:12px 0;padding:14px 16px}.acard h4{margin:0;font-size:16px;display:flex;gap:10px;align-items:center}.acard h4 .n{margin-left:auto;font-weight:400;color:var(--ink2);font-size:14px}.acard>img{width:100%;max-width:1100px;margin:10px 0;cursor:zoom-in}
pre{white-space:pre-wrap;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;font-size:13px}
</style></head><body><header><h1>Vibe-coded site signature</h1><p class="sub">What a coding agent builds from a site's content and images, compared with the original. <span id="hs"></span></p>
<nav><button data-t="pl" class="on">Pipeline</button><button data-t="ov">Overview</button><button data-t="ga">Collages</button><button data-t="ml">Master list</button><button data-t="sd">Seed list</button></nav></header>
<main><div id="pl" class="tab on"></div><div id="ov" class="tab"></div><div id="ga" class="tab"></div><div id="ml" class="tab"></div><div id="sd" class="tab"></div></main><div id="zoom"><img></div>
<script>
const D=__DATA__;const $=s=>document.querySelector(s),esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
$("#hs").textContent=D.n_sites+" sites, "+D.n_attributes+" attributes.";
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{document.querySelectorAll("nav button,.tab").forEach(e=>e.classList.remove("on"));b.classList.add("on");$("#"+b.dataset.t).classList.add("on")});
document.addEventListener("click",e=>{if(e.target.matches(".sheets img,.zoomable,.card img,.acard>img")){$("#zoom img").src=e.target.src;$("#zoom").style.display="flex"}else if(e.target.closest("#zoom"))$("#zoom").style.display="none"});
// pipeline summary
$("#pl").innerHTML=`<p>We measure the stylistic signature of vibe-coded websites: what a coding agent builds on its own from a site's content and images, compared with the original. It is not a quality judgement.</p>
<img class="zoomable" src="pipeline_diagram.png" alt="The three pipelines" style="max-width:100%">
<div class="grid" style="margin-top:16px">
<div class="card"><h4>1. Find sites</h4><p class="obs">A random sample of the 2021 Tranco list, English pages only, labelled with Cloudflare categories, 2 drawn per category.</p><span class="muted">30 drawn, 28 usable. Wayback snapshots from 2021 or earlier.</span></div>
<div class="card"><h4>2. Build the vibe-coded page</h4><p class="obs">Scrape the page into copy and images, sanitize, have an LLM rewrite the content as a designer's brief, then Claude Code builds a site from the brief and images with no style instruction.</p><span class="muted">Rendered at 1440 px, desktop only. The brief keeps names, numbers and URLs.</span></div>
<div class="card"><h4>3. Observe and diff</h4><p class="obs">One Sonnet judge describes the original alone, another the vibe-coded page alone, and an Opus judge combines them into a diff list for the site: general, changed, generated only, original only.</p><span class="muted">1,274 diff items over 28 sites (72% changed).</span></div>
<div class="card"><h4>4. Tag</h4><p class="obs">Each item gets an attribute (the UI/UX feature, e.g. footer, corner radius) and a value (what happens to it, e.g. "changed: sharp corners become rounded").</p><span class="muted">A shared vocabulary keeps attribute names consistent across sites.</span></div>
<div class="card"><h4>5. Master list</h4><p class="obs">All diff lists together: attributes are grouped by embedding similarity, then merged and summarised by an LLM into family, attribute and value.</p><span class="muted">${D.n_attributes} attributes in ${D.families.length} families.</span></div>
<div class="card"><h4>6. Evidence and seed match</h4><p class="obs">Galleries and collages show what each common feature looks like on the vibe-coded pages. At the end, a 120-item seed list of known UI components is matched against the master list.</p><span class="muted">${D.seed.filter(r=>+r.master_attributes>0).length} of ${D.seed.length} seed items matched; about half of the attributes are not about any seed item.</span></div>
</div>
<h3 class="fam">How to read this page</h3><p class="muted"><b>Overview</b>: numbers and the feature distribution plot. <b>Collages</b>: one image per attribute, one tile per site. <b>Master list</b>: every attribute with its values and evidence sheets. <b>Seed list</b>: the seed items and what matched. Prevalence counts the sites whose vibe-coded page shows the attribute; a feature on every site is present everywhere but may look different.</p>`;
// overview
const all=D.families.flatMap(f=>f.attributes.map(a=>({...a,family:f.family})));const at2=all.filter(a=>a.n_generated>=2).length,atAll=all.filter(a=>a.n_generated==D.n_sites).length;
const mt=D.seed.filter(r=>+r.master_attributes>0).length;
$("#ov").innerHTML=`<div class="stats"><div class="stat"><b>${D.n_sites}</b>sites</div><div class="stat"><b>${all.length}</b>attributes</div><div class="stat"><b>${at2}</b>on 2+ sites</div><div class="stat"><b>${atAll}</b>on every site</div><div class="stat"><b>${mt} / ${D.seed.length}</b>seed items matched</div></div>`+
(D.has_plot?`<img class="zoomable" src="feature_distribution.png" alt="Feature distribution">`:"")+
`<p class="muted">Prevalence counts the sites whose vibe-coded page shows the attribute (kept, changed or added). Attributes on every site are present everywhere, but how they look still varies: open the Master list for the values and examples.</p>`+
`<h3 class="fam">The most widespread features, as they look on the vibe-coded pages</h3><p class="muted">Each tile is one vibe-coded site's page region for that attribute. Click an image to enlarge; the Collages and Master list tabs have all of them.</p><div class="grid">`+all.filter(a=>a.collage).sort((x,y)=>y.n_generated-x.n_generated).slice(0,12).map(a=>`<div class="card"><h4>${esc(a.attribute)}</h4><p class="obs">${esc(a.summary)}</p><span class="muted">${esc(a.family)} · ${a.n_generated}/${D.n_sites} sites</span><img loading="lazy" src="${a.collage}"></div>`).join("")+`</div>`+
D.families.map(f=>`<h3 class="fam">${esc(f.family)} <span class="muted">(${f.attributes.length} attributes)</span></h3><p class="muted">${esc(f.summary)}</p>`).join("");
// collages tab
$("#ga").innerHTML=`<div class="bar"><select id="gf"><option value="">All families</option>${D.families.map(f=>`<option>${esc(f.family)}</option>`).join("")}</select><input id="gq" placeholder="Search attributes"></div><div class="grid" id="gg"></div>`;
function renderG(){const f=$("#gf").value,q=$("#gq").value.toLowerCase();$("#gg").innerHTML=all.filter(a=>a.collage&&(!f||a.family==f)&&(!q||(a.attribute+a.summary).toLowerCase().includes(q))).sort((x,y)=>y.n_generated-x.n_generated).map(a=>`<div class="card"><h4>${esc(a.attribute)}</h4><p class="obs">${esc(a.summary)}</p><span class="muted">${esc(a.family)} · ${a.n_generated}/${D.n_sites} sites</span><img loading="lazy" src="${a.collage}"></div>`).join("")||"<p class=muted>None.</p>"}
["gf","gq"].forEach(i=>$("#"+i).addEventListener("input",renderG));renderG();
// master list
const fsel=D.families.map(f=>`<option>${esc(f.family)}</option>`).join("");
$("#ml").innerHTML=`<div class="bar"><input id="q" placeholder="Search attributes and values"><select id="fs"><option value="">All families</option>${fsel}</select><select id="mn"><option value="1">Any number of sites</option><option value="2">2+ sites</option><option value="10">10+ sites</option><option value="${D.n_sites}">Every site</option></select></div><div id="list"></div>`;
function renderML(){const q=$("#q").value.toLowerCase(),fs=$("#fs").value,mn=+$("#mn").value;let h="";
for(const f of D.families){if(fs&&f.family!=fs)continue;const rows=f.attributes.filter(a=>a.n_generated>=mn&&(!q||(a.attribute+a.summary+a.values.map(v=>v.value+v.example).join(" ")).toLowerCase().includes(q)));if(!rows.length)continue;
h+=`<h3 class="fam">${esc(f.family)} <span class="muted">${esc(f.summary)}</span></h3>`;
for(const a of rows){h+=`<div class="acard"><h4>${esc(a.attribute)}<span class="pill" style="width:${a.n_generated/D.n_sites*120}px"></span><span class="n">${a.n_generated}/${D.n_sites} sites</span></h4><p class="muted" style="margin:6px 0">${esc(a.summary)}</p>${a.collage?`<img loading="lazy" src="${a.collage}">`:""}<details><summary>${a.values.length} values, with evidence sheets</summary><div class="body">`;
for(const v of a.values)h+=`<div class="val"><span class="chip">${esc(v.action)}</span><b>${esc(v.value.replace(/^[a-z]+: /,""))}</b> <span class="muted">· vibe-coded on ${v.n_generated} sites${v.n_original?`, original on ${v.n_original}`:""}</span><div class="ex">${esc(v.example)}</div><div class="muted" style="font-size:12.5px">${v.sites.map(esc).join(", ")}</div>${v.sheets.length?`<div class="sheets">${v.sheets.map(s=>`<img loading="lazy" src="${s}">`).join("")}</div>`:""}</div>`;
h+=`</div></details></div>`}}
$("#list").innerHTML=h||"<p class=muted>No matches.</p>"}
["q","fs","mn"].forEach(i=>$("#"+i).addEventListener("input",renderML));renderML();
// seed
$("#sd").innerHTML=`<pre>${esc(D.seed_md.split("\n## Seed items never matched")[0])}</pre><div class="bar"><input id="sq" placeholder="Filter seed items"><select id="sm"><option value="">All items</option><option value="y">Matched only</option><option value="n">Never matched</option></select></div><table><thead><tr><th>Item</th><th>Kind</th><th>Sources</th><th>Attributes</th><th>Vibe-coded sites</th><th>Original sites</th><th>Matched master attributes</th></tr></thead><tbody id="sb"></tbody></table>`;
function renderS(){const q=$("#sq").value.toLowerCase(),m=$("#sm").value;$("#sb").innerHTML=D.seed.filter(r=>(!q||(r.item+r.attributes+r.kind).toLowerCase().includes(q))&&(!m||(m=="y")==(+r.master_attributes>0))).sort((a,b)=>+b.sites_ai_built-+a.sites_ai_built).map(r=>`<tr><td><b>${esc(r.item)}</b></td><td>${esc(r.kind)}</td><td class="muted">${esc(r.sources.replace(/\+/g,", "))}</td><td>${r.master_attributes}</td><td>${r.sites_ai_built}</td><td>${r.sites_original}</td><td>${esc(r.attributes)}</td></tr>`).join("")}
["sq","sm"].forEach(i=>$("#"+i).addEventListener("input",renderS));renderS();
</script></body></html>'''
import shutil; (D / "pipeline_diagram.png").write_bytes(pathlib.Path("pipeline_diagram.png").read_bytes()) if pathlib.Path("pipeline_diagram.png").exists() else None
(D / "viewer.html").write_text(HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
print(f"wrote {D / 'viewer.html'}: {nat} attributes, {len(seed)} seed items, {len(col_files)} collages, {len(gal_dirs)} gallery folders")
