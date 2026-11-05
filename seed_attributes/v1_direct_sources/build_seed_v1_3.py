"""Seed list v1.3 = v1.2 (Component Gallery + Open UI + Tailwind Plus + public CSS frameworks) PLUS the NN/g UI elements glossary (https://www.nngroup.com/articles/ui-elements-glossary/, fetched 2026-11-04).
usage (project root): python seed_attributes/v1_direct_sources/build_seed_v1_3.py
Every glossary term enters (exhaustive; no threshold). A term whose `into` names an existing item becomes an alternate name and adds 'nngroup' to that item's sources; otherwise it is a new item.
Only term names are stored, not the glossary's definitions. Four terms (Control, Input control, Overlay, Picker) are umbrella terms; they are kept as items and noted. Writes seed_attributes/seed_v1_3.csv."""
import csv, pathlib
D = pathlib.Path("seed_attributes"); items = list(csv.DictReader(open(D / "seed_v1_2.csv"))); by = {r["item"]: r for r in items}; added = []
for t in csv.DictReader(open(D / "v1_direct_sources" / "nngroup_glossary.csv")):
    alts = [a.strip() for a in t["alternate_names"].split(";") if a.strip()]; tgt = t["into"] or t["term"]
    if tgt in by:
        r = by[tgt]; have = [x.strip() for x in r["alternate_names"].split(";") if x.strip()]
        for n in alts + ([t["term"]] if t["term"].lower() != tgt.lower() else []):
            if n.lower() != tgt.lower() and n.lower() not in {h.lower() for h in have}: have.append(n)
        r["alternate_names"] = "; ".join(have); r["sources"] = "+".join(dict.fromkeys(r["sources"].split("+") + ["nngroup"]))
    else:
        new = {k: "" for k in items[0]}; new.update(item=t["term"], kind="component", sources="nngroup", alternate_names="; ".join(alts)); items.append(new); by[t["term"]] = new; added.append(t["term"])
w = csv.DictWriter(open(D / "seed_v1_3.csv", "w", newline=""), list(items[0])); w.writeheader(); w.writerows(items)
print(f"{len(items)} items; new from NN/g: {len(added)}: {', '.join(added)}")
