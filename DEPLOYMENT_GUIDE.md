# Deploy Cook Strait Navigator to Streamlit Cloud

This guide takes you through deploying the Cook Strait Navigator to Streamlit Cloud, making it accessible from your Android phone anywhere.

## Prerequisites

- GitHub account (free at https://github.com)
- Streamlit account (free tier available at https://streamlit.io/cloud)
- OpenAI API key (you already have this in openaikey.txt)

## Step-by-Step Deployment

### Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `cook-strait-navigator`
3. Choose **Public** (required for Streamlit Cloud free tier)
4. Click "Create repository"
5. **Copy the GitHub URL** (looks like: `https://github.com/YOUR-USERNAME/cook-strait-navigator.git`)

### Step 2: Push Your Code to GitHub

Open PowerShell in your project directory and run these commands:

```powershell
# Initialize git (only first time)
git init

# Add your GitHub URL
git remote add origin https://github.com/YOUR-USERNAME/cook-strait-navigator.git

# Configure git (first time setup)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files
git add .

# Commit
git commit -m "Initial commit: Cook Strait Navigator"

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Sign in with your GitHub account (if not already)
4. Select:
   - Repository: `YOUR-USERNAME/cook-strait-navigator`
   - Branch: `main`
   - Main file path: `app.py`
5. Click "Deploy"
6. Wait 2-3 minutes for deployment to complete

### Step 4: Add Your OpenAI Key to Streamlit Secrets

1. After deployment, your app will be live at a URL like:
   `https://cook-strait-navigator-xxxxx.streamlit.app`

2. Click the "Settings" button (gear icon) in the top-right corner
3. Click "Secrets"
4. Add your OpenAI key:
   ```
   OPENAI_API_KEY=sk-xxxxxxxxxxxxx
   ```
5. Click "Save"

**⚠️ IMPORTANT:** Never push `openaikey.txt` to GitHub. The `.gitignore` file prevents this, but always verify secrets are added in Streamlit Cloud's Settings, not in code.

### Step 5: Access from Your Android Phone

1. Your app is now live at: `https://cook-strait-navigator-xxxxx.streamlit.app`
2. Open this URL in your Android browser
3. Bookmark it for easy access
4. The native interface will work like an app on your phone

## Android App-Like Experience

To make it feel more like an app:

**on your phone:**
1. Open the URL in Chrome
2. Tap the menu (⋮) → "Install app" or "Add to Home screen"
3. It will appear as an icon and launch in fullscreen

## Future Updates

After you make changes locally:

```powershell
git add .
git commit -m "Your description of changes"
git push origin main
```

Streamlit Cloud will automatically redeploy within 1-2 minutes.

## Troubleshooting

### App won't load
- Check Streamlit Cloud logs (click "Manage app" → "Logs")
- Ensure `openaikey.txt` is NOT in the repo
- Verify OPENAI_API_KEY is added in Secrets

### OpenAI key errors
- Make sure it's saved in Streamlit Cloud Settings
- The app reads from environment variables, not file

### Slow performance
- Free tier has resource limits
- Vectordb might need optimization for large datasets
- Consider Streamlit's paid tier if needed

## Upgrading Later

To move from free to paid Streamlit Cloud:
1. Go to your deployed app
2. Click "Settings" → "App plan"
3. Choose your plan

## More Information

- Streamlit Cloud docs: https://docs.streamlit.io/deploy/streamlit-cloud
- GitHub setup: https://docs.github.com/en/get-started/quickstart
