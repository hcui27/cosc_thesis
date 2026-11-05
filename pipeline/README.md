# Pipelines

The project is three pipelines. Run each from the project root; each runner takes `--dry-run` (print the commands) and `--stages`.

| Folder | Does | Runner | Hands off |
|---|---|---|---|
| `1_find_sites/` | find unpopular sites, label them by Cloudflare category, draw the study set | `run_find_sites.py` | `data/frames/sites_draw_cf.csv`, `replacements_cf.csv` |
| `2_build_sites/` | scrape from Wayback, skeletonize (copy + images), sanitize, let Claude Code build the site, render it | `run_build_sites.py` (per site: `run_site.py`) | `data/sites.csv`, `data/<site>/original/`, `data/<site>/generated_cli/r1/free/render/` |
| `3_annotate/` | judge original vs generated, turn observations into a feature catalog, detect features, analyse variation | `run_annotation.py` | `data/analysis/` |
| `shared/` | `llm.py` (headless Claude calls), `ledger.py` (cost log), `net.py` (wait for network) | | |

Scripts find each other through a small bootstrap at the top of each file (every folder under `pipeline/` is put on `sys.path`), so module names must stay unique across folders. One cross-dependency: pipeline 1 uses `2_build_sites/skeletonize.py` in text-only mode to get a page's copy. See `PLAN.md` for decisions and status.
