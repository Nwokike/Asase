# Deploying ASASE to Render

## Prerequisites
1. Create a Render account at https://render.com
2. Have your GitHub repository ready (or connect directly from Render)

## Step 1: Create PostgreSQL Database
1. Go to your Render Dashboard
2. Click "New +" → "PostgreSQL"
3. Name: `asase-db` (or any name you prefer)
4. Region: Choose closest to your users
5. Plan: **Free** (sufficient for development)
6. Click "Create Database"
7. **Copy the Internal Database URL** - you'll need this

## Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your repository
3. Configure the service:

### Basic Settings
- **Name**: `asase-app`
- **Region**: Same as your database
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave blank
- **Runtime**: Python 3
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn --bind=0.0.0.0:5000 --reuse-port asase_project.wsgi:application`

### Environment Settings
- **Plan**: Free (or paid for better performance)

### Environment Variables
Add the following environment variables:

| Key | Value |
|-----|-------|
| `DEBUG` | `False` |
| `SECRET_KEY` | Generate a secure key (use Django's `get_random_secret_key()` or online generator) |
| `DATABASE_URL` | Paste the Internal Database URL from Step 1 |
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `OPENWEATHER_API_KEY` | Your OpenWeather API key |
| `PYTHON_VERSION` | `3.11.13` |

## Step 3: Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your app
3. Wait for the deployment to complete (usually 3-5 minutes)
4. Your app will be live at: `https://asase-app.onrender.com` (or your custom URL)

## Step 4: Run Migrations (First Deploy Only)
After first deployment, if tables aren't created:
1. Go to your web service dashboard
2. Click "Shell" tab
3. Run: `python manage.py migrate`

## Important Notes

### Free Tier Limitations
- **Cold starts**: App spins down after 15 minutes of inactivity
- **Wake up time**: First request after sleep takes 30-60 seconds
- **Database**: 90 days retention, 1GB storage limit

### Production Checklist
- ✅ DEBUG set to False
- ✅ SECRET_KEY is unique and secure
- ✅ DATABASE_URL configured
- ✅ All API keys added
- ✅ Static files configured with WhiteNoise
- ✅ CSRF trusted origins include Render domain

### Custom Domain (Optional)
1. Go to your web service → Settings → Custom Domains
2. Add your domain
3. Update DNS records as instructed
4. Add domain to `CSRF_TRUSTED_ORIGINS` in settings.py

## Troubleshooting

### Build Fails
- Check build logs for errors
- Ensure `requirements.txt` is up to date
- Verify Python version matches

### App Crashes
- Check service logs
- Verify all environment variables are set
- Ensure database migrations ran successfully

### Static Files Not Loading
- Run `python manage.py collectstatic` manually
- Check STATIC_ROOT and STATIC_URL settings
- Verify WhiteNoise is in MIDDLEWARE

## Upgrading to Paid Plan
For production use, consider:
- **Starter Plan ($7/month)**: No cold starts, always-on
- **PostgreSQL Starter ($7/month)**: Better performance, more storage
- **Professional**: Auto-scaling, advanced monitoring
