from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ScrapeResult:
    vendor: str
    url: str
    success: bool
    status_code: Optional[int]
    response_time_ms: float
    content_length: int
    credits_used: float
    estimated_cost_usd: float = 0.0
    # Diffbot-style structured extraction fields (None for HTML-only scrapers)
    parsed_title: Optional[str] = None
    parsed_text_length: Optional[int] = None  # chars of clean body text
    parsed_fields: Optional[int] = None       # number of structured fields returned
    returns_structured: bool = False
    error: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "vendor": self.vendor,
            "url": self.url,
            "success": self.success,
            "status_code": self.status_code,
            "response_time_ms": round(self.response_time_ms, 2),
            "content_length": self.content_length,
            "credits_used": self.credits_used,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "parsed_title": self.parsed_title,
            "parsed_text_length": self.parsed_text_length,
            "parsed_fields": self.parsed_fields,
            "returns_structured": self.returns_structured,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class BaseScraper(ABC):
    vendor_name: str = "base"
    free_tier_limit: int = 1000       # credits/requests per month (free)
    paid_entry_price_usd: float = 0.0 # cheapest paid plan $/month
    paid_entry_credits: int = 0       # credits included in that plan
    supports_js: bool = False
    supports_proxy: bool = False
    returns_structured: bool = False  # True for AI-extraction APIs (e.g. Diffbot)

    @classmethod
    def usd_per_credit(cls) -> float:
        if cls.paid_entry_credits == 0:
            return 0.0
        return cls.paid_entry_price_usd / cls.paid_entry_credits

    def _estimate_cost(self, credits: float) -> float:
        return round(credits * self.usd_per_credit(), 6)

    @abstractmethod
    def scrape(
        self, url: str, render_js: bool = False, use_proxy: bool = False
    ) -> ScrapeResult:
        """Scrape a URL and return a ScrapeResult."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the API key/token is set and non-empty."""
        pass
