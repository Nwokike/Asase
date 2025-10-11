# ASASE Deployment Guide for Render

## Overview
This guide will help you deploy the ASASE Environmental Intelligence Platform to Render with a free PostgreSQL database.

## Prerequisites
1. A Render account (free tier available at https://render.com)
2. Your Gemini API key
3. Your OpenWeather API key

## Quick Deploy Steps

### 1. Push to GitHub (if not already done)
```bash
git init
git add .
git commit -m "Initial commit - ASASE platform"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Deploy to Render

#### Option A: Using the Render Blueprint (Recommended)
1. Go to https://render.com/
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Apply" to create all services

#### Option B: Manual Setup
1. **Create PostgreSQL Database:**
   - Click "New" → "PostgreSQL"
   - Name: `asase-db`
   - Plan: Free
   - Click "Create Database"
   - Copy the "Internal Database URL" for later

2. **Create Web Service:**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Name: `asase-platform`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn asase_project.wsgi:application --bind 0.0.0.0:$PORT`
   
3. **Configure Environment Variables:**
   Add these environment variables in the Render dashboard:
   ```
   PYTHON_VERSION=3.11.0
   DATABASE_URL=[paste your PostgreSQL Internal Database URL]
   GEMINI_API_KEY=[your Gemini API key]
   OPENWEATHER_API_KEY=[your OpenWeather API key]
   SECRET_KEY=[generate a random secret key]
   DEBUG=False
   ALLOWED_HOSTS=.onrender.com
   ```

4. **Generate a SECRET_KEY:**
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

### 3. Deploy
- Click "Create Web Service" (or "Deploy latest commit")
- Wait for the build to complete (5-10 minutes)
- Your app will be live at: `https://asase-platform.onrender.com`

## Post-Deployment

### Run Database Migrations
After first deployment, you need to run migrations:

1. Go to your web service dashboard
2. Click "Shell" tab
3. Run:
   ```bash
   python manage.py migrate
   ```

### Create Superuser (Optional)
To access Django admin:
```bash
python manage.py createsuperuser
```

## Architecture

### Database Configuration
The app uses different databases for different environments:
- **Development**: SQLite (local testing)
- **Production**: PostgreSQL (Render free tier)

This is automatically configured in `settings.py`:
```python
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config()
else:
    # SQLite for development
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
```

### Static Files
Static files are served using WhiteNoise middleware, which is configured automatically.

## Monitoring

### Check Logs
- Go to your Render dashboard
- Click on your web service
- Click "Logs" tab
- Monitor for any errors

### Common Issues

**Issue: App won't start**
- Check that all environment variables are set
- Verify DATABASE_URL is correct
- Check logs for specific errors

**Issue: Static files not loading**
- Run `python manage.py collectstatic --no-input` in Shell
- Check STATIC_ROOT setting

**Issue: Database connection errors**
- Verify DATABASE_URL is the "Internal Database URL"
- Make sure database and web service are in the same region

## Free Tier Limits
- PostgreSQL: 1GB storage, expires after 90 days (renew for free)
- Web Service: 750 hours/month, sleeps after 15 minutes of inactivity
- Note: First request after sleep may take 30-60 seconds

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection URL from Render |
| GEMINI_API_KEY | Yes | Google Gemini API key for AI analysis |
| OPENWEATHER_API_KEY | Yes | OpenWeather API key for weather data |
| SECRET_KEY | Yes | Django secret key (generate random) |
| DEBUG | No | Set to False for production |
| ALLOWED_HOSTS | No | Set to .onrender.com |

## Support
For issues with Render deployment, see: https://docs.render.com/
For ASASE app issues, check the application logs in the Render dashboard.
