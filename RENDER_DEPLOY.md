# Render Quick Deployment Guide

## 🚀 Quick Start

### Method 1: Using Blueprint (Recommended, Easiest)

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Create Blueprint on Render**
   - Log in to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically read `render.yaml` and create all services

3. **Configure Environment Variables**
   
   In the `chefai-backend` service, set:
   - `GEMINI_API_KEY`: Your Gemini API key (optional)
   - `ALLOWED_ORIGINS`: Frontend URL (set after deploying frontend, e.g., `https://chefai-frontend.onrender.com`)
   
   In the `chefai-frontend` service, set:
   - `VITE_API_URL`: Backend URL (e.g., `https://chefai-backend.onrender.com`)

4. **Wait for Deployment to Complete**
   - Database will be created automatically
   - Backend and frontend will be built and deployed automatically

### Method 2: Manual Service Creation

#### Step 1: Create PostgreSQL Database

1. Render Dashboard → "New" → "PostgreSQL"
2. Name: `chefai-db`
3. Plan: Free
4. After creation, copy the connection string

#### Step 2: Create Backend Service

1. Render Dashboard → "New" → "Web Service"
2. Connect GitHub repository
3. Settings:
   - **Name**: `chefai-backend`
   - **Root Directory**: `/` (leave empty)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r chefAI-backend/requirements.txt`
   - **Start Command**: `cd chefAI-backend && gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app`

4. Environment variables:
   ```
   SECRET_KEY=<generate random key>
   GEMINI_API_KEY=<your Gemini API key>
   DATABASE_URI=<connection string copied from database service>
   ALLOWED_ORIGINS=https://chefai-frontend.onrender.com
   ```

#### Step 3: Create Frontend Service

1. Render Dashboard → "New" → "Web Service"
2. Connect GitHub repository
3. Settings:
   - **Name**: `chefai-frontend`
   - **Root Directory**: `/` (leave empty)
   - **Environment**: `Node`
   - **Build Command**: `cd chefAI-frontend && npm install && npm run build`
   - **Start Command**: `cd chefAI-frontend && npm run preview`

4. Environment variables:
   ```
   VITE_API_URL=https://chefai-backend.onrender.com
   ```

## 📝 Important Notes

1. **Update CORS After First Deployment**
   - After deploying frontend, copy the frontend URL
   - Update `ALLOWED_ORIGINS` in backend service environment variables

2. **Generate SECRET_KEY**
   ```bash
   openssl rand -hex 32
   ```

3. **Free Plan Limitations**
   - Services will sleep after 15 minutes of inactivity
   - First access requires waiting about 30-60 seconds for startup

4. **Database Migration**
   - Database tables will be created automatically on first deployment
   - If you encounter issues, check backend logs

## 🔧 Troubleshooting

### Backend Startup Failure
- Check if `requirements.txt` includes all dependencies
- View Render logs
- Ensure Python version is correct (3.11.0)

### CORS Errors
- Ensure `ALLOWED_ORIGINS` includes the complete frontend URL (including `https://`)
- Do not include trailing slashes

### Frontend Cannot Connect to Backend
- Check if `VITE_API_URL` is correct
- Ensure backend service is running
- Check browser console for error messages

### Database Connection Errors
- Check if `DATABASE_URI` is correct
- Ensure database service is created
- Check if database is running

## 📚 More Information

For detailed deployment instructions, see `DEPLOY.md`
