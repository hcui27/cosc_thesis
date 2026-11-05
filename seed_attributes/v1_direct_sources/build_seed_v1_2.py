"""Seed list v1.2 = v1.1 (Component Gallery + Open UI + Tailwind Plus) PLUS public CSS framework vocabularies (Bootstrap 5.3, Bulma, Foundation 6). Nothing is removed.
usage (project root): python seed_attributes/v1_direct_sources/build_seed_v1_2.py
Input: seed_v1_1.csv (v1 with 3 duplicate names merged), v1_direct_sources/css_frameworks.csv (concept -> the frameworks' own names, included y/n with the reason for each n, from each framework's docs navigation, fetched 2026-11-02).
Rule: NO consensus threshold; every concept in css_frameworks.csv with included=y enters (exhaustive). It is attached to an existing item (its framework names become alternate names, 'css_frameworks' is added to sources)
or becomes a new item. Writes seed_attributes/seed_v1_2.csv. v1 and v1.1 stay as they are."""
import csv, pathlib
D = pathlib.Path("seed_attributes"); items = list(csv.DictReader(open(D / "seed_v1_1.csv"))); by = {r["item"]: r for r in items}
FW = list(csv.DictReader(open(D / "v1_direct_sources" / "css_frameworks.csv")))
dropped = []                                          # nothing is dropped: Tailwind Plus stays, CSS frameworks are ADDED
added = []
for c in FW:                                           # no consensus threshold: every row marked included=y enters (the point is to be exhaustive); included=n rows are listed with the reason
    if c["included"] != "y": continue
    names = [n.strip() for k in ("bootstrap_5_3", "bulma", "foundation_6") for n in c[k].split(";") if n.strip()]
    tgt = c["into"] or c["concept"]
    if tgt in by:
        r = by[tgt]; alts = [x.strip() for x in r["alternate_names"].split(";") if x.strip()]
        for n in names + ([c["concept"]] if c["concept"] != tgt else []):
            if n.lower() != tgt.lower() and n.lower() not in {a.lower() for a in alts}: alts.append(n)
        r["alternate_names"] = "; ".join(alts); r["sources"] = "+".join(dict.fromkeys(r["sources"].split("+") + ["css_frameworks"]))
    else:
        new = {k: "" for k in items[0]}; new.update(item=c["concept"], kind="component", sources="css_frameworks", alternate_names="; ".join(n for n in names if n.lower() != c["concept"].lower()))
        items.append(new); by[c["concept"]] = new; added.append(c["concept"])
nav = by["Navigation"]; nav["alternate_names"] = "; ".join(a for a in nav["alternate_names"].split("; ") if a.lower() != "menu")      # "Menu" is its own item now
w = csv.DictWriter(open(D / "seed_v1_2.csv", "w", newline=""), list(items[0])); w.writeheader(); w.writerows(items)
print(f"{len(items)} items; new from css frameworks: {', '.join(added)}")
