# Operator Runbook

This runbook covers the current Beike/Lianjia workflow and local recommendation pipeline.

## Safety Rules

- Do not bypass login, CAPTCHA, or anti-bot pages.
- Use system Chrome for Beike/Lianjia pages that require login.
- Back up `data/listings.json` before clearing or rewriting local data.
- Keep `data/`, browser profiles, saved HTML, and backup files out of git.

## Backup And Reset Local Listings

```bash
mkdir -p data/backups
cp data/listings.json data/backups/listings.before-reset.$(date +%Y%m%d-%H%M%S).json
printf '[]\n' > data/listings.json
```

## Crawl Beike From Current Chrome Tab

Ask the user to open and verify the filtered Beike list page in Chrome, then run:

```bash
python3 scripts/crawl_interactive.py \
  --platform 贝壳 \
  --city 上海 \
  --budget-max 250 \
  --current-chrome \
  --auto-next \
  --save \
  --exclude-keywords 大厦,商务,商住,商业,办公,写字楼,酒店式,公寓 \
  --recommend-limit 15
```

For the Shanghai Xuhui/Huangpu workflow, target URLs are:

```text
https://sh.ke.com/ershoufang/xuhui/ep250su1sf1/
https://sh.ke.com/ershoufang/huangpu/ep250su1sf1/
```

If CAPTCHA appears, stop and ask the user to solve it in Chrome. After the page returns to the listing page, rerun the same command.

## Estimate Rent

After crawl completion, fill reference rent:

```bash
python3 scripts/enrich_rent_estimates.py \
  --city 上海 \
  --budget-max 250 \
  --only-near-subway \
  --only-ordinary-residence \
  --chrome \
  --pause-on-block \
  --save
```

The script opens first-page Beike whole-rent results by community, computes median rent per square meter, and writes estimated monthly rent back to matching listings.

## Recommend

Final clickable ranking:

```bash
python3 scripts/recommend_listings.py \
  --budget-max 250 \
  --only-near-subway \
  --only-ordinary-residence \
  --exclude-keywords 大厦,商务,商住,商业,办公,写字楼,酒店式,公寓 \
  --limit 15 \
  --format markdown
```

Default scoring excludes rent and rent yield. Rent stays visible as context.

## Verification

```bash
python3 -m py_compile scripts/*.py
python3 scripts/recommend_listings.py --help
python3 scripts/crawl_interactive.py --help
python3 scripts/enrich_rent_estimates.py --help
```
