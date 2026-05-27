# Architecture

`home-buyer-helper` is a local skill made of small Python scripts and shared parser/storage helpers. It uses only the standard library for core workflows.

## Data Model

Primary data is stored in ignored local JSON files:

- `data/listings.json`: normalized home listings.
- `data/viewings.json`: viewing notes and scores.
- `data/backups/`: timestamped backups before destructive local-data operations.

Important listing fields:

- Identity and source: `id`, `community`, `name`, `source`, `url`.
- Pricing: `price_wan`, `unit_price`, `monthly_rent`, `rent_source`, `rent_per_sqm`, `rent_sample_count`, `rent_reference_url`.
- Property facts: `room_type`, `area`, `floor`, `total_floors`, `orientation`, `year_built`, `building_age`, `property_type`, `ordinary_residence`.
- Transit and filtering: `near_subway`, `transport`, `nearest_metro`, `metro_distance`.

`data/` is intentionally not committed.

## Core Modules

- `scripts/listing_parsers.py`: shared URL builders, HTML parsers, data loading/saving, duplicate merge logic, Beike/Lianjia filter helpers, rent-list parsing.
- `scripts/crawl_interactive.py`: human-in-the-loop browser import. Reads the active Chrome tab, waits for list DOM readiness, handles Beike pagination conservatively, and stops on CAPTCHA or non-list pages.
- `scripts/crawl_listings.py`: lower-friction HTML/direct fetch import path for pages that do not require active login/CAPTCHA handling.
- `scripts/enrich_rent_estimates.py`: estimates `monthly_rent` from Beike rental pages by community.
- `scripts/recommend_listings.py`: filters and scores local listings, with Markdown output for clickable details.

## Beike/Lianjia Flow

1. User manually opens or filters Beike/Lianjia in system Chrome.
2. `crawl_interactive.py --current-chrome --auto-next --save` reads the active tab.
3. URL tokens are interpreted:
   - `su1`: near subway.
   - `sf1`: ordinary residence.
   - `ep250`: price under 250w.
4. `--exclude-keywords` removes likely commercial or mixed-use listings by matching community/title/property text.
5. The crawler saves unique listings to `data/listings.json`, merging metadata for duplicates.
6. `enrich_rent_estimates.py` can fill reference rent from Beike rent pages.
7. `recommend_listings.py` produces the final ranking.

The crawler never bypasses CAPTCHA. If validation appears, the user handles it in Chrome and reruns the command.

## Recommendation Scoring

Default recommendation scoring does not use rent or rent yield.

Default weights:

| Dimension | Weight | Notes |
|---|---:|---|
| Metro/commute | 45 | Precise `metro_distance` when present; Beike `su1` listings count as subway-friendly when exact distance is missing. |
| Rental-fit layout | 25 | Defaults favor 1-2 bedroom units and 35-90 sqm. |
| Liquidity | 15 | Area and online listing metadata. |
| Condition | 10 | Building age and decoration when available. |
| School reference | 5 | Low-weight reference only. |
| Rent yield | 0 | Display/reference only unless explicitly overridden with `--weight-rent`. |

Rent fields remain useful for display, labels, and optional hard filters (`--min-monthly-rent`, `--min-rent-yield`).
