"""Is the prompt copy English? Sentence-level language ID with Lingua over the extracted copy (markdown stripped).
english_share(md) -> (word-weighted share of detected sentences (>=6 words) that are English, number of sentences used)
"""
import re, functools
from lingua import Language, LanguageDetectorBuilder

@functools.lru_cache(maxsize=1)
def _detector(): return LanguageDetectorBuilder.from_all_languages().build()

def _sentences(md):
    out = []
    for line in md.splitlines():
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line); line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"^[#>\-\s—]+", "", line).replace("**", "").replace("*", "").strip()
        for part in re.split(r"(?<=[.!?])\s+", line):
            if len(part.split()) >= 6 and not re.search(r"[<>{}]|https?://|www\.|\]\(|\bjavascript\b|\bend of\b.*\bcode\b", part, re.I): out.append(part)  # names/link lists are too short for reliable ID
    return out

def english_share(md):
    d = _detector(); res = [(d.detect_language_of(s), len(s.split())) for s in _sentences(md)]
    res = [(l, w) for l, w in res if l is not None]
    tot = sum(w for _, w in res)
    return (sum(w for l, w in res if l == Language.ENGLISH) / tot if tot else 0.0), len(res)  # word-weighted share
