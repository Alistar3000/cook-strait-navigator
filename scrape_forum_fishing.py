#!/usr/bin/env python3
"""
Forum fishing report scraper - extracts fishing data from provided forum links.
Automatically parses reports and creates markdown files for each location/entry.

Uses Selenium for browser automation to bypass anti-scraping protections.

Usage:
    python scrape_forum_fishing.py --url "https://forum.example.com/thread/123"
    python scrape_forum_fishing.py --file forum_urls.txt
    python scrape_forum_fishing.py  # Interactive mode
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
import re
import sys
import argparse
from urllib.parse import urlparse
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FishingForumScraper:
    """Scrape fishing reports from forum URLs using browser automation"""
    
    def __init__(self):
        self.browser = None
        self.debug_mode = False  # Debug flag for showing unmatched posts
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Location keywords to extract/organize reports by
        self.location_keywords = {
            'wellington': ['wellington', 'lyall', 'oriental', 'baring', 'barrett', 'south coast'],
            'kapiti': ['kapiti', 'plimmerton', 'raumati', 'waikanae', 'otaki', 'paraparaumu'],
            'sounds': ['tory', 'koamaru', 'picton', 'sounds', 'queen charlotte'],
            'mana': ['mana', 'mana island'],
            'pukerua': ['pukerua'],
            'general': []  # Fallback for unspecified locations
        }
        
        # Species keywords
        self.species = [
            'snapper', 'kahawai', 'gurnard', 'kingfish', 'trevally',
            'blue cod', 'tarakihi', 'groper', 'hapuka', 'warehou',
            'flatfish', 'bream', 'flounder', 'yellow tail', 'john dory',
            'crayfish', 'rock lobster', 'kina', 'paua'
        ]
    
    def _init_browser(self):
        """Initialize undetected Chrome browser for scraping Cloudflare-protected sites"""
        if self.browser:
            return  # Already initialized
        
        try:
            print("   🌐 Starting undetected browser...")
            
            # Use undetected-chromedriver to bypass Cloudflare
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'User-Agent={self.headers["User-Agent"]}')
            
            # undetected_chromedriver handles the driver installation automatically
            self.browser = uc.Chrome(options=options, version_main=None, no_sandbox=True)
            print("   ✅ Undetected browser ready (bypasses Cloudflare)")
        except Exception as e:
            print(f"   ❌ Failed to start browser: {e}")
            raise
    
    def _close_browser(self):
        """Close the Selenium browser"""
        if self.browser:
            try:
                self.browser.quit()
                self.browser = None
            except:
                pass
    
    def _get_page_content(self, url, wait_for_selector=None, wait_seconds=10):
        """Get page content using Selenium browser"""
        try:
            self.browser.get(url)
            
            # Wait for content to load
            if wait_for_selector:
                try:
                    WebDriverWait(self.browser, wait_seconds).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, wait_for_selector))
                    )
                except TimeoutException:
                    print(f"   ⚠️  Timeout waiting for content selector")
            else:
                # Generic wait for page to load
                time.sleep(2)
            
            return self.browser.page_source
        except Exception as e:
            print(f"   ❌ Browser error: {e}")
            return None
    
    def scrape_forum_url(self, url):
        """Scrape a forum URL and extract fishing reports from ALL pages"""
        
        print(f"\n🌐 Scraping: {url}")
        all_reports = []
        current_url = url
        page_count = 0
        max_pages = 20  # Safety limit to avoid infinite loops
        
        while current_url and page_count < max_pages:
            page_count += 1
            print(f"   📄 Page {page_count}: {current_url}")
            
            try:
                # Initialize browser on first run
                if not self.browser:
                    self._init_browser()
                
                # Get page content using browser
                page_source = self._get_page_content(current_url, wait_for_selector='div')
                
                if not page_source:
                    print(f"   ❌ Failed to load page {page_count}")
                    break
                
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Extract forum posts - try different common selectors
                posts = self._extract_posts(soup)
                
                if not posts:
                    print(f"   ⚠️  No posts found on page {page_count}")
                    break
                
                print(f"   ✅ Found {len(posts)} posts on page {page_count}")
                
                # Parse each post for fishing information
                page_reports = []
                for post in posts:
                    report = self._parse_fishing_report(post, current_url)
                    if report:
                        page_reports.append(report)
                
                print(f"   📊 Extracted {len(page_reports)} fishing reports from page {page_count}")
                all_reports.extend(page_reports)
                
                # Find next page
                next_url = self._find_next_page_url(soup, current_url)
                if next_url:
                    print(f"   ➡️  Found next page link")
                    current_url = next_url
                else:
                    print(f"   ✋ No more pages found")
                    break
                
            except Exception as e:
                print(f"   ❌ Error on page {page_count}: {e}")
                break
        
        if page_count > 1:
            print(f"\n✅ Scraped {page_count} pages total")
        
        print(f"📊 Total: Extracted {len(all_reports)} fishing reports from all pages")
        return all_reports
    
    def _extract_posts(self, soup):
        """Extract forum posts from various forum software"""
        
        posts = []
        
        # Try common forum selectors
        selectors = [
            'div.post',
            'div.message',
            'article.post',
            'div[data-post]',
            'div.entry',
            'div.forum-post',
            'li.post-item',
            'div.topic-post'
        ]
        
        for selector in selectors:
            candidates = soup.select(selector)
            # Filter out very small posts (likely navigation elements)
            posts = [p for p in candidates if len(p.get_text().strip()) > 100]
            if posts:
                return posts[:50]  # Limit to 50 posts to avoid huge scrapes
        
        # Fallback: get all divs with significant text content
        all_divs = soup.find_all('div', class_=re.compile('post|message|comment|entry', re.I))
        posts = [p for p in all_divs if len(p.get_text().strip()) > 100]
        return posts[:50] if posts else []
    
    def _find_next_page_url(self, soup, current_url):
        """Find the next page URL in forum pagination"""
        
        # Strategy 1: Look for rel="next" link (HTML5 standard)
        next_link = soup.find('link', {'rel': 'next'})
        if next_link and next_link.get('href'):
            return self._resolve_url(next_link['href'], current_url)
        
        # Strategy 2: Look for "Next" button/link
        next_selectors = [
            'a[rel="next"]',
            'a:contains("Next")',
            'a.next-page',
            'a[title="Next"]',
            'li.next > a',
            'a.pagination-next',
            'a[aria-label*="next" i]'
        ]
        
        for selector in next_selectors:
            try:
                next_elem = soup.select_one(selector)
                if next_elem and next_elem.get('href'):
                    return self._resolve_url(next_elem['href'], current_url)
            except:
                pass
        
        # Strategy 3: Look for numbered pagination and find next number
        page_links = soup.select('a[href*="start="], a[href*="page="], a[href*="p="]')
        if page_links:
            # Extract page numbers from URLs
            for link in page_links:
                href = link.get('href', '')
                # Extract the page/start parameter
                if 'start=' in href:
                    match = re.search(r'start=(\d+)', href)
                    if match:
                        start_num = int(match.group(1))
                        current_match = re.search(r'start=(\d+)', current_url)
                        if current_match:
                            current_start = int(current_match.group(1))
                            if start_num > current_start:
                                return self._resolve_url(href, current_url)
                        else:
                            # Current URL doesn't have start, might be first page
                            if start_num > 0:
                                return self._resolve_url(href, current_url)
        
        # Strategy 4: Check for common pagination patterns (like &start=20, &start=40, etc)
        if 'start=' in current_url:
            match = re.search(r'start=(\d+)', current_url)
            posts_per_page = 20  # Common default
            if match:
                current_start = int(match.group(1))
                next_start = current_start + posts_per_page
                next_url = re.sub(r'start=\d+', f'start={next_start}', current_url)
                return next_url
        elif '?' in current_url and 'start' not in current_url:
            # Add pagination parameter
            connector = '&' if '?' in current_url else '?'
            return f"{current_url}{connector}start=20"
        
        return None
    
    def _resolve_url(self, href, base_url):
        """Resolve relative URLs to absolute URLs"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            # Absolute path
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{href}"
        else:
            # Relative path
            base_without_query = base_url.split('?')[0]
            if base_without_query.endswith('/'):
                return base_without_query + href
            else:
                return base_without_query + '/' + href
    
    def _parse_fishing_report(self, post_element, post_url):
        """Extract fishing information from a single post"""
        
        text = post_element.get_text()
        
        # Skip posts that are too short
        if len(text) < 50:
            if self.debug_mode:
                print(f"      [DEBUG] Post too short ({len(text)} chars)")
            return None
        
        # Check if post mentions fishing/fish
        if not self._contains_fishing_keywords(text):
            if self.debug_mode:
                snippet = text[:100].replace('\n', ' ')
                print(f"      [DEBUG] No fishing keywords: {snippet}...")
            return None
        
        # Extract key information
        location = self._extract_location(text)
        if not location:
            location = 'General'
        
        species_found = self._extract_species(text)
        conditions = self._extract_conditions(text)
        catch_info = self._extract_catch_info(text)
        
        # Skip if minimal info
        if not species_found and not conditions and not catch_info:
            if self.debug_mode:
                snippet = text[:100].replace('\n', ' ')
                print(f"      [DEBUG] Has fishing keywords but minimal data: {snippet}...")
            return None
        
        report = {
            'location': location,
            'text': text[:1000],  # First 1000 chars
            'species': species_found,
            'conditions': conditions,
            'catch_info': catch_info,
            'source_url': post_url,
            'scraped_date': datetime.now().isoformat(),
            'post_snippet': text[:200]  # For identification
        }
        
        return report
    
    def _contains_fishing_keywords(self, text):
        """Check if post is about fishing"""
        keywords = [
            'fish', 'catch', 'caught', 'fishing', 'bite', 'rod', 'line',
            'bait', 'lure', 'snapper', 'kahawai', 'kingfish', 'spot',
            'water', 'sea', 'bay', 'reef', 'tide', 'wind', 'weather'
        ]
        text_lower = text.lower()
        return sum(1 for k in keywords if k in text_lower) >= 2
    
    def _extract_location(self, text):
        """Extract location name from text"""
        text_lower = text.lower()
        
        for location, keywords in self.location_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return location.replace('_', ' ').title()
        
        return None
    
    def _extract_species(self, text):
        """Extract fish species mentioned"""
        found = []
        text_lower = text.lower()
        
        for species in self.species:
            if species in text_lower:
                found.append(species.title())
        
        return list(set(found))  # Remove duplicates
    
    def _extract_conditions(self, text):
        """Extract weather/conditions mentioned"""
        conditions = []
        
        condition_patterns = {
            'Wind': [r'(north|south|east|west|calm|light|strong|building|shifting)\s*(wind|breeze|northerly|southerly|easterly|westerly|northerlies|southerlies)',
                    r'(\d+)\s*kt.*?(wind|breeze)',
                    r'(calm|light|moderate|strong|gusty|shifty|variable)\s*(conditions|wind)'],
            'Tide': [r'(slack|running|strong|ebbing|flowing|flood|ebb)\s*(tide|water)',
                    r'(incoming|outgoing|high|low)\s*tide',
                    r'tide.*?(running|slack|strong|weak)'],
            'Sea State': [r'(smooth|calm|rough|choppy|lumpy|swell)\s*(sea|conditions|water)',
                         r'(\d+).*?(metre|foot).*?(wave|swell)'],
            'Weather': [r'(sunny|cloudy|overcast|rainy|clear|misty|foggy).*?(conditions|morning|afternoon)',
                       r'(clear skies|good weather|poor conditions)']
        }
        
        text_lower = text.lower()
        
        for condition_type, patterns in condition_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    conditions.append(f"{condition_type}: {matches[0] if isinstance(matches[0], str) else ' '.join(matches[0])}")
                    break
        
        return list(set(conditions))  # Remove duplicates
    
    def _extract_catch_info(self, text):
        """Extract catch information (numbers, sizes)"""
        catch = []
        
        # Look for catch counts
        count_pattern = r'(?:caught|got|landed|got|had|took|pulled)\s+(?:(\d+)|several|a few|multiple|good|well|plenty).*?(?:fish|snapper|kahawai|kingfish|cod|bream|flatfish)?'
        matches = re.findall(count_pattern, text, re.IGNORECASE)
        if matches:
            catch.append(f"Multiple fish landed")
        
        # Look for size mentions
        size_pattern = r'(\d+)\s*(?:cm|mm|kg|lbs?|pound).*?(?:fish|snapper|kahawai|kingfish)'
        matches = re.findall(size_pattern, text, re.IGNORECASE)
        if matches:
            catch.append(f"Fish sizes: {', '.join(set(matches))} cm/kg")
        
        # Look for quality descriptors
        quality = ['excellent', 'great', 'amazing', 'good', 'okay', 'slow', 'poor', 'fantastic', 'productive']
        quality_pattern = rf"({'|'.join(quality)})\s+(?:fishing|catch|bite|session|day)"
        if re.search(quality_pattern, text, re.IGNORECASE):
            match = re.search(quality_pattern, text, re.IGNORECASE)
            catch.append(f"Session quality: {match.group(1)}")
        
        return catch
    
    def save_reports_to_files(self, reports):
        """Save extracted reports to markdown files"""
        
        if not reports:
            print("⚠️  No reports to save")
            return 0
        
        fishing_reports_dir = Path("fishing_reports")
        fishing_reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Group reports by location
        by_location = {}
        for report in reports:
            loc = report['location']
            if loc not in by_location:
                by_location[loc] = []
            by_location[loc].append(report)
        
        created = 0
        
        for location, location_reports in by_location.items():
            # Create one file per location with all reports
            filename = f"{location.upper().replace(' ', '_')}_FORUM.md"
            filepath = fishing_reports_dir / filename
            
            markdown = self._create_markdown_from_reports(location, location_reports)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                print(f"✅ Created {filepath.name} ({len(location_reports)} reports)")
                created += 1
            except Exception as e:
                print(f"❌ Error creating {filepath.name}: {e}")
        
        return created
    
    def _create_markdown_from_reports(self, location, reports):
        """Convert multiple reports to markdown format"""
        
        markdown = f"## {location.upper()}\n\n"
        markdown += f"### Forum Source Data\n"
        markdown += f"- Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown += f"- Total Reports: {len(reports)}\n"
        markdown += f"- Source URLs: {len(set(r['source_url'] for r in reports))} forum threads\n\n"
        
        # Compile aggregate information
        all_species = set()
        all_conditions = set()
        all_catches = set()
        
        for report in reports:
            all_species.update(report['species'])
            all_conditions.update(report['conditions'])
            all_catches.update(report['catch_info'])
        
        # Summary section
        markdown += "### Species Reported\n"
        if all_species:
            for species in sorted(all_species):
                markdown += f"- {species}\n"
        else:
            markdown += "- Various (details in forum posts)\n"
        markdown += "\n"
        
        markdown += "### Conditions Mentioned\n"
        if all_conditions:
            for condition in sorted(all_conditions)[:10]:  # Top 10
                markdown += f"- {condition}\n"
        else:
            markdown += "- Variable conditions\n"
        markdown += "\n"
        
        # Individual reports
        markdown += "### Recent Forum Reports\n\n"
        
        for i, report in enumerate(reports[:20], 1):  # Top 20 reports
            markdown += f"**Report {i}**: {report['post_snippet'][:100]}...\n"
            
            if report['species']:
                markdown += f"  - Species: {', '.join(report['species'][:3])}\n"
            
            if report['conditions']:
                markdown += f"  - Conditions: {', '.join(report['conditions'][:2])}\n"
            
            if report['catch_info']:
                markdown += f"  - Catch: {', '.join(report['catch_info'][:2])}\n"
            
            markdown += f"  - Source: [Link]({report['source_url']})\n\n"
        
        markdown += "### How to Use This Data\n"
        markdown += "1. This data was automatically extracted from forum posts\n"
        markdown += "2. Review the source links for full context\n"
        markdown += "3. Verify catches and conditions match your experience\n"
        markdown += "4. Edit this file to add manual validation notes\n\n"
        
        markdown += f"### Raw Data (JSON)\n"
        markdown += "```json\n"
        markdown += json.dumps({
            'location': location,
            'report_count': len(reports),
            'species': list(all_species),
            'conditions': list(all_conditions),
            'scraped_date': datetime.now().isoformat()
        }, indent=2)
        markdown += "\n```\n"
        
        return markdown


def main():
    parser = argparse.ArgumentParser(
        description='Scrape fishing reports from forum URLs'
    )
    parser.add_argument('--url', help='Single forum URL to scrape')
    parser.add_argument('--file', help='Text file with forum URLs (one per line)')
    parser.add_argument('--urls', nargs='+', help='Multiple URLs as arguments')
    parser.add_argument('--debug', action='store_true', help='Show debug info about posts not matched')
    
    args = parser.parse_args()
    
    scraper = FishingForumScraper()
    scraper.debug_mode = args.debug  # Add debug flag
    all_reports = []
    
    urls_to_scrape = []
    
    # Collect URLs from various input methods
    if args.url:
        urls_to_scrape.append(args.url)
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                # Filter out comments (lines starting with #) and empty lines
                urls_to_scrape = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            return
    elif args.urls:
        urls_to_scrape = args.urls
    else:
        # Interactive mode
        print("\n" + "="*60)
        print("🎣 FORUM FISHING REPORT SCRAPER")
        print("="*60)
        print("\nEnter forum URLs to scrape (one per line, empty line to finish):")
        print("Example: https://www.fishing.net.nz/forum/viewtopic.php?t=12345\n")
        
        while True:
            url = input("URL: ").strip()
            if not url:
                break
            if url.startswith('http'):
                urls_to_scrape.append(url)
            else:
                print("⚠️  Invalid URL (must start with http/https)")
    
    if not urls_to_scrape:
        print("❌ No URLs provided")
        return
    
    print(f"\n{'='*60}")
    print(f"🌐 Scraping {len(urls_to_scrape)} URL(s)")
    print(f"{'='*60}\n")
    
    # Scrape all URLs
    for url in urls_to_scrape:
        reports = scraper.scrape_forum_url(url)
        all_reports.extend(reports)
    
    # Clean up browser
    scraper._close_browser()
    
    if not all_reports:
        print("\n⚠️  No fishing reports found in provided URLs")
        print("💡 Tips:")
        print("  - Check URLs are accessible (not behind login)")
        print("  - Try forum threads with actual fishing discussions")
        print("  - Paste a forum URL directly from your browser address bar")
        return
    
    # Save reports
    print(f"\n📊 Saving {len(all_reports)} total reports...")
    created = scraper.save_reports_to_files(all_reports)
    
    if created > 0:
        print(f"\n✅ Successfully created {created} report file(s)")
        print("\nNext steps:")
        print("1. Review files in fishing_reports/")
        print("2. Run: python ingest_knowledge.py")
        print("3. Restart streamlit: streamlit run app.py")
        print("\n🎣 Your forum data is now integrated into the agent!")
    else:
        print("\n❌ No reports were saved")


if __name__ == "__main__":
    main()
