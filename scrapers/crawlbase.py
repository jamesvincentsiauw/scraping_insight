import sys
import time

import requests

sys.path.insert(0, "..")
from config import CRAWLBASE_JS_TOKEN, CRAWLBASE_TOKEN
from scrapers.base import BaseScraper, ScrapeResult


class CrawlbaseScraper(BaseScraper):
    """
    Crawlbase (formerly ProxyCrawl) — https://crawlbase.com
    Free tier: 1,000 requests/month (no credit card required)
    Paid entry: $25/mo → 250,000 requests ($0.0001/request)
    Crawlbase uses two separate tokens:
      - Normal token (NC):  for plain HTTP requests (1 credit each)
      - JavaScript token (JS): for JS-rendered requests (1 credit each, different quota)
    Set CRAWLBASE_TOKEN for normal requests and CRAWLBASE_JS_TOKEN for JS rendering.
    Docs: https://crawlbase.com/docs/crawling-api/
    """

    vendor_name = "Crawlbase"
    free_tier_limit = 1_000
    paid_entry_price_usd = 25.0
    paid_entry_credits = 250_000
    supports_js = True
    supports_proxy = True
    BASE_URL = "https://api.crawlbase.com/"

    def __init__(self):
        self.token = CRAWLBASE_TOKEN
        self.js_token = CRAWLBASE_JS_TOKEN

    def is_configured(self) -> bool:
        return bool(self.token)

    def scrape(
        self, url: str, render_js: bool = False, use_proxy: bool = False
    ) -> ScrapeResult:
        token = self.js_token if render_js and self.js_token else self.token
        params: dict = {
            "token": token,
            "url": url,
        }

        start = time.perf_counter()
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            elapsed_ms = (time.perf_counter() - start) * 1000

            success = resp.status_code == 200

            return ScrapeResult(
                vendor=self.vendor_name,
                url=url,
                success=success,
                status_code=resp.status_code,
                response_time_ms=elapsed_ms,
                content_length=len(resp.content),
                credits_used=1.0,
                estimated_cost_usd=self._estimate_cost(1.0),
                error=None if success else resp.text[:300],
                raw_content=resp.content if success else None,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return ScrapeResult(
                vendor=self.vendor_name,
                url=url,
                success=False,
                status_code=None,
                response_time_ms=elapsed_ms,
                content_length=0,
                credits_used=0,
                estimated_cost_usd=0,
                error=str(exc),
            )
