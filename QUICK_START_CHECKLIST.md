# Railway Deployment Quick Start Checklist

## ☐ Pre-Deployment (GitHub)

- [ ] Copy all files from this package to your repository
- [ ] Files in `/backend`: requirements.txt, .python-version, .env.example
- [ ] Files in `/frontend`: Caddyfile, nixpacks.toml
- [ ] File at root: .gitignore
- [ ] Commit and push to GitHub

## ☐ Railway Project Setup

- [ ] Create new Railway project (Empty Project)
- [ ] Add PostgreSQL database (+ New → Database → PostgreSQL)

## ☐ Backend Service Configuration

- [ ] Create Empty Service named "Backend"
- [ ] Connect GitHub repository
- [ ] Set Root Directory: `/backend`
- [ ] Set Start Command: `gunicorn app:app --host=0.0.0.0 --port=$PORT`
- [ ] Set Watch Paths: `/backend/**`
- [ ] Add environment variables:
  - [ ] PYTHONUNBUFFERED=1
  - [ ] DATABASE_URL=${{Postgres.DATABASE_URL}}
  - [ ] ALLOWED_ORIGINS=${{Frontend.RAILWAY_PUBLIC_DOMAIN}}
  - [ ] SECRET_KEY=your-secret-key
- [ ] Generate public domain
- [ ] Deploy service

## ☐ Frontend Service Configuration

- [ ] Create Empty Service named "Frontend"
- [ ] Connect same GitHub repository
- [ ] Set Root Directory: `/frontend`
- [ ] Set Watch Paths: `/frontend/**`
- [ ] Add environment variable:
  - [ ] VITE_API_URL=https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}
- [ ] Generate public domain
- [ ] Deploy service

## ☐ Verification Tests

- [ ] Backend build completed successfully
- [ ] Frontend build completed successfully
- [ ] Backend health check works: `/health` endpoint returns 200
- [ ] Frontend loads in browser
- [ ] Frontend can call backend API (no CORS errors)
- [ ] Database connection works

## 🎯 Expected Results

✅ **Backend URL:** `https://your-backend-name.railway.app`
✅ **Frontend URL:** `https://your-frontend-name.railway.app`
✅ **Status:** Both services showing "Active" (green)
✅ **Logs:** No errors in deploy logs
✅ **API Test:** `curl https://your-backend.railway.app/health` returns `{"status":"healthy"}`

## ⏱️ Estimated Time

- Setup: 10-15 minutes
- First deployment: 5-10 minutes
- Total: ~20 minutes

## 🔴 Common Mistakes to Avoid

❌ **Don't** try to deploy as a single service
❌ **Don't** forget to set Root Directory for each service
❌ **Don't** skip the Watch Paths configuration
❌ **Don't** use `npm start` or `flask run` in production
❌ **Don't** forget to generate domains for both services

## 💪 You've Got This!

Follow each checkbox in order, and you'll have a working deployment. If you get stuck, check DEPLOYMENT_GUIDE.md for detailed troubleshooting.
