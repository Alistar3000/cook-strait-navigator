# Fishing Intelligence System - Cook Strait Navigator

## How It Works

The system combines three data sources to give smart fishing recommendations:

1. **Live Weather Forecast** (MetOcean API) - Wind, waves, tides
2. **Bite Times Calendar** (bitetimes.fishing / fishing.net.nz) - Major/minor feeding windows, sun/moon
3. **Fishing Forum Reports** (Wellington/Kapiti) - Species, locations, techniques

Agent workflow when user asks "Where should I fish on Wednesday?":
- Fetch Wednesday forecast → Light northerlies, ebbing tide 11am
- Get bite times → Major bite 14:00-16:00  
- Search reports → "Pukerua Bay productive in northerlies" 
- Combine: "Wednesday 1-4pm at Pukerua Bay, major bite window 2-4pm, return by 4pm"

## Current Status

✅ **Weather forecasts** - Working (MetOcean API)  
✅ **Bite times reference** - Available (https://www.bitetimes.fishing/bite-times/kapiti-island & fallback)  
⚠️ **Forum scraper** - Blocked by 403 (both sites have anti-bot protection)  
✅ **Manual report entry** - Ready to use  

## Getting Forum Fishing Data

### Option 1: Automated Forum Scraping (Recommended)

Use the forum scraper to automatically extract fishing reports from forum URLs you provide:

**With a single URL:**
```bash
python scrape_forum_fishing.py --url "https://www.fishing.net.nz/forum/viewtopic.php?t=12345"
```

**With multiple URLs from a file:**
1. Edit `forum_urls.txt` and add your forum thread URLs (one per line)
2. Run: `python scrape_forum_fishing.py --file forum_urls.txt`

**Interactive mode (paste URLs when prompted):**
```bash
python scrape_forum_fishing.py
# Then paste URLs one at a time when prompted
```

The scraper will:
- Extract all fishing posts from the forum threads
- Parse species catches, conditions, techniques
- Create markdown files automatically in `fishing_reports/`
- Group reports by location (Wellington, Kapiti, etc.)

### Option 2: Manual Copy-Paste

1. Visit the forum thread manually
2. Create a `.md` file in `fishing_reports/` folder
3. Paste the report information
4. Run: `python ingest_knowledge.py`

## Getting Bite Times

Bite times are available at:
- Primary: https://www.bitetimes.fishing/bite-times/kapiti-island
- Fallback: https://www.fishing.net.nz/fishing-advice/bite-times/

### For Automated Reference

The system can reference bite times dynamically. To set up manual bite times:

1. Visit the bite times link above  
2. Note the major/minor bite times for your area
3. Add to `fishing_reports/BITE_TIMES_MANUAL.json`
4. Agent includes these in fishing recommendations

Example entry in BITE_TIMES_MANUAL.json:
```json
{
  "Wed 19-Feb": {
    "major_bites": [
      "13:45 - 15:45",
      "01:23 - 03:23"
    ],
    "minor_bites": [
      "05:20 - 08:20", 
      "18:01 - 21:01"
    ]
  }
}
```

## System Components

### Scripts

- **navigator.py** - Main agent (enhanced with FishingReports + BiteTimesAPI tools)
- **bite_times_api.py** - Fetches/caches bite times from website or manual file
- **scrape_fishing_data.py** - Attempts automated scraping (currently blocked)
- **setup_fishing_integration.py** - Creates templates and guides
- **ingest_knowledge.py** - Indexes all fishing data into ChromaDB

### Fishing Reports Directory

```
fishing_reports/
├── README_TEMPLATE.md          # Reference template
├── MANA_ISLAND.md              # Example detailed report
├── MANUAL_REPORT_GUIDE.md      # How to add manual reports
├── BITE_TIMES_MANUAL.json      # Manual bite times entry
└── [user reports].md           # Add your forum data here
```

## Quick Start

### 1. Add a Fishing Report
```bash
# Create fishing_reports/YOUR_LOCATION.md with forum data
# See MANUAL_REPORT_GUIDE.md for format
```

### 2. Ingest Into System
```bash
python ingest_knowledge.py
```

### 3. Restart Streamlit
```bash
# Stop: Ctrl+C
streamlit run app.py
```

### 4. Test It
```bash
python test_fishing_integration.py
```

### 5. Use It
Ask in Streamlit: "Where should I fish on Thursday?"

Agent will:
- Check weather for Thursday
- Fetch bite times  
- Search fishing reports
- Recommend location + timing

## Example Interaction

**User:** "Best fishing spot this weekend?"

**Agent Response:**
```
🎣 FISHING RECOMMENDATION

BEST DAY: Saturday 21-Feb

WEATHER:
- Wind: 10-12kt northerlies
- Waves: 0.5m
- Tide: Ebbing 11am-3pm

BITE TIMES:
- 🟢 Major: 13:45 - 15:45
- 🟡 Minor: 05:20 - 08:20

RECOMMENDED: Pukerua Bay
Based on reports, productive in northerlies
Target: Snapper (soft baits), Kahawai (jigging)

TIMING:
- ✅ Depart: 12:30pm
- ⚓ Return by: 4pm (wind shift forecast)
```

## Adding More Data

### Fishing Reports
1. Find forum posts on https://www.fishing.net.nz/forum/
2. Create file: `fishing_reports/LOCATION_SOURCE.md`
3. Run `ingest_knowledge.py`  
4. Restart streamlit

### Bite Times
1. Visit https://www.fishing.net.nz/fishing-advice/bite-times/
2. Add to `fishing_reports/BITE_TIMES_MANUAL.json`
3. Agent automatically includes in recommendations

### Custom Data
Create any `.md`, `.txt`, or `.pdf` file in `fishing_reports/` and it'll be indexed.

## Troubleshooting

**"No fishing reports found"**
- Add files to `fishing_reports/` folder
- Run `python ingest_knowledge.py`
- Restart streamlit

**"Bite times not appearing"**  
- Check `fishing_reports/BITE_TIMES_MANUAL.json` exists
- Update manual entry with current bite times
- System caches for 24 hours

**Scraper always blocked**
- Website has anti-bot protection (403 Forbidden)
- Use manual entry or install Selenium for browser automation
- Alternative: Use `/fishing-reports/` section on their site directly

## Next Steps

1. **Immediate:** Add 2-3 manual forum reports to `fishing_reports/`
2. **Short-term:** Build up report library (5-10 locations)
3. **Medium-term:** Consider Selenium if you want full automation
4. **Long-term:** Seasonal data, different conditions, pattern analysis

## Developer Notes

### Tools Added to Agent

**FishingReports Tool**
- Searches fishing knowledge base
- Matches weather patterns to historical catches
- Returns location recommendations

**BiteTimesAPI Tool**  
- Fetches live bite times (with fallback to manual cache)
- Returns major/minor bite windows
- Includes sun/moon rise-set times

### Files Modified

- **navigator.py** - Added FishingReports & BiteTimesAPI tools, enhanced prompt
- Created: bite_times_api.py, scrape_fishing_data.py, setup_fishing_integration.py

### Integration Points

The agent now:
1. Checks weather forecast
2. Gets bite times automatically
3. Searches fishing reports for location matches
4. Combines all data in recommendations
5. Always includes safe return timing

## References

- Bite Times: https://www.fishing.net.nz/fishing-advice/bite-times/
- Forum: https://www.fishing.net.nz/forum/
- Fishing Reports: https://www.fishing.net.nz/fishing-reports/
- Māori Fishing Calendar: Available via fishing.net.nz

---

**Status:** System ready with manual data entry. Fork scraper capability with Selenium for full automation.
