# Render Deployment Guide

This guide will help you deploy the ChefAI project to the Render platform.

## Prerequisites

1. Render account (free account is sufficient)
2. GitHub repository (push your code to GitHub)

## Deployment Steps

### 1. Prepare Code Repository

Make sure your code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create Services on Render

#### Method 1: Using render.yaml (Recommended)

1. Log in to Render Dashboard
2. Click "New" -> "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file and create all services

#### Method 2: Manual Service Creation

##### Create Database

1. In Render Dashboard, click "New" -> "PostgreSQL"
2. Database name: `chefai-db`
3. Select free plan
4. Record the database connection string

##### Create Backend Service

1. Click "New" -> "Web Service"
2. Connect your GitHub repository
3. Configure as follows:
   - **Name**: `chefai-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r chefAI-backend/requirements.txt`
   - **Start Command**: `cd chefAI-backend && gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Root Directory**: `/` (project root directory)

4. Add environment variables:
   - `SECRET_KEY`: Generate a random key (you can use `openssl rand -hex 32`)
   - `GEMINI_API_KEY`: Your Gemini API key
   - `DATABASE_URI`: Connection string copied from database service
   - `ALLOWED_ORIGINS`: Frontend URL (update after deploying frontend)

##### Create Frontend Service

1. Click "New" -> "Web Service"
2. Connect your GitHub repository
3. Configure as follows:
   - **Name**: `chefai-frontend`
   - **Environment**: `Node`
   - **Build Command**: `cd chefAI-frontend && npm install && npm run build`
   - **Start Command**: `cd chefAI-frontend && npm run preview`
   - **Root Directory**: `/` (project root directory)

4. Add environment variables:
   - `VITE_API_URL`: Backend service URL (e.g., `https://chefai-backend.onrender.com`)

### 3. Update CORS Configuration

After deploying the frontend, update the backend environment variable `ALLOWED_ORIGINS` to the frontend URL:
```
ALLOWED_ORIGINS=https://your-frontend-url.onrender.com
```

### 4. Verify Deployment

1. Visit the frontend URL, you should see the application
2. Try registering/logging in
3. Test the recipe generation feature

## Environment Variables

### Backend Environment Variables

- `SECRET_KEY`: Flask session secret key (required)
- `GEMINI_API_KEY`: Google Gemini API key (optional, will use mock data if not provided)
- `DATABASE_URI`: Database connection string (Render will provide automatically)
- `ALLOWED_ORIGINS`: Allowed frontend domains, comma-separated

### Frontend Environment Variables

- `VITE_API_URL`: Complete URL of the backend API

## Important Notes

1. **Free Plan Limitations**:
   - Services will sleep after 15 minutes of inactivity
   - First access may require waiting for service startup (about 30-60 seconds)

2. **Database**:
   - Use PostgreSQL (provided free by Render)
   - SQLite is not recommended for production environments

3. **CORS**:
   - Ensure `ALLOWED_ORIGINS` includes the frontend URL
   - Do not include trailing slashes

4. **API Keys**:
   - Do not hardcode API keys in code
   - Use Render's environment variable feature

## Troubleshooting

### Backend Won't Start
- Check if `requirements.txt` includes all dependencies
- View error messages in Render logs
- Ensure `startCommand` is correct

### CORS Errors
- Check the `ALLOWED_ORIGINS` environment variable
- Ensure the frontend URL is correct (including protocol https://)

### Database Connection Errors
- Check the `DATABASE_URI` environment variable
- Ensure the database service is created and running

## Updating Deployment

Every time you push code to GitHub, Render will automatically redeploy. You can also manually trigger deployment in the Render Dashboard.
