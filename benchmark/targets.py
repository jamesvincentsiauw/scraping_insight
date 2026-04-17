"""
Test URLs organized by difficulty tier.

Tier 1 — No protection: plain HTTP, static content, scraper-friendly.
Tier 2 — Light protection: some JS content or minor bot detection.
Tier 3 — Heavy protection: strong anti-bot, requires residential proxy or JS.

We use publicly available, scraper-friendly URLs to stay ethical.
httpbin.org is the canonical choice for Tier 1 — it never changes and
has no anti-bot logic.
"""

from dataclasses import dataclass


@dataclass
class Target:
    url: str
    label: str
    tier: int  # 1, 2, or 3
    render_js: bool = False
    use_proxy: bool = False
    description: str = ""


TARGETS: list[Target] = [
    # ── Tier 1: Static / no protection ─────────────────────────────────────
    Target(
        url="https://httpbin.org/get",
        label="httpbin-get",
        tier=1,
        description="Plain JSON response, zero bot protection",
    ),
    Target(
        url="https://httpbin.org/html",
        label="httpbin-html",
        tier=1,
        description="Simple HTML page from httpbin",
    ),
    Target(
        url="https://quotes.toscrape.com/",
        label="quotes-toscrape",
        tier=1,
        description="Intentionally scrapable quotes site",
    ),
    Target(
        url="https://books.toscrape.com/",
        label="books-toscrape",
        tier=1,
        description="Intentionally scrapable books catalogue",
    ),
    # ── Tier 2: Light JS / mild protection ────────────────────────────────
    Target(
        url="https://quotes.toscrape.com/js/",
        label="quotes-toscrape-js",
        tier=2,
        render_js=True,
        description="JS-rendered version of quotes.toscrape.com",
    ),
    Target(
        url="https://httpbin.org/delay/2",
        label="httpbin-slow",
        tier=2,
        description="Slow endpoint to test timeout handling",
    ),
    Target(
        url="https://www.sae.org/professional-development/advanced-technologies",
        label="sae-advanced-tech",
        tier=2,
        render_js=True,
        description="SAE professional development page — real-world content-rich article, JS rendered",
    ),
    # ── Tier 3: Anti-bot / requires proxy + JS ────────────────────────────
    Target(
        url="https://httpbin.org/status/403",
        label="httpbin-403",
        tier=3,
        use_proxy=True,
        description="Returns 403 — baseline test for proxy bypass",
    ),
    Target(
        url="https://www.g2.com/products/notion/reviews",
        label="g2-reviews",
        tier=3,
        render_js=True,
        use_proxy=True,
        description="G2 review page — Cloudflare + heavy JS, strong anti-bot",
    ),
    Target(
        url="https://www.glassdoor.com/Reviews/Google-Reviews-E9079.htm",
        label="glassdoor-reviews",
        tier=3,
        render_js=True,
        use_proxy=True,
        description="Glassdoor — login wall + Cloudflare, notorious for blocking scrapers",
    ),
    Target(
        url="https://www.indeed.com/jobs?q=software+engineer&l=Singapore",
        label="indeed-jobs",
        tier=3,
        render_js=True,
        use_proxy=True,
        description="Indeed job listings — DataDome anti-bot protection",
    ),
    Target(
        url="https://www.amazon.com/dp/B08N5WRWNW",
        label="amazon-product",
        tier=3,
        render_js=True,
        use_proxy=True,
        description="Amazon product page — aggressive bot fingerprinting",
    ),
    Target(
        url="https://www.zillow.com/homes/for_sale/",
        label="zillow-listings",
        tier=3,
        render_js=True,
        use_proxy=True,
        description="Zillow — PerimeterX anti-bot, requires residential proxy",
    ),
    Target(
        url="https://www.trustpilot.com/review/apple.com",
        label="trustpilot-reviews",
        tier=3,
        render_js=True,
        use_proxy=True,
        description="Trustpilot — Cloudflare challenge, needs JS + proxy",
    ),
]
