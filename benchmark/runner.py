"""
Benchmark runner — scrapes all targets with all configured vendors and saves results.

Usage:
    cd scraper_insight
    python -m benchmark.runner                  # all targets, all vendors
    python -m benchmark.runner --tier 1         # only tier-1 targets
    python -m benchmark.runner --tier 2         # tier-2 targets (includes SAE + MAS)
    python -m benchmark.runner --label sae-advanced-tech mas-regulation-notices
    python -m benchmark.runner --vendor scrapingbee scrapfly
    python -m benchmark.runner --runs 3         # repeat each target N times
"""

import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, "..")

from benchmark.targets import TARGETS, Target
from config import RESULTS_DIR
from scrapers import ALL_SCRAPERS, BaseScraper, ScrapeResult
from storage.results import save_run


def _scrape_one(scraper: BaseScraper, target: Target) -> ScrapeResult:
    return scraper.scrape(
        url=target.url,
        render_js=target.render_js,
        use_proxy=target.use_proxy,
    )


def _safe_dirname(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_") or "unknown"


def _save_html(result: ScrapeResult) -> None:
    """Write raw_content to results/<target-label>/<Vendor>.html (or .json for Diffbot)."""
    if not result.raw_content:
        return
    target_dir = Path(RESULTS_DIR) / _safe_dirname(result.label)
    target_dir.mkdir(parents=True, exist_ok=True)
    ext = "json" if result.returns_structured else "html"
    out = target_dir / f"{result.vendor}.{ext}"
    out.write_bytes(result.raw_content)


def run_benchmark(
    tier_filter: int | None = None,
    label_filter: list[str] | None = None,
    vendor_filter: list[str] | None = None,
    runs: int = 1,
    workers: int = 4,
) -> list[dict]:
    targets = TARGETS
    if tier_filter is not None:
        targets = [t for t in targets if t.tier == tier_filter]
    if label_filter:
        targets = [t for t in targets if t.label in label_filter]

    scrapers: list[BaseScraper] = []
    for cls in ALL_SCRAPERS:
        scraper = cls()
        if vendor_filter:
            if scraper.vendor_name.lower() not in [v.lower() for v in vendor_filter]:
                continue
        if not scraper.is_configured():
            print(f"  [skip] {scraper.vendor_name} — no API key configured")
            continue
        scrapers.append(scraper)

    if not scrapers:
        print("No vendors configured. Add API keys to .env and retry.")
        return []

    print(f"\nRunning benchmark: {len(scrapers)} vendor(s) × {len(targets)} target(s) × {runs} run(s)")
    print(f"Vendors : {[s.vendor_name for s in scrapers]}")
    print(f"Targets : {[t.label for t in targets]}\n")

    jobs: list[tuple[BaseScraper, Target]] = [
        (scraper, target)
        for scraper in scrapers
        for target in targets
        for _ in range(runs)
    ]

    all_results: list[dict] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_scrape_one, s, t): (s, t) for s, t in jobs}
        for i, future in enumerate(as_completed(futures), 1):
            scraper, target = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print(f"  [{i}/{len(jobs)}] ERROR {scraper.vendor_name} → {target.label}: {exc}")
                continue

            result.label = target.label

            # Save HTML/JSON file for manual comparison
            _save_html(result)

            ext = "json" if result.returns_structured else "html"
            status_icon = "✓" if result.success else "✗"
            print(
                f"  [{i}/{len(jobs)}] {status_icon} {result.vendor:<14} "
                f"{target.label:<30} "
                f"{result.response_time_ms:>7.0f}ms  "
                f"{result.content_length:>8} bytes"
                + (f"  → {result.vendor}.{ext}" if result.raw_content else "  (no content saved)")
            )
            all_results.append(result.to_dict())

    saved_path = save_run(all_results)
    print(f"\nMetrics saved → {saved_path}")
    print(f"HTML files  → results/<target-label>/<Vendor>.html")
    print(f"Total results: {len(all_results)}")
    return all_results


def main():
    parser = argparse.ArgumentParser(description="Scraper Insight Benchmark Runner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Filter targets by tier")
    parser.add_argument("--label", nargs="+", help="Filter targets by label (e.g. sae-advanced-tech)")
    parser.add_argument("--vendor", nargs="+", help="Filter vendors by name")
    parser.add_argument("--runs", type=int, default=1, help="Repeat each target N times")
    parser.add_argument("--workers", type=int, default=4, help="Parallel worker threads")
    args = parser.parse_args()

    run_benchmark(
        tier_filter=args.tier,
        label_filter=args.label,
        vendor_filter=args.vendor,
        runs=args.runs,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
