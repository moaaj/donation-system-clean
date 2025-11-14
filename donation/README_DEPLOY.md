# 🚀 ONE-CLICK DEPLOYMENT TO RENDER

## Method 1: One-Click Deploy Button (EASIEST!)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/YOUR_REPO_NAME)

**Steps:**
1. **Push your code to GitHub** (if not already done)
2. **Click the "Deploy to Render" button above**
3. **Connect your GitHub account**
4. **Click "Deploy"**
5. **Done!** Your app will be live at `yourapp.onrender.com`

## Method 2: Manual Render Deployment

1. **Go to [render.com](https://render.com)**
2. **Sign up/Login**
3. **Click "New +" → "Web Service"**
4. **Connect GitHub repository**
5. **Configure:**
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn donation.wsgi:application`
   - **Environment**: `DJANGO_SETTINGS_MODULE=donation.settings_production`
6. **Deploy!**

## 🔧 What's Included:

✅ **render.yaml** - Automatic configuration
✅ **build.sh** - Build script for dependencies and migrations  
✅ **settings_production.py** - Production-ready settings
✅ **Procfile** - Process configuration
✅ **requirements.txt** - All dependencies

## 🎯 Features:

- **Free PostgreSQL database** included
- **Automatic HTTPS** certificates
- **Auto-deploy** on GitHub push
- **Environment variables** pre-configured
- **Static files** handled automatically

## 🔑 Environment Variables (Auto-configured):

- `DJANGO_SETTINGS_MODULE=donation.settings_production`
- `DJANGO_SECRET_KEY` (auto-generated)
- `DATABASE_URL` (auto-provided by Render)

## 📱 Your Live App:

After deployment, your Django donation system will be available at:
`https://your-app-name.onrender.com`

## 🆘 Need Help?

If deployment fails:
1. Check the build logs in Render dashboard
2. Ensure all files are committed to GitHub
3. Verify requirements.txt is complete

---

**That's it! One-click deployment ready!** 🎉
