# Guardian Route - Web Deployment Guide

Deploy your safety routing app as a live web POC in 3 ways:

---

## 🚀 Option 1: Streamlit Cloud (Recommended - FREE)

**Easiest deployment. Live in 10 minutes.**

### Prerequisites
- GitHub account
- Run the data pipeline once locally (to generate model files)

### Step 1: Test Locally First

```bash
cd ~/guardian-route
source venv/bin/activate

# Install web dependencies
pip install streamlit streamlit-folium

# Run locally
streamlit run app.py
```

Opens at `http://localhost:8501` - test that it works!

### Step 2: Push to GitHub

```bash
cd ~/guardian-route

# Initialize git (if not already)
git init

# Create .gitignore
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
.DS_Store
*.ipynb_checkpoints
EOF

# Add files
git add .
git commit -m "Initial commit - Guardian Route web app"

# Create GitHub repo (via GitHub.com) then:
git remote add origin https://github.com/YOUR_USERNAME/guardian-route.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud

1. Go to https://streamlit.io/cloud
2. Click "New app"
3. Connect your GitHub account
4. Select:
   - **Repository**: `YOUR_USERNAME/guardian-route`
   - **Branch**: `main`
   - **Main file**: `app.py`
   - **Requirements file**: `requirements-web.txt`
5. Click "Deploy"

**Wait 5-10 minutes** → Your app is live!

You'll get a URL like: `https://your-app.streamlit.app`

### Troubleshooting Streamlit Cloud

**Error: "File not found"**
→ Make sure data files are committed to git:
```bash
git lfs track "*.pkl"
git lfs track "*.graphml"
git add data/ models/
git commit -m "Add data files"
git push
```

**Error: "Memory limit exceeded"**
→ Reduce model/data size or upgrade to paid tier

---

## 🐳 Option 2: Docker + Railway/Render (FREE Tier)

**More control, still easy deployment.**

### Create Dockerfile

```bash
cat > ~/guardian-route/Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-web.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy app
COPY . .

# Expose port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF
```

### Test Docker Locally

```bash
cd ~/guardian-route

# Build image
docker build -t guardian-route .

# Run container
docker run -p 8501:8501 guardian-route
```

Visit `http://localhost:8501`

### Deploy to Railway.app

1. Go to https://railway.app
2. Sign up (free tier: 500 hours/month)
3. Click "New Project" → "Deploy from GitHub"
4. Select `guardian-route` repo
5. Railway auto-detects Dockerfile
6. Click "Deploy"

**Live URL**: `https://your-app.railway.app`

### Alternative: Deploy to Render.com

1. Go to https://render.com
2. Sign up (free tier available)
3. Click "New" → "Web Service"
4. Connect GitHub repo
5. Configure:
   - **Build Command**: (leave empty, uses Dockerfile)
   - **Start Command**: (leave empty, uses Dockerfile CMD)
6. Click "Create Web Service"

---

## 💻 Option 3: Flask App (More Control)

**For production deployment with custom domain.**

### Create Flask App

I can build a Flask version with:
- RESTful API backend
- Custom HTML/CSS/JS frontend
- Better performance
- More customization

Let me know if you want the Flask version!

---

## 📊 Comparison

| Method | Cost | Ease | Speed | Control |
|--------|------|------|-------|---------|
| **Streamlit Cloud** | Free | ⭐⭐⭐⭐⭐ | Fast | Low |
| **Railway/Render** | Free tier | ⭐⭐⭐⭐ | Medium | Medium |
| **Flask + Heroku/AWS** | Paid | ⭐⭐⭐ | Slow | High |

---

## 🎯 Recommended Quick Deploy

```bash
# 1. Test locally
cd ~/guardian-route
source venv/bin/activate
pip install streamlit streamlit-folium
streamlit run app.py

# 2. Push to GitHub
git init
git add .
git commit -m "Guardian Route web app"
# Create repo on GitHub.com
git remote add origin https://github.com/YOUR_USERNAME/guardian-route.git
git push -u origin main

# 3. Deploy to Streamlit Cloud
# Visit: https://streamlit.io/cloud
# Click "New app" → Select repo → Deploy
```

**10 minutes later**: Live web app! 🎉

---

## 🔧 Configuration

### Environment Variables

For production, you may want to set:

```bash
# .streamlit/secrets.toml (don't commit to git!)
[general]
data_path = "/app/data"
model_path = "/app/models"
```

### Custom Domain

**Streamlit Cloud**:
- Paid plan required
- Settings → Custom domain

**Railway/Render**:
- Free tier supports custom domains
- Add DNS CNAME record

---

## 📈 Performance Optimization

### For Large Files

Use Git LFS for model files:

```bash
git lfs install
git lfs track "*.pkl"
git lfs track "*.graphml"
git add .gitattributes
git commit -m "Add LFS tracking"
```

### Caching

The app uses `@st.cache_resource` to cache:
- Model loading
- Network loading
- Tile mapping

This makes it fast after first load!

---

## 🐛 Common Deployment Issues

### Issue: "Module not found"
**Solution**: Add missing package to `requirements-web.txt`

### Issue: "Data files not found"
**Solution**: Commit data files or use Git LFS

### Issue: "App crashes on startup"
**Solution**: Check logs in deployment platform

### Issue: "Slow performance"
**Solution**:
- Reduce tile count
- Use smaller network area
- Upgrade to paid tier

---

## 🎨 Customization

### Change Branding

Edit `app.py`:
```python
st.set_page_config(
    page_title="Your App Name",
    page_icon="🚗",  # Change icon
)
```

### Change Theme

Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF6B6B"  # Your color
```

---

## 📚 Next Steps

After deploying:

1. **Test thoroughly** with different addresses
2. **Monitor usage** in deployment platform
3. **Gather feedback** from users
4. **Iterate** on features

**Share your live URL!**

---

## 🆘 Need Help?

- Streamlit docs: https://docs.streamlit.io
- Railway docs: https://docs.railway.app
- Render docs: https://render.com/docs

Or ping me for the Flask version!
