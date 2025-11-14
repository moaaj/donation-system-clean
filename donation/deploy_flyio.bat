@echo off
echo 🚀 Deploying to Fly.io for FREE client access...

echo 📦 Step 1: Install Fly CLI
echo Go to: https://fly.io/docs/hands-on/install-flyctl/
echo Download and install flyctl
pause

echo 🔑 Step 2: Login to Fly.io
flyctl auth login

echo 🚀 Step 3: Launch your app
flyctl launch --no-deploy

echo 🐳 Step 4: Deploy with Docker
flyctl deploy

echo ✅ Deployment complete!
echo 🌐 Your client URL: https://django-donation-demo.fly.dev

pause
