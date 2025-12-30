# Guardian Route → Railway Deployment Checklist

Complete step-by-step guide to deploy your app to Railway.

---

## ✅ Pre-Deployment Checklist

### 1. Run Data Pipeline (Required)

Your app needs these files to exist:

```bash
cd ~/guardian-route
source venv/bin/activate

# Run each script in order:
python scripts/01_download_data.py       # Creates data/raw/crime_raw.csv
python scripts/02_create_spatial_grid.py # Creates data/processed/
python scripts/03_prepare_triplets.py    # Creates crime_triplets.pkl
python scripts/04_train_model.py         # Creates models/trained/
python scripts/06_prepare_network.py     # Creates data/network/
```

**Verify files exist:**
```bash
ls -lh data/raw/crime_raw.csv
ls -lh data/processed/spatial_grid.geojson
ls -lh data/processed/crime_triplets.pkl
ls -lh models/trained/cynet_model.pkl
ls -lh data/network/denver_network.graphml
ls -lh data/network/tile_edge_mapping.pkl
```

All should show file sizes (not "No such file").

---

### 2. Test Locally

```bash
cd ~/guardian-route
source venv/bin/activate

# Install web dependencies
pip install streamlit streamlit-folium

# Run the app
streamlit run app.py
```

**Expected**: Browser opens at `http://localhost:8501`

**Test**:
- Enter origin/destination addresses
- Click "Calculate Safe Route"
- Should show map with routes

**If it works locally** ✅ → Ready to deploy!

---

## 🚀 Deployment Steps

### Step 1: Prepare Git Repository

```bash
cd ~/guardian-route

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Environment
.env
.venv
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Logs
*.log
EOF

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Guardian Route web app"
```

---

### Step 2: Create GitHub Repository

**Option A: Via GitHub.com (Recommended)**

1. Go to https://github.com/new
2. Repository name: `guardian-route`
3. Description: `Safety-weighted routing for Denver using predictive analytics`
4. Visibility: Public or Private (your choice)
5. **DON'T** initialize with README (we already have files)
6. Click **Create repository**

**Option B: Via GitHub CLI** (if you have `gh` installed)

```bash
gh repo create guardian-route --public --source=. --remote=origin --push
```

**Option C: Manual commands**

```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/guardian-route.git
git branch -M main
git push -u origin main
```

---

### Step 3: Deploy to Railway

#### A. Login to Railway

1. Go to https://railway.app
2. Click **Login** → Sign in with GitHub
3. Authorize Railway to access your repositories

#### B. Create New Project

1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Click **Configure GitHub App** (if first time)
4. Give Railway access to `guardian-route` repository
5. Select `guardian-route` from the list

#### C. Configure Deployment

Railway will auto-detect:
- ✅ Dockerfile
- ✅ railway.json config
- ✅ Build settings

**You should see:**
```
Builder: Dockerfile
Start Command: streamlit run app.py --server.port=$PORT...
```

**Click "Deploy"**

#### D. Monitor Deployment

Watch the build logs:
- Building Docker image (2-3 min)
- Installing dependencies (3-5 min)
- Starting app (1 min)

**Total time: 5-10 minutes**

---

### Step 4: Access Your Live App

Once deployed, Railway gives you a URL:

**Format**: `https://guardian-route-production-XXXX.up.railway.app`

**To find it:**
1. Click on your deployment in Railway dashboard
2. Go to **Settings** → **Domains**
3. Copy the Railway-provided URL

**Open the URL** → Your app is LIVE! 🎉

---

## 🔧 Post-Deployment Configuration

### Add Custom Domain (Optional)

**In Railway:**
1. Settings → Domains → Custom Domain
2. Enter your domain: `route.yourdomain.com`
3. Copy the CNAME target

**In GoDaddy:**
1. DNS Management
2. Add CNAME record:
   - Name: `route`
   - Value: `[Railway CNAME from above]`
   - TTL: 600
3. Save

**Wait 10-60 min** for DNS propagation → `route.yourdomain.com` works!

---

### Set Environment Variables (Optional)

If you need custom config:

**In Railway:**
1. Select your project
2. **Variables** tab
3. Add variables:
   ```
   STREAMLIT_SERVER_PORT=8501
   STREAMLIT_SERVER_ADDRESS=0.0.0.0
   ```

---

## 🐛 Troubleshooting

### Issue: "Application failed to start"

**Check logs:**
1. Railway dashboard → Your project → Deployments
2. Click latest deployment → View logs

**Common fixes:**

**Error: "File not found"**
```bash
# Make sure files are committed
git add data/ models/
git commit -m "Add data files"
git push
```

**Error: "Memory limit exceeded"**
- Free tier: 512MB RAM
- Your app needs ~300-400MB
- Should work, but if not:
  - Upgrade to Pro ($5/month)
  - Or reduce data size

**Error: "Port binding failed"**
- Railway sets `$PORT` env var
- Dockerfile already handles this ✅

---

### Issue: "Module not found"

**Fix:** Add to `requirements-web.txt`
```bash
# Edit requirements-web.txt
# Add missing package
git add requirements-web.txt
git commit -m "Add missing dependency"
git push
```

Railway auto-redeploys on push!

---

### Issue: "Geocoding fails"

OSMnx geocoding sometimes times out.

**Workaround:** Use coordinates instead:
- In app sidebar, switch to "Coordinates" input
- Enter lat/lon manually

---

## 🔄 Update Your App

After deployment, to make changes:

```bash
cd ~/guardian-route

# Make your changes to app.py or other files

# Commit and push
git add .
git commit -m "Update: describe your changes"
git push

# Railway auto-deploys! (2-5 min)
```

Watch deployment in Railway dashboard.

---

## 📊 Monitor Usage

**In Railway Dashboard:**

- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: History of all deployments

**Free Tier Limits:**
- 500 hours/month (enough for POC)
- $5 credit included
- ~$0.01/hour after free hours

**Estimate**: Light usage = ~100 hours/month = FREE

---

## ✅ Deployment Checklist Summary

- [ ] Data pipeline completed (6 scripts run)
- [ ] Tested locally with `streamlit run app.py`
- [ ] Created .gitignore
- [ ] Initialized git repo
- [ ] Created GitHub repository
- [ ] Pushed code to GitHub
- [ ] Connected Railway to GitHub
- [ ] Deployed to Railway
- [ ] Tested live URL
- [ ] (Optional) Added custom domain
- [ ] Shared URL with stakeholders! 🎉

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ Live URL loads without errors
✅ Can enter origin/destination
✅ Click "Calculate" generates routes
✅ Map displays with risk heatmap
✅ Routes are visible (green safe, blue fast)

---

## 📱 Share Your App

Once live, share with:

**Format**: `https://guardian-route-production-XXXX.up.railway.app`

**Marketing pitch**:
> "Guardian Route: AI-powered safety routing for Denver. Enter any two addresses and get a route that minimizes crime risk exposure while balancing travel distance."

---

## 🆘 Need Help?

**Railway Support:**
- Discord: https://discord.gg/railway
- Docs: https://docs.railway.app

**GitHub Issues:**
- https://github.com/YOUR_USERNAME/guardian-route/issues

**Or ping me!**

---

## 🚀 Ready to Deploy?

Run this complete sequence:

```bash
# 1. Verify data exists
ls -lh data/processed/crime_triplets.pkl

# 2. Test locally
streamlit run app.py

# 3. Git setup
git init
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
.DS_Store
.env
EOF
git add .
git commit -m "Guardian Route web app"

# 4. Push to GitHub
# (Create repo at github.com/new first)
git remote add origin https://github.com/YOUR_USERNAME/guardian-route.git
git branch -M main
git push -u origin main

# 5. Go to railway.app
# → New Project → Deploy from GitHub → guardian-route → Deploy

# 6. Wait 5-10 minutes → LIVE! 🎉
```

**You got this!** Let me know when it's live and I'll help with any issues.
