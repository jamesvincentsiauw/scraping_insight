import sys
import time

import requests

sys.path.insert(0, "..")
from config import SCRAPINGBEE_API_KEY
from scrapers.base import BaseScraper, ScrapeResult


class ScrapingBeeScraper(BaseScraper):
    """
    ScrapingBee — https://www.scrapingbee.com
    Free tier: 1,000 credits/month (no credit card required)
    Paid entry: $29/mo → 150,000 credits ($0.000193/credit)
    Credit cost:
      - Basic request:       1 credit
      - JS rendering:        5 credits
      - Premium proxy:      10 credits
      - JS + premium proxy: 75 credits
    Docs: https://www.scrapingbee.com/documentation/
    """

    vendor_name = "ScrapingBee"
    free_tier_limit = 1_000
    paid_entry_price_usd = 29.0
    paid_entry_credits = 150_000
    supports_js = True
    supports_proxy = True
    BASE_URL = "https://app.scrapingbee.com/api/v1/"

    def __init__(self):
        self.api_key = SCRAPINGBEE_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def scrape(
        self, url: str, render_js: bool = False, use_proxy: bool = False
    ) -> ScrapeResult:
        params: dict = {
            "api_key": self.api_key,
            "url": url,
            "render_js": "true" if render_js else "false",
        }
        if use_proxy:
            params["premium_proxy"] = "true"

        # Estimate credits per ScrapingBee pricing
        credits: float = 1.0
        if render_js and use_proxy:
            credits = 75.0
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
