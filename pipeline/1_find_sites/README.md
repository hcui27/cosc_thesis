# Pipeline 1: finding the websites

Runner `run_find_sites.py`; its docstring is reproduced here.

```
PIPELINE 1: finding the websites themselves. Runner.
usage: python pipeline/1_find_sites/run_find_sites.py [--stages sample,label,draw] [--n 300] [--seed 0] [--min-english 0.90] [--target 30] [--dry-run]
  sample  build_frame.py          random domains from the 2021-06-01 Tranco list (rank floor dropped 2026-11-04: default --min-rank 1; the 30 drawn sites used --min-rank 100001); fetch each homepage from Wayback (<= 2021) -> data/frames/sample_unpopular.csv, data/frames/html/
  label   label_categories.py     LLM labels each saved homepage with a Cloudflare top-level category, language and confidence -> data/frames/cf_labels.csv   (about $2.60 per 270 pages)
  draw    draw_cf.py              English-only, per-category draw (2 per fulfilled category, topped up to --target) -> data/frames/sites_draw_cf.csv, replacements_cf.csv, qualifying_sites.md
Manual helper, run separately: review_english.py (threshold review sheet). Output of this pipeline: the DRAW. Pipeline 2 takes it from there.
Needs data/frames/tranco_2021/tranco_2021-06-01.csv. Every stage is resumable.
```

Files in this folder:
- `build_frame.py`
- `draw_cf.py`
- `english.py`
- `label_categories.py`
- `page_features.py`
- `review_english.py`
- `run_find_sites.py`

See the top-level `PLAN.md` for decisions, status and open items.
