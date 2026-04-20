import sys
import time

import requests

sys.path.insert(0, "..")
from config import SCRAPFLY_API_KEY
from scrapers.base import BaseScraper, ScrapeResult


class ScrapFlyScraper(BaseScraper):
    """
    ScrapFly — https://scrapfly.io
    Free tier: 1,000 credits/month (no credit card required)
    Paid entry: $20/mo → 50,000 credits ($0.0004/credit)
    Credit cost:
      - Datacenter proxy (default): 1 credit
      - JS rendering:               5 credits
      - Residential proxy:         25 credits
    ScrapFly returns actual credits_used in the API response context.
    Docs: https://scrapfly.io/docs/scrape-api/getting-started
    """

    vendor_name = "ScrapFly"
    free_tier_limit = 1_000
    paid_entry_price_usd = 20.0
    paid_entry_credits = 50_000
    supports_js = True
    supports_proxy = True
    BASE_URL = "https://api.scrapfly.io/scrape"

    def __init__(self):
        self.api_key = SCRAPFLY_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def scrape(
        self, url: str, render_js: bool = False, use_proxy: bool = False
    ) -> ScrapeResult:
        params: dict = {
            "key": self.api_key,
            "url": url,
        }
        if render_js:
            params["render_js"] = "true"
        if use_proxy:
            params["proxy_pool"] = "public_residential_pool"

        start = time.perf_counter()
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            elapsed_ms = (time.perf_counter() - start) * 1000

            data = resp.json()
            result = data.get("result", {})
            origin_status = result.get("status_code", resp.status_code)
            success = resp.status_code == 200 and origin_status == 200

            # ScrapFly returns the actual credit cost in context.cost
            credits = float(data.get("context", {}).get("cost", 1))
            html = result.get("content", "")

            return ScrapeResult(
                vendor=self.vendor_name,
                url=url,
                success=success,
                status_code=origin_status,
                response_time_ms=elapsed_ms,
                content_length=len(html.encode("utf-8")),
                credits_used=credits,
                estimated_cost_usd=self._estimate_cost(credits),
                error=None if success else data.get("message", resp.text[:300]),
                raw_content=html.encode("utf-8") if success else None,
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
