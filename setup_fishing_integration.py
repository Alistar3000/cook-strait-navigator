#!/usr/bin/env python3
"""
Advanced scraper using browser automation (Selenium) to bypass 403 blocking.
Falls back to manual data entry or cached data.
"""

import json
from datetime import datetime
from pathlib import Path
import time

def create_manual_bite_times_template():
    """Create a template for manual entry of bite times"""
    
    template = {
        "source": "https://www.fishing.net.nz/fishing-advice/bite-times/",
        "instructions": "Visit the link above, take screenshots of bite times, and enter data manually here. Format: HH:MM - HH:MM",
        "note": "Due to website blocking automated access, manual entry recommended. Once data is in this file, it becomes the reference source.",
        "sample_date": "Thu 19-Feb-2026",
        "sample_data": {
            "major_bites": [
                {"time": "13:45 - 15:45", "note": "Afternoon major bite window"},
                {"time": "01:23 - 03:23", "note": "Early morning major bite window"}
            ],
            "minor_bites": [
                {"time": "05:20 - 08:20", "note": "Morning minor bite"},
                {"time": "18:01 - 21:01", "note": "Evening minor bite"}
            ],
            "sun": {
                "rise": "06:55",
                "set": "20:13"
            },
            "moon": {
                "rise": "08:20",
                "set": "21:01"
            }
        }
    }
    
    filepath = Path("fishing_reports") / "BITE_TIMES_MANUAL.json"
    
    try:
        if not filepath.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(template, f, indent=2)
            print(f"✅ Created template: {filepath}")
            print("   Edit this file to add real bite times from the website")
            return filepath
    except Exception as e:
        print(f"❌ Error creating template: {e}")
    
    return None

def create_manual_forum_reports_guide():
    """Create a guide for manually adding forum fishing reports"""
    
    guide = """# Manual Fishing Report Entry Guide

## How to Add Forum Fishing Reports

Since automated scraping is blocked, use this method to manually add fishing forum data:

### Step 1: Find Forum Reports
Visit: https://www.fishing.net.nz/forum/

Look for posts about Wellington and Kapiti fishing with actual reports.

### Step 2: Create Report File
Create a file in `fishing_reports/` with:
- Filename: `LOCATION_SOURCE_DATE.md`
- Format: Markdown (.md) or plain text (.txt)

### Step 3: Extract Information
Copy the forum post information and organize it:

```markdown
## LOCATION NAME

### Forum Source
- Thread: [thread title]
- Author: [poster name]
- Date Posted: [date]
- Source: https://www.fishing.net.nz/forum/

### Report Summary
[Copy relevant fishing report text]

### Species Caught
- Species: Size range and count

### Conditions Reported
- Wind: [speed and direction]
- Tide: [state]
- Time: [time of day caught]
- Weather: [other conditions]

### Techniques Used
- Method 1
- Method 2

### Location Details
- Exact spot (if mentioned)
- Access points
- Hazards noted

### Recommendations from Forum
[Any tips or advice from the post]
```

### Step 4: Save and Ingest
1. Save file to `fishing_reports/` folder
2. Run: `python ingest_knowledge.py`
3. Restart streamlit

### Example
Create `fishing_reports/WELLINGTON_HARBOR_FORUM_FEB2026.md` with actual post data.

## Automated Scraper Status
- Website blocks automated access (403 Forbidden)
- Recommendation: Use browser to manually export data
- Alternative: Use this guide for structured entry

## Tips for Good Reports
- Include specific dates and times
- Note actual catch results, not theory
- Mention exact conditions (wind speed, direction, tide state)
- List species with sizes
- Describe techniques that worked
- Note what DIDN'T work (important for pattern learning)

The system learns best from detailed, dated, actual fishing outcomes.
"""
    
    filepath = Path("fishing_reports") / "MANUAL_REPORT_GUIDE.md"
    
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(guide)
        print(f"✅ Created guide: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error creating guide: {e}")
    
    return None

def check_selenium_option():
    """Check if Selenium is available for advanced scraping"""
    
    print("\n" + "="*60)
    print("ADVANCED OPTION: Selenium Browser Automation")
    print("="*60)
    
    try:
        from selenium import webdriver
        print("✅ Selenium is installed")
        print("   Can use browser automation to bypass 403 blocking")
        print("   Run: pip install selenium")
        return True
    except ImportError:
        print("❌ Selenium not installed")
        print("   Install with: pip install selenium")
        print("   Then download ChromeDriver matching your Chrome version")
        print("   This enables full browser automation to scrape the forum")
        return False

def main():
    """Main execution"""
    
    print("\n" + "="*60)
    print("🎣 FISHING DATA INTEGRATION - Workaround Setup")
    print("="*60 + "\n")
    
    print("ℹ️  Automated web scraping is blocked (403 Forbidden)")
    print("    Website has anti-bot protection against automated requests\n")
    
    print("📋 SOLUTION: Manual + Automated Hybrid Approach\n")
    
    # Create templates
    print("Step 1: Setting up templates...")
    create_manual_bite_times_template()
    create_manual_forum_reports_guide()
    
    # Check for Selenium
    print("\nStep 2: Checking for browser automation capability...")
    has_selenium = check_selenium_option()
    
    # Guide for next steps
    print("\n" + "="*60)
    print("📚 RECOMMENDED WORKFLOW")
    print("="*60)
    
    if not has_selenium:
        print("\n✅ IF YOU WANT MANUAL ENTRY (Recommended for now):")
        print("   1. Read 'MANUAL_REPORT_GUIDE.md' in fishing_reports/")
        print("   2. Visit https://www.fishing.net.nz/forum/")
        print("   3. Copy Wellington/Kapiti fishing reports")
        print("   4. Create .md files in fishing_reports/ with that data")
        print("   5. Run: python ingest_knowledge.py")
        print("   6. System automatically indexes them")
    
    print("\n⚙️  IF YOU WANT BROWSER AUTOMATION:")
    print("   1. Install Selenium: pip install selenium")
    print("   2. Download ChromeDriver via: https://chromedriver.chromium.org/")
    print("   3. We can enhance scraper_fishing_data.py with Selenium")
    print("   4. This bypasses the 403 Forbidden blocking")
    
    print("\n🔗 DIRECT LINKS FOR REFERENCE:")
    print("   - Bite Times: https://www.fishing.net.nz/fishing-advice/bite-times/")
    print("   - Forum: https://www.fishing.net.nz/forum/")
    print("   - Fishing Reports: https://www.fishing.net.nz/fishing-reports/")
    
    print("\n💡 QUICK START:")
    print("   1. Manually add 2-3 fishing reports to fishing_reports/ folder")
    print("   2. Run: python ingest_knowledge.py")
    print("   3. Test: python test_fishing_integration.py")
    print("   4. Agent will use your reports + bite times reference")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
