from scrapers.base import BaseScraper, ScrapeResult
from scrapers.crawlbase import CrawlbaseScraper
from scrapers.diffbot import DiffbotScraper
from scrapers.scraperapi import ScraperAPIScraper
from scrapers.scrapfly import ScrapFlyScraper
from scrapers.scrapingbee import ScrapingBeeScraper
from scrapers.scrapestack import ScrapeStackScraper

ALL_SCRAPERS: list[type[BaseScraper]] = [
    ScrapingBeeScraper,
    ScrapFlyScraper,
    CrawlbaseScraper,
    ScraperAPIScraper,
    ScrapeStackScraper,
    DiffbotScraper,
]

__all__ = [
    "BaseScraper",
    "ScrapeResult",
    "ScrapingBeeScraper",
    "ScrapFlyScraper",
    "CrawlbaseScraper",
    "ScraperAPIScraper",
    "ScrapeStackScraper",
    "DiffbotScraper",
    "ALL_SCRAPERS",
]
