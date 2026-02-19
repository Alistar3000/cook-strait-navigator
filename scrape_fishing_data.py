#!/usr/bin/env python3
"""
Scrape fishing reports from fishing.net.nz forum and bite times calendar.
Automatically creates fishing report files for Wellington/Kapiti locations.
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import os
from pathlib import Path

# Locations we're interested in
TARGET_LOCATIONS = {
    'wellington': ['Wellington', 'Lyall Bay', 'Oriental Bay', 'Baring Head', 'Barrett Reef'],
    'kapiti': ['Kapiti', 'Plimmerton', 'Raumati', 'Waikanae', 'Otaki'],
    'other_local': ['Pukerua', 'Mana Island', 'Tory Channel', 'Cook Strait', 'Picton']
}

def scrape_bite_times():
    """Fetch and parse bite times from fishing sites"""
    sources = [
        "https://www.bitetimes.fishing/bite-times/kapiti-island",
        "https://www.fishing.net.nz/fishing-advice/bite-times/"
    ]
    
    for url in sources:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"🎣 Trying bite times from {url.split('/')[2]}...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract bite times data - looking for major/minor bites and times
            bite_data = {}
            
            # Parse the schedule section
            days = soup.find_all('h5')
            for day_elem in days:
                day_text = day_elem.get_text(strip=True)
                if not re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', day_text):
                    continue
                    
                # Extract date and times
                parent = day_elem.find_parent()
                if parent:
                    time_text = parent.get_text()
                    # Look for major and minor bite times in format HH:MM - HH:MM
                    times = re.findall(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', time_text)
                    if times:
                        bite_data[day_text] = times
            
            if bite_data:
                print(f"✅ SUCCESS fetching from {url.split('/')[2]}")
                return bite_data
            
        except Exception as e:
            print(f"⚠️  {url.split('/')[2]} failed: {e}")
            continue
    
    print("❌ All bite time sources blocked or unavailable")
    return None

def scrape_forum_reports():
    """Scrape fishing reports from fishing.net.nz forum"""
    try:
        forum_url = "https://www.fishing.net.nz/forum/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print("🌐 Scraping fishing forum reports...")
        response = requests.get(forum_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for forum threads/posts about fishing
        reports = []
        
        # Try to find post containers (structure varies by forum)
        posts = soup.find_all(['article', 'div'], class_=re.compile('post|thread|report', re.I))
        
        if not posts:
            # Fallback: look for any content with location names
            posts = soup.find_all('div', class_=re.compile('content|body', re.I))
        
        for post in posts[:20]:  # Limit to avoid timeouts
            text = post.get_text()
            
            # Check if post mentions our target locations
            location_found = False
            location_name = None
            
            for region, locs in TARGET_LOCATIONS.items():
                for loc in locs:
                    if loc.lower() in text.lower():
                        location_found = True
                        location_name = loc
                        break
                if location_found:
                    break
            
            if location_found and len(text) > 100:
                # Extract relevant fishing information
                report = {
                    'location': location_name,
                    'text': text[:500],  # First 500 chars
                    'timestamp': datetime.now().isoformat(),
                    'source': 'fishing.net.nz forum'
                }
                reports.append(report)
        
        return reports if reports else None
        
    except Exception as e:
        print(f"❌ Error scraping forum: {e}")
        return None

def parse_forum_report_to_markdown(report, location_data=None):
    """Convert scraped forum data to markdown fishing report format"""
    
    text = report.get('text', '')
    location = report.get('location', 'Unknown')
    
    # Extract any fish species mentioned
    species_keywords = ['snapper', 'kahawai', 'gurnard', 'kingfish', 'blue cod', 
                       'tarakihi', 'trevally', 'yellowtail', 'groper', 'hapuka']
    species_found = []
    for species in species_keywords:
        if species.lower() in text.lower():
            species_found.append(species.capitalize())
    
    # Extract conditions if mentioned
    conditions = []
    if 'calm' in text.lower():
        conditions.append('Light winds')
    if 'northerly' in text.lower():
        conditions.append('Northerlies')
    if 'southerly' in text.lower():
        conditions.append('Southerlies')
    if 'tide' in text.lower():
        conditions.append('Variable tides')
    
    # Build markdown report
    markdown = f"""## {location.upper()}

### Location
{location}, Wellington Region
Source: fishing.net.nz forum
Scraped: {report.get('timestamp', 'Unknown')}

### Recent Forum Reports
**Report Snippet**:
{text}

### Species Mentioned
{', '.join(species_found) if species_found else 'Various'}

### Conditions Noted  
{', '.join(conditions) if conditions else 'Variable conditions'}

### To Add This Systematically
This report was auto-generated from forum data. To add manual validation:
1. Check forum thread for full context
2. Verify species and conditions
3. Add actual catch data and dates
4. Note successful techniques mentioned

### Source
fishing.net.nz forum
"""
    
    return markdown

def create_automated_reports(forum_reports):
    """Create markdown files from forum reports"""
    
    if not forum_reports:
        print("❌ No forum reports to process")
        return 0
    
    fishing_reports_dir = Path("fishing_reports")
    if not fishing_reports_dir.exists():
        fishing_reports_dir.mkdir(parents=True)
    
    created = 0
    for report in forum_reports:
        location = report.get('location', 'Unknown')
        
        # Clean filename
        filename = re.sub(r'[^\w\s-]', '', location).strip().replace(' ', '_').upper()
        filepath = fishing_reports_dir / f"{filename}_FORUM.md"
        
        # Don't overwrite existing detailed reports
        if filepath.exists():
            print(f"⏭️  Skipping {filepath.name} (already exists)")
            continue
        
        markdown = parse_forum_report_to_markdown(report)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"✅ Created {filepath.name}")
            created += 1
        except Exception as e:
            print(f"❌ Failed to create {filepath.name}: {e}")
    
    return created

def save_bite_times_reference(bite_times):
    """Save bite times data for agent reference"""
    
    if not bite_times:
        print("⚠️  No bite times to save")
        return False
    
    filepath = Path("fishing_reports") / "BITE_TIMES_REFERENCE.json"
    
    try:
        data = {
            'source': 'https://www.fishing.net.nz/fishing-advice/bite-times/',
            'scraped': datetime.now().isoformat(),
            'bite_times': bite_times,
            'note': 'Major and minor bite times for each day. Use this to enhance fishing recommendations.'
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Saved bite times to {filepath.name}")
        return True
    except Exception as e:
        print(f"❌ Failed to save bite times: {e}")
        return False

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🎣 FISHING DATA SCRAPER - Wellington & Kapiti Region")
    print("="*60 + "\n")
    
    # Check if requests library is available
    try:
        import requests
        import bs4
    except ImportError:
        print("⚠️  Required libraries not installed.")
        print("Run: pip install requests beautifulsoup4")
        return
    
    # Fetch bite times
    print("📅 Step 1: Fetching bite times calendar...")
    bite_times = scrape_bite_times()
    if bite_times:
        print(f"✅ Got bite times for {len(bite_times)} days")
        save_bite_times_reference(bite_times)
    else:
        print("⚠️  Could not fetch bite times (may need manual entry)")
    
    # Scrape forum
    print("\n📝 Step 2: Scraping fishing forum reports...")
    forum_reports = scrape_forum_reports()
    
    if forum_reports:
        print(f"✅ Found {len(forum_reports)} forum posts mentioning target locations")
        created = create_automated_reports(forum_reports)
        print(f"\n✅ Created {created} fishing report files")
    else:
        print("⚠️  Could not scrape forum (site structure may have changed)")
        print("💡 You can manually add reports to fishing_reports/ folder")
    
    # Next steps
    print("\n" + "="*60)
    print("📋 Next Steps:")
    print("="*60)
    print("1. Run: python ingest_knowledge.py")
    print("2. Restart streamlit: streamlit run app.py")
    print("3. Test with: python test_fishing_integration.py")
    print("\n✅ Automated reports are ready for agent use!")

if __name__ == "__main__":
    main()
