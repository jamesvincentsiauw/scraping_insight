from dataclasses import dataclass


@dataclass
class Target:
    url: str
    label: str
    tier: int
    render_js: bool = False
    use_proxy: bool = False
    description: str = ""


TARGETS: list[Target] = [
    Target(
        url="https://www.sae.org/professional-development/advanced-technologies",
        label="sae-advanced-tech",
        tier=2,
        render_js=True,
        use_proxy=True,
        description="SAE professional development page — content-rich, JS rendered",
    ),
    Target(
        url="https://www.mas.gov.sg/regulation/regulations-and-guidance?content_type=Notices",
        label="mas-regulation-notices",
        tier=2,
        render_js=True,
        description="MAS (Monetary Authority of Singapore) regulatory notices — JS-rendered table",
    ),
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
