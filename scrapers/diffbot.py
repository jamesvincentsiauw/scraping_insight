import sys
import time

import requests

sys.path.insert(0, "..")
from config import DIFFBOT_TOKEN
from scrapers.base import BaseScraper, ScrapeResult


class DiffbotScraper(BaseScraper):
    """
    Diffbot — https://www.diffbot.com
    Free tier: 10,000 API calls/month (most generous free tier here)
    Paid entry: $299/mo (commercial use)

    Diffbot is fundamentally different from the other scrapers:
    - It does NOT return raw HTML — it returns structured JSON
    - The AI automatically extracts: title, text, author, date, images, links, tags
    - Use the /analyze endpoint to auto-detect page type
    - 'parsed_text_length' and 'parsed_fields' are meaningful quality signals

    Because it returns structured data, content_length reflects JSON size.
    Compare parsed_text_length across vendors for a fairer quality comparison.
    Docs: https://docs.diffbot.com/reference/introduction-to-diffbot-apis
    """

    vendor_name = "Diffbot"
    free_tier_limit = 10_000
    paid_entry_price_usd = 299.0
    paid_entry_credits = 500_000  # approximate: ~$0.000598/call at Starter plan
    supports_js = True   # Diffbot renders JS natively
    supports_proxy = True
    returns_structured = True
    BASE_URL = "https://api.diffbot.com/v3/analyze"

    def __init__(self):
        self.token = DIFFBOT_TOKEN

    def is_configured(self) -> bool:
        return bool(self.token)

    def scrape(
        self, url: str, render_js: bool = False, use_proxy: bool = False
    ) -> ScrapeResult:
        params: dict = {
            "token": self.token,
            "url": url,
            # /analyze auto-detects page type (article, product, discussion, etc.)
        }

        start = time.perf_counter()
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            elapsed_ms = (time.perf_counter() - start) * 1000

            success = resp.status_code == 200
            raw_json = resp.json() if success else {}

            # Extract quality signals from Diffbot's structured response
            objects = raw_json.get("objects", [])
            first = objects[0] if objects else {}

            parsed_title = first.get("title") or first.get("name")
            body_text = first.get("text") or first.get("description") or ""
            # Count non-null top-level fields as a proxy for extraction richness
            parsed_fields = sum(1 for v in first.values() if v not in (None, "", [], {}))

            return ScrapeResult(
                vendor=self.vendor_name,
                url=url,
                success=success,
                status_code=resp.status_code,
                response_time_ms=elapsed_ms,
                content_length=len(resp.content),
                credits_used=1.0,
                estimated_cost_usd=self._estimate_cost(1.0),
                parsed_title=parsed_title,
                parsed_text_length=len(body_text),
                parsed_fields=parsed_fields,
                returns_structured=True,
                error=None if success else resp.text[:300],
                raw_content=resp.content if success else None,  # JSON bytes
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
                returns_structured=True,
                error=str(exc),
            )
