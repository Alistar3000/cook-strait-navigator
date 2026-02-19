#!/usr/bin/env python3
"""
FORUM SCRAPER USAGE GUIDE
==========================

The scrape_forum_fishing.py script automatically extracts fishing reports 
from forum URLs you provide. It parses posts and creates markdown files.

QUICK START
-----------

1. SINGLE URL (simplest):
   python scrape_forum_fishing.py --url "https://www.example-forum.com/thread-url"

2. MULTIPLE URLS (from file):
   - Edit forum_urls.txt
   - Add your forum URLs (one per line)
   - Run: python scrape_forum_fishing.py --file forum_urls.txt

3. INTERACTIVE MODE (paste URLs when prompted):
   python scrape_forum_fishing.py
   < Paste URLs one at a time, press Enter for empty line when done >

WHAT IT DOES
------------

For each forum URL provided:
✓ Scrapes all posts from the thread
✓ Extracts fishing information:
  - Species caught (snapper, kahawai, kingfish, etc.)
  - Conditions mentioned (wind, tide, swell)
  - Catch information (numbers, sizes)
  - Location references
✓ Creates markdown files in fishing_reports/
✓ Groups reports by location automatically
✓ Includes links back to original forum threads

OUTPUT FILES
------------

Creates files like:
- fishing_reports/WELLINGTON_FORUM.md
- fishing_reports/KAPITI_FORUM.md
- fishing_reports/SOUNDS_FORUM.md

Each file contains:
- Summary of all reports
- Species compiled from all posts
- Conditions mentioned
- Individual report excerpts with links
- Raw JSON data

NEXT STEPS
----------

After scraping:
1. Run: python ingest_knowledge.py
   (This indexes all the extracted data)

2. Restart Streamlit:
   Ctrl+C to stop
   streamlit run app.py

3. Ask fishing questions in the interface
   The agent will use your forum data

WHAT FORUMS WORK
-----------------

The scraper works with:
✓ fishing.net.nz forum threads
✓ Most PHP-based forums (phpBB, XenForo, vBulletin)
✓ Simple HTML forums
✓ Discussion threads with standard post layouts

It tries multiple selectors to find posts, so it's pretty flexible.

TIPS
----

1. Use COMPLETE THREAD URLs:
   Good: https://www.fishing.net.nz/forum/viewtopic.php?t=12345
   Good: https://forum.com/threads/wellington-fishing-reports/
   Bad: https://www.fishing.net.nz/forum/ (just the forum home)

2. MULTIPLE THREADS:
   If you have 10 forum threads with fishing reports, just add all
   the URLs to forum_urls.txt and run the scraper once. It will
   extract from all of them.

3. HUNDREDS OF REPORTS:
   You mentioned potentially hundreds - the scraper handles this:
   - Feed it all the URLs
   - It extracts everything automatically
   - Creates organized markdown files
   - Agent uses all of it for recommendations

4. UPDATE DATA:
   To add more reports later:
   - Add new URLs to forum_urls.txt
   - Run scraper again
   - Run ingest_knowledge.py again
   - New data is incorporated automatically

TROUBLESHOOTING
---------------

"No reports found"
- Check URL is valid and not behind a login page
- Try opening URL in browser first to verify it works
- Some forums block automated access (403) - use a different forum

"Connection error"
- Check internet connection
- Verify URL is accessible
- Try a different URL

"Very few reports extracted"
- Some forums have unusual post structures
- Try another forum as alternative source
- Manual copy-paste still works for problematic sites

EXAMPLES
--------

Using with fishing.net.nz:

python scrape_forum_fishing.py --file forum_urls.txt

Where forum_urls.txt contains:
https://www.fishing.net.nz/forum/viewtopic.php?t=1234567
https://www.fishing.net.nz/forum/viewtopic.php?t=1234568
https://www.fishing.net.nz/forum/viewtopic.php?t=1234569

Or interactive:

$ python scrape_forum_fishing.py
🎣 FORUM FISHING REPORT SCRAPER
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enter forum URLs to scrape (one per line, empty line to finish):
Example: https://www.fishing.net.nz/forum/viewtopic.php?t=12345

URL: https://www.fishing.net.nz/forum/viewtopic.php?t=99999
URL: https://www.fishing.net.nz/forum/viewtopic.php?t=88888
URL: 
[scraper runs and creates files]

INTEGRATION WITH AGENT
---------------------

Once reports are ingested, the agent:
1. Checks weather forecast
2. Gets bite times
3. Searches YOUR forum reports
4. Combines all data in recommendations

Example:
User: "Best spot for snapper next week?"

Agent: Checks forecast → Tuesday light northerlies
       Gets bite times → Major bite 2-4pm
       Searches reports → "User's forum said Pukerua Bay great in northerlies"
       Response: "Tuesday afternoon at Pukerua Bay, 2-4pm bite window"

This is the complete system you wanted - forum data + weather + bite times.

TECHNICAL DETAILS
-----------------

The scraper:
- Uses BeautifulSoup for parsing
- Supports multiple forum post selectors
- Extracts structured data (species, conditions, catches)
- Creates well-formatted markdown
- Limits to 50 posts per URL (avoid huge downloads)
- Includes source links for verification
- Detects locations automatically

The keyword extraction is pattern-based:
- Species: Looks for common NZ fish names
- Conditions: Parses wind direction, tide state, sea state
- Catches: Extracts numbers, sizes mentioned
- Locations: Matches against known Wellington/Kapiti areas

ENJOY!
-----

You now have a fully automated pipeline:
Forum URLs → Scraper → Markdown files → Ingestion → Agent integration

Feed it URLs, get fishing intelligence. That's it!
"""

if __name__ == "__main__":
    print(__doc__)
