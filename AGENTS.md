# Agent Notes

This project is a local Codex/OpenClaw skill for buying-home workflows. Keep changes scoped to the skill unless the user explicitly asks for workspace-wide cleanup.

## Data Safety

- Runtime data lives under `data/` and is ignored by git. Do not commit `data/listings.json`, Chrome profiles, saved HTML pages, or backups.
- Before destructive data operations, create a timestamped backup under `data/backups/`.
- Do not bypass Beike/Lianjia login, CAPTCHA, or anti-bot checks. Use the human-in-the-loop Chrome workflow and stop when validation is required.

## Current Crawling Workflow

- For Beike/Lianjia, prefer system Chrome with:
  `scripts/crawl_interactive.py --current-chrome --auto-next --save`
- For Shanghai Xuhui/Huangpu 250w-under subway-side ordinary residence work, use:
  `--budget-max 250 --exclude-keywords 大厦,商务,商住,商业,办公,写字楼,酒店式,公寓`
- `su1` in the URL marks near-subway records; `sf1` marks ordinary residence records.
- `--auto-next` defaults to at most 10 pages and stops on CAPTCHA, non-list pages, duplicate URL loops, or last-page metadata.

## Recommendation Semantics

- Price/budget is a hard filter only.
- Rent and rent yield are display/reference fields by default; they do not affect default scoring.
- Default score weights are: rent 0, metro 45, rental-fit 25, liquidity 15, condition 10, school 5.
- Use `--format markdown` for clickable recommendation output.
- Rent estimates come from `scripts/enrich_rent_estimates.py`: first-page Beike whole-rent samples by community, median monthly rent per square meter multiplied by listing area.

## Verification

Use focused standard-library checks:

```bash
python3 -m py_compile scripts/*.py
python3 scripts/recommend_listings.py --budget-max 250 --only-near-subway --only-ordinary-residence --exclude-keywords 大厦,商务,商住,商业,办公,写字楼,酒店式,公寓 --limit 15 --format markdown
```
