"""Label each saved homepage with Cloudflare's top-level content category (and subcategory), from cheap text signals (no network).
usage: python pipeline/1_find_sites/label_categories.py [--html-dir data/frames/html] [--out data/frames/cf_labels.csv] [--model claude-sonnet-5-5] [--batch 8]
Taxonomy source: https://developers.cloudflare.com/cloudflare-one/traffic-policies/domain-categories/ (26 top-level categories).
Labels are produced by an LLM from the 2021 page, NOT by Cloudflare. Excluded categories stay in the label set so such pages are caught, then dropped.
"""
import sys, os, csv, json, pathlib
import pathlib as _p; sys.path[:0] = [str(d) for d in _p.Path(__file__).resolve().parents[1].iterdir() if d.is_dir() and d.name not in ('deprecated', '__pycache__')]  # all pipeline folders importable
from page_features import features
from llm import ask_json

CF = {
 "Ads": ["Advertisements"],
 "Adult Themes": ["Adult Themes", "Nudity", "Pornography"],
 "Business & Economy": ["Brokerage & Investing", "Business", "Economy & Finance", "Cryptocurrency", "Personal Finance"],
 "Child Abuse": [],
 "Education": ["Education", "Educational Institutions", "Reference", "Science", "Space & Astronomy"],
 "Entertainment": ["Arts", "Audio Streaming", "Cartoons & Anime", "Comic Books", "Entertainment", "Fine Art", "Gaming", "Home Video/DVD", "Humor", "Magazines", "Movies", "Music", "News & Media", "Paranormal", "Radio", "Television", "Video Streaming"],
 "Gambling": ["Gambling"],
 "Government & Politics": ["Charity and Non-profit", "Government/Legal", "Politics, Advocacy, and Government-Related"],
 "Health": ["Health & Fitness", "Sex Education"],
 "Information Technology": [],
 "Internet Communication": ["Chat", "Forums", "Information Security", "Instant Messengers", "Internet Phone & VOIP", "Messaging", "P2P", "Personal Blogs", "Webmail", "Photo Sharing"],
 "Job Search & Careers": ["Job Search & Careers"],
 "Miscellaneous": ["Login Screens", "Miscellaneous", "No Content", "URL Alias/Redirect", "Unreachable"],
 "Questionable Content": ["Deceptive Ads", "Drugs", "Hacking", "Profanity", "Questionable Activities", "Militancy, Hate & Extremism", "Unreliable Information"],
 "Real Estate": ["Real Estate"],
 "Religion": ["Religion & Spirituality"],
 "Security Risks": ["Parked & For Sale Domains", "New Domains", "Newly Seen Domains"],
 "Shopping & Auctions": ["Auctions & Marketplaces", "Coupons", "Ecommerce", "Shopping"],
 "Social & Family": [],
 "Society & Lifestyle": ["Arts & Crafts", "Astrology", "Clothing", "Dating & Relationships", "Digital Postcards", "Parenting", "Fashion", "Food & Drink", "Hobbies & Interests", "Home & Garden", "Lifestyle", "Pets", "Photography", "Professional Networking", "Sexuality", "Social Networks", "Swimsuits", "Tobacco", "Body Art", "Lingerie & Bikini", "Alcohol"],
 "Sports": ["Sports"],
 "Technology": ["APIs", "Content Servers", "File Sharing", "Information Technology", "News, Portal & Search", "Search Engines", "Technology", "Translator", "Artificial Intelligence", "Remote Access", "Shareware/Freeware", "Keep Awake Software"],
 "Travel": ["Travel"],
 "Vehicles": ["Vehicles"],
 "Violence": ["Violence", "Weapons"],
 "Weather": ["Weather"],
}
EXCLUDED = {"Child Abuse", "Gambling", "Questionable Content", "Security Risks", "Violence", "Adult Themes"}

g = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
HD, OUT, MODEL, BATCH = pathlib.Path(g("--html-dir", "data/frames/html")), pathlib.Path(g("--out", "data/frames/cf_labels.csv")), g("--model", "claude-sonnet-5-5"), int(g("--batch", 8))

def main():
    done = {r["domain"] for r in csv.DictReader(open(OUT))} if OUT.exists() else set()
    pages = [features(f) for f in sorted(HD.glob("*.html")) if f.stem not in done]
    new = not OUT.exists(); fields = ["domain", "category", "subcategory", "confidence", "language", "rationale", "title"]
    with open(OUT, "a", newline="") as fh:
        w = csv.DictWriter(fh, fields)
        if new: w.writeheader()
        for i in range(0, len(pages), BATCH):
            chunk = pages[i:i + BATCH]
            prompt = ("Classify each website homepage into exactly one Cloudflare content category (top level) and one of its subcategories, using ONLY this taxonomy "
                      "(category: [subcategories]). Choose by what the site is about / does. 'Miscellaneous' is for login screens, empty pages, redirects and unreachable pages; "
                      "'Security Risks' covers parked/for-sale domains.\n" + json.dumps(CF, indent=1) +
                      "\n\nAlso give confidence (0-1), language ('en','other','mixed') and a rationale of at most 12 words.\n"
                      'Final answer ONLY a JSON array: [{"domain": str, "category": str, "subcategory": str, "confidence": float, "language": str, "rationale": str}], one per page, same order.\n\nPAGES:\n'
                      + json.dumps([{k: v for k, v in p.items() if not k.startswith("_")} for p in chunk], ensure_ascii=False))
            res = ask_json(prompt, MODEL, "cf_label", pages=len(chunk)); by = {p["domain"]: p for p in chunk}
            for r in res:
                p = by.get(r["domain"])
                if p: w.writerow({"domain": r["domain"], "category": r["category"] if r["category"] in CF else "unknown", "subcategory": r.get("subcategory", ""),
                                  "confidence": r["confidence"], "language": r["language"], "rationale": r["rationale"], "title": p["title"]})
            fh.flush(); print(f"{min(i + BATCH, len(pages))}/{len(pages)} labelled", flush=True)

if __name__ == "__main__":
    main()
