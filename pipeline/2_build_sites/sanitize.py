"""Strip design clues from the prompt inputs. Reads a site's copy (copy.md, else copy.auto.md) + images/, writes data/<site>/prompt/{copy.md, images/}.
usage: python pipeline/2_build_sites/sanitize.py <site_dir> [--copy copy.md]
Originals are never modified. What is removed / neutralised:
  * image file names are kept EXCEPT words that say where an image goes ('footer-graph.png' -> 'graph.png', 'hero.jpg' -> 'image-01.jpg'); content words stay
  * ALL image alt text / captions-in-brackets ('![5 stars](..)', '![Basecamp logo](..)') -> '![](...)': contextual labels are removed
  * divider rules ('---' from <hr>/<footer>) and '(mobile version ...)' notes
  * images that copy.md does not reference (alternate formats, mobile-only sizes, unused assets), and referenced images that failed to download
Files are copied under their neutralised names; if two images share a name the later one gets a numeric suffix (recorded in prompt/_map.json).
"""
import sys, re, json, shutil, pathlib

PLACEMENT = re.compile(r"(?<![a-z])(hero|banner|header|footer|sidebar|side|nav|navbar|menu|masthead|slider|slide|carousel|background|bg|top|bottom|left|right|above|below|section|cta|homepage|home|splash|strip|band|widget)(?![a-z])", re.I)

def neutral_name(stem, k):
    """Drop placement words from an image file stem; if nothing is left, use image-NN."""
    kept = [t for t in re.split(r"[-_ .]+", stem) if t and not PLACEMENT.fullmatch(t) and not re.fullmatch(r"\d+x?\d*", t)]
    return "-".join(kept) if kept else f"image-{k:02d}"

def sanitize(site_dir, copy_name=None):
    root = pathlib.Path(site_dir)
    src = root / (copy_name or ("copy.md" if (root / "copy.md").exists() else "copy.auto.md"))
    md = src.read_text()
    out = root / "prompt"
    if out.exists(): shutil.rmtree(out)
    (out / "images").mkdir(parents=True)
    mapping = {}
    def swap(m):
        alt, path = m.group(1), m.group(2)
        f = root / path
        if not f.exists() or f.stat().st_size == 0: return ""            # dangling / failed download
        if path not in mapping:
            base = neutral_name(f.stem, len(mapping) + 1); new = f"images/{base}{f.suffix}"; k = 1
            while (out / new).exists(): k += 1; new = f"images/{base}_{k}{f.suffix}"
            shutil.copy2(f, out / new); mapping[path] = new
        return f"![]({mapping[path]})"
    md = re.sub(r"!\[([^\]]*)\]\((images/[^)]+)\)", swap, md)
    md = re.sub(r"^\(mobile version[^\n]*\n?", "", md, flags=re.M)
    md = re.sub(r"^\s*---+\s*$", "", md, flags=re.M)                     # divider rules
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    (out / "copy.md").write_text(md)
    (out / "_map.json").write_text(json.dumps(mapping, indent=1))
    return {"images": len(mapping), "words": len(md.split())}

if __name__ == "__main__":
    print(sanitize(sys.argv[1], sys.argv[sys.argv.index("--copy") + 1] if "--copy" in sys.argv else None))
