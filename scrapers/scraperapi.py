import sys
import time

import requests

sys.path.insert(0, "..")
from config import SCRAPERAPI_KEY
from scrapers.base import BaseScraper, ScrapeResult


class ScraperAPIScraper(BaseScraper):
    """
    ScraperAPI — https://www.scraperapi.com
    Free tier: 1,000 credits/month (no credit card required)
    Paid entry: $29/mo → 250,000 credits ($0.000116/credit)
    Credit cost:
      - Basic request:        1 credit
      - JS rendering:         5 credits
      - Premium proxy:       10 credits
      - Ultra premium proxy: 25 credits
    Docs: https://docs.scraperapi.com/making-requests/python
    """

    vendor_name = "ScraperAPI"
    free_tier_limit = 1_000
    paid_entry_price_usd = 29.0
    paid_entry_credits = 250_000
    supports_js = True
    supports_proxy = True
    BASE_URL = "https://api.scraperapi.com/"

    def __init__(self):
        self.api_key = SCRAPERAPI_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def scrape(
        self, url: str, render_js: bool = False, use_proxy: bool = False
    ) -> ScrapeResult:
        params: dict = {
            "api_key": self.api_key,
            "url": url,
        }
        if render_js:
            params["render"] = "true"
        if use_proxy:
            params["premium"] = "true"

        # Estimate credits per ScraperAPI pricing
        credits: float = 1.0
        if render_js and use_proxy:
            credits = 10.0
        elif use_proxy:
            credits = 10.0
        elif render_js:
            credits = 5.0

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
                credits_used=credits,
                estimated_cost_usd=self._estimate_cost(credits),
                error=None if success else resp.text[:300],
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
