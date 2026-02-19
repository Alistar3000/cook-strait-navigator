# Using Cook Strait Navigator on Android

Once deployed to Streamlit Cloud, you can access the app from your Android phone via web browser.

## Access the App

1. After deployment, you'll get a URL like:
   ```
   https://cook-strait-navigator-xxxxx.streamlit.app
   ```

2. Open this URL in your Android Chrome browser
3. Bookmark it or add to home screen

## Install as Android App

To make it feel like a native app:

### Chrome Browser (Recommended)

1. Open the Streamlit Cloud URL in Chrome
2. Tap the menu (⋮) in top right
3. Select **"Install app"** or **"Add to Home screen"**
4. Choose a name (e.g., "Navigator")
5. Tap "Install"

Result: 
- App icon appears on home screen
- Launches in fullscreen (like a native app)
- Works offline (partially)

### Firefox Browser

1. Open the URL in Firefox
2. Tap the menu (⋮)
3. Select **"Create Shortcut"**
4. Place on home screen

## Using the App

### Asking Questions

The AI agent understands:

**Weather & Safety:**
- "Is it safe to cross today?"
- "What's the forecast for this weekend?"
- "Wind speed at Mana Island?"

**Fishing:**
- "Best spot to fish on Wednesday?"
- "What are the current bite times?"
- "Recent catches in Wellington?"

**Navigation:**
- "Route to Tory Channel"
- "Conditions at Cape Koamaru"
- "Tell me about Fishermans Rock"

### Vessel Settings

1. Click the hamburger menu (☰) on left
2. Set your vessel information:
   - Boat length (meters)
   - VHF radio status
   - Lifejackets availability

The agent uses this for safety recommendations.

### Chat History

- Clear conversation history: Click "Clear Chat History" in sidebar
- History is stored locally in browser
- Starts fresh each session

## Network Requirements

- **At home:** Works on local WiFi
- **At sea:** Requires 4G/LTE connection
- **Offline:** Navigation tips work offline (pre-loaded)
- **Data usage:** Light (mostly text, minimal images)

## Screen Orientation

The app adapts to:
- Portrait (phone held upright)
- Landscape (phone laid flat)

**Recommended:** Landscape for larger text, easier reading

## Browser Tips

### Data Saving
- Use Lite mode in Chrome to reduce data
- Works great over 4G

### Notifications
- Browser notifications enabled (optional):
  - Chrome → Settings → Notifications → Allow

### Offline Access (Limited)
- Some agent responses cached
- Weather data requires internet
- Full functionality needs connection

## Performance

### On First Load
- May take 10-15 seconds
- Streamlit Cold Starts: Normal for free tier
- Subsequent loads are faster

### Ongoing Use
- Responses: 2-5 seconds (depends on internet)
- Free tier has concurrent user limits
- Paid tier recommended for frequent use

## Troubleshooting

### Page Won't Load
1. Check internet connection
2. Close and reopen the URL
3. Clear browser cache (Chrome Settings → Storage)
4. If still broken, check Streamlit Cloud status

### Slow Performance
- Free Streamlit tier: Limited resources
- Try Landscape mode
- Close other browser tabs
- Upgrade to Streamlit paid tier

### Formatting Issues
- Refresh page (pull down)
- Try different browser (Firefox, Edge)
- Landscape view usually better

### Lost Responses
- Chat history visible on screen
- Can screenshot for reference
- Not automatically saved between sessions

## Advanced: Home Screen Setup

For best Android experience:

1. **Install app** (see Chrome section above)
2. **Customize home screen:**
   - Long-press app icon
   - Select "Edit" or "App info"
   - Change colors/icon if available

3. **Keyboard shortcuts:**
   - Focus text box (tap)
   - Type question
   - Send

## Network Conditions

### Good Connection (5G/Good 4G)
- Instant responses
- Smooth interface
- All features work

### Moderate Connection (4G/WiFi)
- 2-5 second delay on responses
- Occasional timeout (refresh helps)
- Basic features work

### Poor Connection (Edge/3G)
- 10+ second delays likely
- May timeout on complex queries
- Recommend waiting for better signal

## Tips for Boating Use

1. **Waterproof case** - Keep phone dry
2. **Screen brightness** - Max brightness in sunlight
3. **Quick queries** - Keep questions short/specific
4. **Offline prep** - Screenshot important info before heading out
5. **Solar charger** - Battery backup for trips

## Battery Usage

- Similar to web browsing
- Default brightness: ~4-5 hours
- Max brightness: ~2-3 hours
- WiFi uses less battery than 4G

## Share Information

To share information with crew:

1. Take screenshot (Volume Down + Power button)
2. Share via messaging/email
3. Or read query results aloud

## More Help

- Streamlit docs: https://docs.streamlit.io
- Browser help: Chrome/Firefox settings
- Deployment status: Check Streamlit Cloud dashboard
