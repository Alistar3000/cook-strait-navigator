# Cook Strait Navigator 🌊⛵

An intelligent navigation and fishing intelligence system for Cook Strait, New Zealand. Combines real-time weather/tide data, bite times, and forum fishing reports to provide comprehensive recommendations.

## Features

- 🌦️ **Weather & Tide Forecasts** - Real-time weather data and tidal predictions for Cook Strait area
- 🎣 **Fish Bite Times** - Optimal bite time predictions with multi-source data
- 🗺️ **Location Intelligence** - Wellington, Kapiti Coast, Sounds, and surrounding areas
- 💬 **AI Agent** - LangChain ReAct agent with OpenAI GPT-4o
- 📱 **Mobile Friendly** - Access from Android phone anywhere via Streamlit Cloud
- 🧠 **Vector Database** - ChromaDB for intelligent search across fishing knowledge

## Quick Start

### Local Development

```bash
# Clone repo
git clone https://github.com/YOUR-USERNAME/cook-strait-navigator.git
cd cook-strait-navigator

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Add your OpenAI API key
echo "sk-your-api-key-here" > openaikey.txt

# Run the app
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

### Deploy to Streamlit Cloud

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions.

Once deployed, access from Android phone at the provided Streamlit Cloud URL.

## Project Structure

```
cook-strait-navigator/
├── app.py                          # Main Streamlit interface
├── navigator.py                    # LangChain agent with 5 tools
├── bite_times_api.py              # Bite times fetcher (multi-source)
├── scrape_forum_fishing.py        # Forum scraper with pagination
├── ingest_knowledge.py            # Load fishing/maritime PDFs
├── requirements.txt               # Python dependencies
├── DEPLOYMENT_GUIDE.md            # How to deploy to Streamlit Cloud
├── books/                         # PDF maritime & fishing knowledge
├── fishing_reports/               # Scraped forum reports (markdown)
└── chroma_db/                     # Vector database
```

## Agent Tools

The AI agent has 5 integrated tools:

1. **WeatherTideAPI** - Forecast weather & tides for any location
2. **WebConsensus** - Search DuckDuckGo for current information
3. **LocalKnowledge** - Semantic search over local fishing/maritime PDFs
4. **FishingReports** - Search extracted forum fishing data
5. **BiteTimesAPI** - Get optimal fishing times

## Technologies

- **Framework:** Streamlit (web UI)
- **AI:** LangChain + OpenAI GPT-4o
- **Scraping:** Selenium + BeautifulSoup (with undetected-chromedriver for Cloudflare bypass)
- **Vector DB:** ChromaDB with OpenAI embeddings
- **Data:** Real fishing reports + maritime knowledge PDFs

## Demo

Ask the agent questions like:

- "Best place to fish Wednesday in Wellington?"
- "What are conditions like at Kapiti this week?"
- "When's the next good snapper bite?"
- "Tell me about recent catches in the Sounds"

## Environment Variables

Create `.env` or use Streamlit Cloud Secrets:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
```

## Known Limitations

- Some forums (fishing.net.nz) use Cloudflare Turnstile that requires additional handling
- Free Streamlit tier has resource/bandwidth limits
- Vectordb scales with knowledge base size

## Future Enhancements

- Mobile app wrapper (React Native)
- Tide prediction model improvements
- More forum sources & automated scraping
- Historical catch data analysis
- Recommendation learning from user feedback

## License

MIT

## Author

Built for New Zealand boating & fishing enthusiasts

## Support

For deployment help, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
