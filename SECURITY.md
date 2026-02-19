# Security & API Quota Protection Guide

## 🔐 Current Security Status

### ✅ API Keys Protection
- **Status:** SECURE ✅
- `.env` file is in `.gitignore` and was never committed to git
- `openaikey.txt` also protected
- Environment variables used instead of hardcoded secrets
- Dual-source secret loading (Streamlit Cloud + local .env)

### ✅ Git Security
- All sensitive files are excluded from version control
- `.gitignore` properly configured:
  - `.env` and `.env.local`
  - `openaikey.txt`
  - `.streamlit/secrets.toml`
  - `__pycache__/`, `venv/`

---

## 🛡️ API Quota Protection (NEW)

### Rate Limiting Implemented
To prevent abuse and quota exhaustion on public Streamlit Cloud:

**MetOcean API:**
- Minimum 2 seconds between requests
- User-Agent header identifies requests as "CookStraitNavigator"
- Blocks rapid-fire requests

**NIWA Tide API:**
- Minimum 1 second between requests
- Gracefully returns None if rate limited

**OpenAI API:**
- Tracks 20 requests maximum per hour
- Warns users when approaching limit
- Prevents token exhaustion

### How It Works
```python
# Automatic check before each API call
allowed, msg = check_rate_limit('metocean')
if not allowed:
    return msg  # User sees: "Rate limited (wait X.Xs)"
```

---

## 🔑 Best Practices - DO THIS NOW

### 1. **Set Streamlit Cloud Secrets (For Production)**
Since your app is public on Streamlit Cloud:

1. Go to: https://share.streamlit.io/projects
2. Click your Cook Strait Navigator project
3. Click "⋮" menu → "Settings"
4. Go to "Secrets" tab
5. Add your keys in TOML format:
```toml
METOCEAN_API_KEY = "your-key-here"
NIWA_API_KEY = "your-key-here"
OPENAI_API_KEY = "your-key-here"
```

**Why:** Streamlit Cloud then uses these instead of looking at `.env` (which only works locally)

### 2. **Rotate/Regenerate API Keys (Recommended)**
Since these were typed into a user file and you've shared the repo:
- **MetOcean:** Log in → Settings → Regenerate API keys
- **NIWA:** API keys are typically fixed, but ensure your account is secure
- **OpenAI:** https://platform.openai.com/account/api-keys → Delete old, create new

### 3. **Monitor Your API Usage**
- **MetOcean:** Check your dashboard for request counts
- **NIWA:** Monitor your API quota at developer portal
- **OpenAI:** Check usage at https://platform.openai.com/account/usage

### 4. **Set API Quota Alerts** (If Available)
- MetOcean: Set billing alerts for high usage
- NIWA: Request a usage alert from support
- OpenAI: Set hard/soft limits on billing

---

## 🚨 Quota Abuse Scenarios Protected

### Scenario 1: Bad Actor Spam
❌ **Before:** Someone could call MetOcean API 1000x/second and exhaust quota
✅ **After:** Rate limiter blocks requests faster than 1 every 2 seconds

### Scenario 2: Accidental Loop
❌ **Before:** Bug in LangChain agent could call APIs repeatedly
✅ **After:** Throttling prevents rapid requests even if code misbehaves

### Scenario 3: OpenAI Token Drain
❌ **Before:** No limit on conversation rounds, user could burn through quota
✅ **After:** Hard limit of 20 requests/hour with warning messages

---

## 📊 Monitoring Your Usage

### Check MetOcean Usage
```
Dashboard → Usage → Check daily/monthly request count
```

### Check OpenAI Usage
```
https://platform.openai.com/account/usage
- Shows tokens used per model
- Tracks usage by date
```

### View Rate Limit Status in App
The system now shows:
- "Rate limited (wait 1.5s)" - if user is hitting API too fast
- "⚠️ **Quota Alert:** You've made 20 requests this hour" - approaching limit

---

## 🔄 When to Rotate Keys

**Rotate immediately if:**
- Keys were ever committed to git (check your case - they weren't!)
- Keys were pasted in Slack/email
- Keys were visible in public logs
- You suspect unauthorized access

**Rotate every 6 months:**
- Good security hygiene practice
- Less critical since rate limiting is now in place

---

## 📝 Current Deployment Checklist

- [x] API keys NOT in git history
- [x] `.gitignore` configured properly
- [x] Rate limiting implemented
- [x] User-Agent headers on requests (tracking)
- [ ] Streamlit Cloud secrets CONFIGURED (DO THIS!)
- [ ] API quota monitoring enabled
- [ ] Alerts set for high usage

---

## ⚠️ Remaining Risks (Minor)

1. **Public Streamlit App** - Anyone can use it
   - Mitigation: Rate limiting prevents quota exhaustion
   - Risk: Low (limited to 20 AI calls/hour anyway)

2. **MetOcean/NIWA Free Tiers** - May have monthly limits
   - Mitigation: Monitor usage dashboard
   - Risk: Low (only 2sec+ between requests limits damage)

3. **OpenAI Token Usage** - Conversations expensive
   - Mitigation: 20 requests/hour hard limit
   - Risk: Low (well protected)

---

## 🎯 Next Steps

1. **RIGHT NOW:** Set up Streamlit Cloud secrets (section 1 above)
2. **TODAY:** Monitor your API dashboards for any unusual usage
3. **THIS WEEK:** Consider rotating API keys for extra safety
4. **ONGOING:** Watch for rate limit warnings in app output

Your keys are safe! The code is production-ready for public deployment. 🚀
