#!/usr/bin/env python3
"""
Helper script to download and inspect forum page HTML using undetected-chromedriver.
This handles Cloudflare challenges and saves the real forum page for inspection.

Usage:
    python inspect_forum_undetected.py "https://www.fishing.net.nz/forum/wellington-boat-fishing_topic63514.html"
"""

import sys
import time
import undetected_chromedriver as uc
from pathlib import Path
from bs4 import BeautifulSoup

def inspect_forum_page(url):
    """Download and save forum page HTML using undetected browser"""
    
    print(f"🌐 Downloading (undetected): {url}")
    print()
    
    try:
        # Setup undetected browser
        print("📄 Starting undetected browser...")
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        
        browser = uc.Chrome(options=options, version_main=None, no_sandbox=True)
        
        # Load page
        print("⏳ Loading page (waiting for Cloudflare challenge)...")
        browser.get(url)
        
        # Wait for page to load
        print("⏳ Waiting for forum content to load...")
        time.sleep(5)  # Extra time to ensure content loads
        
        # Get HTML
        html = browser.page_source
        browser.quit()
        
        # Save file
        output_file = Path("forum_page_source_undetected.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ Saved to: {output_file}")
        print(f"📊 File size: {len(html)} bytes")
        print()
        
        # Analyze the HTML
        print("Diagnostic Info:")
        print("=" * 60)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check page title
        title = soup.find('title')
        if title:
            print(f"Page title: {title.text}")
        
        # Look for post-related elements
        post_divs = soup.find_all('div', class_=lambda x: x and any(word in x.lower() for word in ['post', 'message', 'entry', 'topic', 'forum']))
        print(f"\nFound {len(post_divs)} divs with post-related classes")
        
        if post_divs:
            print("\nSample classes found (first 15):")
            seen = set()
            for div in post_divs[:50]:
                classes = div.get('class', [])
                if classes:
                    class_str = ' '.join(classes)
                    if class_str not in seen:
                        print(f"  - {class_str}")
                        seen.add(class_str)
                        if len(seen) >= 15:
                            break
        
        # Check for data attributes
        data_attr_elements = soup.find_all(True, {'data-post': True})
        print(f"\nFound {len(data_attr_elements)} elements with data-post attribute")
        
        # Look for any divs with "post" in attribute
        everything_div = soup.find_all('div')
        post_attrs = [d for d in everything_div if d.get('id') and 'post' in d.get('id', '').lower()]
        print(f"Found {len(post_attrs)} divs with 'post' in id")
        
        if post_attrs:
            print("Sample IDs:")
            for elem in post_attrs[:10]:
                print(f"  - {elem.get('id')}")
        
        # Try to find content areas
        content_divs = soup.find_all('div', class_=lambda x: x and 'content' in x.lower())
        print(f"\nFound {len(content_divs)} divs with 'content' in class")
        
        print("\n" + "=" * 60)
        print("To fix the scraper:")
        print("1. Open forum_page_source_undetected.html in your browser")
        print("2. Right-click on a post → Inspect")
        print("3. Look at the parent div/section container class/id")
        print("4. Tell me the selector (e.g., 'div.post-container', 'div#post-123')")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_forum_undetected.py <forum-url>")
        print()
        print("Example:")
        print('  python inspect_forum_undetected.py "https://www.fishing.net.nz/forum/wellington-boat-fishing_topic63514.html"')
        sys.exit(1)
    
    url = sys.argv[1]
    inspect_forum_page(url)
