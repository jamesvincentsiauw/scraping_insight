import os
from dotenv import load_dotenv

load_dotenv()

SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY", "")
SCRAPFLY_API_KEY = os.getenv("SCRAPFLY_API_KEY", "")
CRAWLBASE_TOKEN = os.getenv("CRAWLBASE_TOKEN", "")
CRAWLBASE_JS_TOKEN = os.getenv("CRAWLBASE_JS_TOKEN", CRAWLBASE_TOKEN)
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "")
SCRAPESTACK_ACCESS_KEY = os.getenv("SCRAPESTACK_ACCESS_KEY", "")
DIFFBOT_TOKEN = os.getenv("DIFFBOT_TOKEN", "")

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
