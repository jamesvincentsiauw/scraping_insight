import sys
import time

import requests

sys.path.insert(0, "..")
from config import SCRAPESTACK_ACCESS_KEY
from scrapers.base import BaseScraper, ScrapeResult


class ScrapeStackScraper(BaseScraper):
    """
    ScrapeStack (by APILayer) — https://scrapestack.com
    Free tier: 100 requests/month (no credit card required)
    Paid entry: $19.99/mo → 250,000 requests ($0.00008/request) — cheapest paid tier
    Note: Very low free limit (100 req/mo) — budget carefully.
    Docs: https://scrapestack.com/documentation
    """

    vendor_name = "ScrapeStack"
    free_tier_limit = 100
    paid_entry_price_usd = 19.99
    paid_entry_credits = 250_000
    supports_js = False  # no JS rendering on free/basic plans
    supports_proxy = True
    BASE_URL = "https://api.scrapestack.com/scrape"

    def __init__(self):
        self.access_key = SCRAPESTACK_ACCESS_KEY

    def is_configured(self) -> bool:
        return bool(self.access_key)

    def scrape(
        self, url: str, render_js: bool = False, use_proxy: bool = False
    ) -> ScrapeResult:
        params: dict = {
            "access_key": self.access_key,
            "url": url,
        }
        # ScrapeStack supports residential proxies via render_type param on paid plans
        if use_proxy:
            params["residential"] = "1"

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
