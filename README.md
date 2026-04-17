# Scraper Insight

Benchmarks and compares free-tier web scraping APIs across success rate, latency, credit efficiency, and content quality — with a live analytics dashboard.

## Vendors (all have genuine free tiers)

| Vendor | Free Tier | Signup |
|--------|-----------|--------|
| [ScrapingBee](https://www.scrapingbee.com) | 1,000 credits/month | https://app.scrapingbee.com/account/register |
| [ScrapFly](https://scrapfly.io) | 1,000 credits/month | https://scrapfly.io/register |
| [Crawlbase](https://crawlbase.com) | 1,000 requests/month | https://crawlbase.com/signup |
| [ScraperAPI](https://www.scraperapi.com) | 1,000 credits/month | https://www.scraperapi.com/signup |

> **Not included:** ZenRows (14-day trial only, not a free tier), Oxylabs (trial only).

## Project Structure

```
scraper_insight/
├── .env.example           # API key template
├── config.py              # Reads keys from .env
├── requirements.txt
├── scrapers/
│   ├── base.py            # BaseScraper + ScrapeResult dataclass
│   ├── scrapingbee.py
│   ├── scrapfly.py
│   ├── crawlbase.py
│   └── scraperapi.py
├── benchmark/
│   ├── targets.py         # Test URLs (tier 1–3 by anti-bot strength)
│   └── runner.py          # Parallel benchmark runner
├── storage/
│   └── results.py         # Save/load JSON run files
├── dashboard/
│   └── app.py             # Streamlit analytics dashboard
└── results/               # Auto-created; stores run_YYYYMMDD_HHMMSS.json
```

## Quick Start

```bash
cd scraper_insight

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env — add at least one API key

# 3. Run the benchmark (only configured vendors are used)
python -m benchmark.runner

# Optional flags:
python -m benchmark.runner --tier 1            # only easy targets
python -m benchmark.runner --vendor scrapingbee scrapfly
python -m benchmark.runner --runs 3            # 3 runs per target (averaged)

# 4. Launch the dashboard
streamlit run dashboard/app.py
```

## Metrics Tracked

| Metric | Description |
|--------|-------------|
| **Success Rate** | % of requests returning HTTP 200 |
| **Avg Response Time** | Mean latency in ms |
| **Credits Used** | API credits consumed per request |
| **Content Size** | Bytes returned (proxy for content completeness) |
| **Per-URL Heatmap** | Success rate for each vendor × target combination |
| **Historical Trend** | Response time across multiple runs |

## Target Tiers

| Tier | Description | Example |
|------|-------------|---------|
| 1 | Static HTML, no bot protection | httpbin.org, quotes.toscrape.com |
| 2 | Light JS rendering required | quotes.toscrape.com/js/ |
| 3 | Heavy anti-bot, proxy required | Sites that return 403 without proxy |

## Adding a New Vendor

1. Create `scrapers/yourvendor.py` — extend `BaseScraper`, implement `scrape()` and `is_configured()`
2. Add the API key to `.env.example` and `config.py`
3. Register the class in `scrapers/__init__.py` → `ALL_SCRAPERS`

The runner and dashboard pick it up automatically.
