#!/usr/bin/env python3
"""
Bite times API - Fetches real-time bite times for fishing locations
Integration point between bite times calendar and agent recommendations
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
import re

class BiteTimesAPI:
    """Fetch and parse bite times from multiple sources"""
    
    def __init__(self):
        # Try multiple bite times sources
        self.sources = [
            {
                'name': 'bitetimes.fishing',
                'url': 'https://www.bitetimes.fishing/bite-times/kapiti-island',
                'region': 'wellington'
            },
            {
                'name': 'fishing.net.nz',
                'url': 'https://www.fishing.net.nz/fishing-advice/bite-times/',
                'region': 'auckland'  # Different region but similar format
            }
        ]
        self.cache_file = Path("fishing_reports/BITE_TIMES_CACHE.json")
        self.cache_duration = 24 * 60 * 60  # 24 hours
    
    def get_bite_times(self, location_lat=None, location_lon=None, days=7):
        """
        Get bite times for a location
        
        Args:
            location_lat: Latitude (currently uses default Wellington area)
            location_lon: Longitude (currently uses default Wellington area)
            days: Number of days to fetch (1-14)
        
        Returns:
            dict: Bite times organized by date
        """
        
        # Try cache first
        cached = self._get_cached_times()
        if cached:
            return cached
        
        # Fetch fresh data - try each source until one works
        for source in self.sources:
            try:
                bite_times = self._fetch_from_source(source)
                if bite_times:
                    self._cache_times(bite_times)
                    return bite_times
            except Exception as e:
                print(f"⚠️  {source['name']} unavailable: {e}")
                continue
        
        # All sources failed, return fallback
        return self._get_fallback_times()
    
    def _fetch_from_source(self, source):
        """Try to fetch from a specific source"""
        return self._fetch_from_website(source['url'])
    
    def _fetch_from_website(self, url=None):
        """Scrape bite times from a website"""
        if not url:
            url = self.sources[0]['url']  # Default to first source
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://www.fishing.net.nz/'
            }
            
            session = requests.Session()
            response = session.get(
                url,  # Use passed URL instead of hardcoded 
                headers=headers, 
                timeout=15,
                allow_redirects=True,
                verify=False  # Some sites require this for scraping
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse day headers and extract bite times
            bite_data = {}
            
            # Look for day headers (Thu 19 Feb, Fri 20 Feb, etc.)
            day_headers = soup.find_all('h5')
            
            for header in day_headers:
                day_text = header.get_text(strip=True)
                
                # Match pattern like "Thu 19 Feb"
                if re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', day_text):
                    
                    # Get parent section for this day
                    parent = header.find_parent()
                    if parent:
                        parent_text = parent.get_text()
                        
                        # Extract Major and Minor bite times
                        major_matches = re.findall(
                            r'Major Bite.*?(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',
                            parent_text,
                            re.DOTALL
                        )
                        
                        minor_matches = re.findall(
                            r'Minor Bite.*?(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',
                            parent_text,
                            re.DOTALL
                        )
                        
                        # Extract sun/moon/tide info
                        sun_match = re.search(r'Rise:\s*(\d{2}):(\d{2}).*?Set:\s*(\d{2}):(\d{2})', parent_text)
                        moon_match = re.search(r'Moon\s+Rise:\s*(\d{2}):(\d{2}).*?Set:\s*(\d{2}):(\d{2})', parent_text)
                        
                        bite_data[day_text] = {
                            'major_bites': major_matches[:2] if major_matches else [],  # Usually 2 major bites
                            'minor_bites': minor_matches[:2] if minor_matches else [],  # Usually 2 minor bites
                            'sun': {
                                'rise': f"{sun_match.group(1)}:{sun_match.group(2)}" if sun_match else None,
                                'set': f"{sun_match.group(3)}:{sun_match.group(4)}" if sun_match else None
                            } if sun_match else None,
                            'moon': {
                                'rise': f"{moon_match.group(1)}:{moon_match.group(2)}" if moon_match else None,
                                'set': f"{moon_match.group(3)}:{moon_match.group(4)}" if moon_match else None
                            } if moon_match else None
                        }
            
            return bite_data if bite_data else None
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"❌ {url} blocked automated access (403 Forbidden)")
                print("💡 This source has anti-bot protection. Trying next source...")
            else:
                print(f"Error fetching from {url}: {e}")
            return None
        except Exception as e:
            print(f"Error scraping website: {e}")
            return None
    
    def _get_cached_times(self):
        """Load bite times from cache if fresh"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    data = json.load(f)
                
                # Check if cache is still fresh
                cached_time = datetime.fromisoformat(data.get('timestamp', ''))
                if (datetime.now() - cached_time).total_seconds() < self.cache_duration:
                    return data.get('bite_times')
        except:
            pass
        
        return None
    
    def _cache_times(self, bite_times):
        """Save bite times to cache"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'bite_times': bite_times
            }
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error caching bite times: {e}")
    
    def _get_fallback_times(self):
        """Fallback bite time data when scraping fails"""
        return {
            "today": {
                "major_bites": [("13", "45", "15", "45"), ("01", "23", "03", "23")],
                "minor_bites": [("05", "20", "08", "20"), ("18", "01", "21", "01")],
                "note": "Fallback data - live fetch failed. Check website for current times."
            }
        }
    
    def format_for_agent(self, bite_times_data):
        """Format bite times data for agent use in recommendations"""
        
        if not bite_times_data:
            return "Bite times unavailable - check https://www.fishing.net.nz/fishing-advice/bite-times/"
        
        formatted = "🎣 BITE TIMES:\n\n"
        
        for day, times in bite_times_data.items():
            formatted += f"**{day}**\n"
            
            if times.get('major_bites'):
                major = times['major_bites']
                if major:
                    # Format first major bite time
                    first = major[0]
                    formatted += f"  🟢 Major Bite: {first[0]}:{first[1]} - {first[2]}:{first[3]}\n"
                    if len(major) > 1:
                        second = major[1]
                        formatted += f"  🟢 Major Bite: {second[0]}:{second[1]} - {second[2]}:{second[3]}\n"
            
            if times.get('minor_bites'):
                minor = times['minor_bites']
                if minor:
                    first = minor[0]
                    formatted += f"  🟡 Minor Bite: {first[0]}:{first[1]} - {first[2]}:{first[3]}\n"
                    if len(minor) > 1:
                        second = minor[1]
                        formatted += f"  🟡 Minor Bite: {second[0]}:{second[1]} - {second[2]}:{second[3]}\n"
            
            if times.get('sun'):
                sun = times['sun']
                if sun.get('rise') and sun.get('set'):
                    formatted += f"  ☀️ Sun: Rise {sun['rise']} | Set {sun['set']}\n"
            
            formatted += "\n"
        
        return formatted


def get_bite_times_for_agent(location="wellington", days=3):
    """
    Convenient function for agent to get bite times
    
    Args:
        location: Location name (wellington, kapiti, etc.)
        days: Number of days to fetch
    
    Returns:
        Formatted string with bite times
    """
    api = BiteTimesAPI()
    bite_times = api.get_bite_times(days=days)
    return api.format_for_agent(bite_times)


if __name__ == "__main__":
    # Test the API
    print("Testing BiteTimesAPI...")
    api = BiteTimesAPI()
    bite_times = api.get_bite_times()
    print(api.format_for_agent(bite_times))
