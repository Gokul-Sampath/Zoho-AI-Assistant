"""
Zoho Deluge Documentation Crawler using Crawl4AI
Fetches documentation from Zoho Deluge / Creator Script help pages and saves extracted content into local Markdown.
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Default targets
DEFAULT_TARGET_URL = "https://www.zoho.com/creator/help/script/"
CANONICAL_DELUGE_URL = "https://www.zoho.com/deluge/help/"
DEFAULT_OUTPUT_FILE = "zoho_deluge_docs.md"


def is_valid_doc_link(url: str, base_domain: str = "www.zoho.com") -> bool:
    """Filter links to only keep relevant Deluge / Creator documentation pages."""
    parsed = urlparse(url)
    if parsed.netloc != base_domain:
        return False
    path = parsed.path.lower()
    # Must be within deluge/help or creator/help
    if not ("/deluge/help/" in path or "/creator/help/script" in path):
        return False
    # Avoid sign-in, signup, accounts, or non-doc assets
    if any(p in path for p in ["signin", "signup", "download", ".pdf", ".zip", "release-notes"]):
        return False
    return True


async def crawl_zoho_documentation(
    start_url: str = DEFAULT_TARGET_URL,
    output_file: str = DEFAULT_OUTPUT_FILE,
    deep_crawl: bool = False,
    max_pages: int = 0,
    request_delay: float = 1.0,
):
    limit_info = "All pages (unlimited)" if max_pages <= 0 else f"max {max_pages} pages"
    print(f"\n{'='*70}")
    print(f"🚀 Starting Zoho Documentation Crawler with Crawl4AI")
    print(f"📍 Target URL   : {start_url}")
    print(f"📁 Output file  : {output_file}")
    print(f"🔍 Deep crawl   : {'Enabled (' + limit_info + ')' if deep_crawl else 'Disabled (hub page only)'}")
    print(f"{'='*70}\n")

    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
    )

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        css_selector="main",  # Focus on the documentation main container
        word_count_threshold=10,
    )

    extracted_pages = []
    visited_urls = set()

    # Explicitly configure AsyncWebCrawler with max_pages (0 = all pages)
    async with AsyncWebCrawler(config=browser_config, max_pages=max_pages) as crawler:
        # Step 1: Crawl the starting URL
        print(f"⏳ [1] Fetching initial documentation page: {start_url} ...")
        result = await crawler.arun(url=start_url, config=run_config)

        # Check if the initial page was blocked (e.g., deprecated 403 on creator/help/script/)
        if not result.success or (result.status_code and result.status_code >= 400):
            print(f"⚠️  Note: {start_url} returned status {result.status_code} (or was protected).")
            if start_url != CANONICAL_DELUGE_URL:
                print(f"🔄 Automatically redirecting to active canonical Deluge documentation hub: {CANONICAL_DELUGE_URL}")
                start_url = CANONICAL_DELUGE_URL
                result = await crawler.arun(url=start_url, config=run_config)

        if not result.success:
            print(f"❌ Failed to fetch documentation from {start_url}. Error: {result.error_message}")
            return False

        print(f"✅ Successfully extracted {start_url} ({len(result.markdown or '')} markdown characters)")
        visited_urls.add(start_url)
        extracted_pages.append({
            "url": start_url,
            "title": "Zoho Deluge Scripting - Help Documentation Overview",
            "markdown": result.markdown or ""
        })

        # Step 2: Deep crawl subpages if requested
        if deep_crawl:
            internal_links = []
            if hasattr(result, "links") and isinstance(result.links, dict):
                for link in result.links.get("internal", []):
                    href = link.get("href", "")
                    clean_href = href.split("#")[0]  # Remove anchor
                    if clean_href and clean_href not in visited_urls and is_valid_doc_link(clean_href):
                        if clean_href not in internal_links:
                            internal_links.append(clean_href)

            print(f"\n🔗 Discovered {len(internal_links)} relevant documentation subpages.")
            pages_to_crawl = internal_links if max_pages <= 0 else internal_links[:max_pages]
            count_desc = f"all {len(pages_to_crawl)}" if max_pages <= 0 else f"top {len(pages_to_crawl)}"
            print(f"📚 Crawling {count_desc} subpages...\n")

            for idx, page_url in enumerate(pages_to_crawl, start=1):
                if page_url in visited_urls:
                    continue
                visited_urls.add(page_url)

                print(f"⏳ [{idx}/{len(pages_to_crawl)}] Fetching: {page_url} ...")
                try:
                    sub_result = await crawler.arun(url=page_url, config=run_config)
                    if sub_result.success and sub_result.markdown:
                        title = getattr(sub_result, "metadata", {}).get("title") or page_url.rstrip("/").split("/")[-1].replace(".html", "").replace("-", " ").title()
                        print(f"   ↳ Extracted: {title} ({len(sub_result.markdown)} chars)")
                        extracted_pages.append({
                            "url": page_url,
                            "title": title,
                            "markdown": sub_result.markdown
                        })
                    else:
                        print(f"   ↳ ⚠️ Skipping {page_url} (no content or error)")
                except Exception as e:
                    print(f"   ↳ ❌ Error crawling {page_url}: {e}")

                if request_delay > 0:
                    await asyncio.sleep(request_delay)

    # Step 3: Compile everything into a unified Markdown file
    print(f"\n💾 Writing extracted documentation to '{output_file}' ...")
    with open(output_file, "w", encoding="utf-8") as f:
        # Header Metadata
        f.write(f"# Zoho Deluge Scripting Documentation\n\n")
        f.write(f"> **Extracted on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"> **Primary Source:** [{start_url}]({start_url})\n")
        f.write(f"> **Total Pages Extracted:** {len(extracted_pages)}\n\n")
        f.write("---\n\n")

        # Table of Contents
        f.write("## Table of Contents\n\n")
        for i, page in enumerate(extracted_pages, start=1):
            anchor = page['title'].lower().replace(" ", "-").replace("/", "").replace(":", "")
            f.write(f"{i}. [{page['title']}](#{anchor}) - `({page['url']})`\n")
        f.write("\n---\n\n")

        # Page Contents
        for i, page in enumerate(extracted_pages, start=1):
            f.write(f"## {i}. {page['title']}\n\n")
            f.write(f"**Source URL:** [{page['url']}]({page['url']})\n\n")
            f.write(page['markdown'])
            f.write("\n\n---\n\n")

    file_size_kb = os.path.getsize(output_file) / 1024
    print(f"🎉 Done! Documentation successfully saved to '{output_file}' ({file_size_kb:.1f} KB, {len(extracted_pages)} pages).")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Zoho Deluge Help Documentation and export to Markdown using Crawl4AI."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_TARGET_URL,
        help=f"Target URL to start crawling from (default: {DEFAULT_TARGET_URL})",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Path to local output markdown file (default: {DEFAULT_OUTPUT_FILE})",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Enable multi-page crawl across linked Deluge subpages",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=0,
        help="Maximum subpages to crawl when --deep is specified (default: 0 for all pages)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between requests during deep crawl (default: 0.5s)",
    )

    args = parser.parse_args()

    asyncio.run(
        crawl_zoho_documentation(
            start_url=args.url,
            output_file=args.output,
            deep_crawl=args.deep,
            max_pages=args.max_pages,
            request_delay=args.delay,
        )
    )


if __name__ == "__main__":
    main()
