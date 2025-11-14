# Django App Deployment Guide - Railway

This guide will help you deploy your Django donation management system to Railway (free hosting).

## Prerequisites

1. **GitHub Account**: Your code needs to be in a GitHub repository
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **Environment Variables**: Prepare your production environment variables

## Step 1: Prepare Your Repository

1. **Create a GitHub repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git push -u origin main
   ```

2. **Ensure all deployment files are in place**:
   - ✅ `Procfile` - Process configuration
   - ✅ `requirements.txt` - Python dependencies
   - ✅ `runtime.txt` - Python version
   - ✅ `railway.json` - Railway configuration
   - ✅ `nixpacks.toml` - Build configuration

## Step 2: Deploy to Railway

1. **Sign up/Login to Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign up with your GitHub account

2. **Create a new project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add PostgreSQL Database**:
   - In your Railway project dashboard
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically provide `DATABASE_URL`

## Step 3: Configure Environment Variables

In your Railway project settings, add these environment variables:

### Required Variables:
```
DEBUG=False
DJANGO_SECRET_KEY=your-super-secret-key-generate-a-new-one
ALLOWED_HOSTS=.railway.app,.up.railway.app
```

### Email Configuration:
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Payment Integration (Optional):
```
STRIPE_TEST_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_TEST_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### Site Configuration:
```
SITE_DOMAIN=your-app-name.up.railway.app
SITE_NAME=Donation System
```

## Step 4: Generate Django Secret Key

Generate a new secret key for production:

```python
# Run this in Python shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## Step 5: Deploy and Test

1. **Trigger Deployment**:
   - Push changes to your GitHub repository
   - Railway will automatically deploy

2. **Monitor Deployment**:
   - Check Railway dashboard for build logs
   - Wait for deployment to complete

3. **Create Superuser** (after first deployment):
   - In Railway dashboard, go to your service
   - Open "Deploy" tab → "View Logs"
   - Use Railway CLI or run commands in the dashboard

## Step 6: Post-Deployment Setup

1. **Create Admin User**:
   ```bash
   # Using Railway CLI (install first: npm install -g @railway/cli)
   railway login
   railway run python manage.py createsuperuser
   ```

2. **Test Your Application**:
   - Visit your Railway app URL
   - Test login functionality
   - Verify database connections
   - Test payment integration (if configured)

## Troubleshooting

### Common Issues:

1. **Static Files Not Loading**:
   - Ensure `STATIC_ROOT` is set correctly
   - Check WhiteNoise configuration
   - Run `python manage.py collectstatic`

2. **Database Connection Errors**:
   - Verify `DATABASE_URL` is set by Railway
   - Check PostgreSQL service is running

3. **Environment Variables**:
   - Double-check all required variables are set
   - Ensure no typos in variable names

4. **Build Failures**:
   - Check `requirements.txt` for compatibility
   - Review build logs in Railway dashboard

### Useful Railway CLI Commands:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Run commands on Railway
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py collectstatic

# View logs
railway logs
```

## Alternative Free Hosting Options

If Railway doesn't work for you, consider these alternatives:

1. **Render** (render.com) - Similar to Railway
2. **Heroku** (heroku.com) - Classic PaaS (limited free tier)
3. **PythonAnywhere** (pythonanywhere.com) - Python-focused hosting
4. **Vercel** (vercel.com) - Good for static sites, limited Django support

## Security Notes

- Never commit sensitive data to GitHub
- Use environment variables for all secrets
- Enable HTTPS in production (Railway provides this automatically)
- Regularly update dependencies
- Monitor your application logs

## Support

If you encounter issues:
1. Check Railway documentation
2. Review Django deployment best practices
3. Check the application logs for specific error messages

Your Django donation management system should now be live and accessible via your Railway URL!
