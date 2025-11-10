# Railway Deployment Fix for Flask + React

This package contains all the configuration files needed to fix the "Error creating build plan with Railpack" error when deploying your Flask + React app to Railway.

## 📁 File Structure

```
your-github-repo/
├── backend/
│   ├── app.py (your Flask application)
│   ├── requirements.txt (✅ included in this package)
│   ├── .python-version (✅ included in this package)
│   └── .env.example (✅ included in this package)
├── frontend/
│   ├── src/ (your React source code)
│   ├── package.json (your existing file)
│   ├── Caddyfile (✅ included in this package)
│   └── nixpacks.toml (✅ included in this package)
├── .gitignore (✅ included in this package)
└── README.md (this file)
```

## 🚀 Step-by-Step Deployment Guide

### **Step 1: Copy Files to Your Repository**

1. Copy the `backend/` files into your existing backend directory
2. Copy the `frontend/` files into your existing frontend directory
3. Copy `.gitignore` to your repository root
4. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

### **Step 2: Create Railway Project**

1. Go to https://railway.app
2. Click **"+ New Project"** → **"Empty Project"**
3. Rename project: "Zeitec Verifier App"

### **Step 3: Add PostgreSQL Database**

1. In your project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway auto-provisions the database ✅

### **Step 4: Create Backend Service**

1. Click **"+ New"** → **"Empty Service"**
2. Name it: **"Backend"**
3. Click on the Backend service card
4. Go to **Settings** tab:
   
   **a. Connect Repository:**
   - Click "Connect Repo"
   - Select your GitHub repository
   - Choose your branch (main/master)
   
   **b. Set Root Directory:**
   - Scroll to "Root Directory" field
   - Enter: `/backend`
   
   **c. Set Start Command:**
   - Find "Custom Start Command"
   - Enter: `gunicorn app:app --host=0.0.0.0 --port=$PORT`
   
   **d. Configure Watch Paths:**
   - Find "Watch Paths" section
   - Enter: `/backend/**`

5. Go to **Variables** tab and add:
   ```
   PYTHONUNBUFFERED=1
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ALLOWED_ORIGINS=${{Frontend.RAILWAY_PUBLIC_DOMAIN}}
   SECRET_KEY=your-random-secret-key-here
   ```

6. Go to **Settings** → **Networking** → Click **"Generate Domain"**

### **Step 5: Create Frontend Service**

1. Back to project canvas, click **"+ New"** → **"Empty Service"**
2. Name it: **"Frontend"**
3. Click on the Frontend service card
4. Go to **Settings** tab:
   
   **a. Connect Repository:**
   - Click "Connect Repo"
   - Select same repository
   - Same branch
   
   **b. Set Root Directory:**
   - Enter: `/frontend`
   
   **c. Configure Watch Paths:**
   - Enter: `/frontend/**`
   
   (Start command is auto-configured via nixpacks.toml)

5. Go to **Variables** tab and add:
   ```
   VITE_API_URL=https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}
   ```

6. Go to **Settings** → **Networking** → Click **"Generate Domain"**

### **Step 6: Deploy Both Services**

1. Click **"Deploy"** on each service or press `Shift + Enter`
2. Wait for builds to complete (check logs)

## ✅ Verification Checklist

### Backend Verification:
- [ ] Build logs show "Successfully installed Flask gunicorn..."
- [ ] Deploy logs show "Listening at: http://0.0.0.0:XXXX"
- [ ] Visit `https://your-backend.railway.app/health` → Should return `{"status": "healthy"}`
- [ ] Visit `https://your-backend.railway.app/api/test` → Should return success message

### Frontend Verification:
- [ ] Build logs show "npm run build" completing successfully
- [ ] Deploy logs show "Caddy started"
- [ ] Visit your frontend domain → React app loads
- [ ] Browser console has no CORS errors
- [ ] Frontend can communicate with backend API

## 🔧 Configuration Files Explained

### `backend/requirements.txt`
- Lists all Python dependencies
- **MUST include `gunicorn`** for production server
- **MUST include `psycopg2-binary`** for PostgreSQL

### `backend/.python-version`
- Tells Railway to use Python 3.11
- Alternative to setting `RAILPACK_PYTHON_VERSION` env var

### `backend/app.py`
- Example Flask app with proper Railway configuration
- Includes `/health` endpoint (Railway healthcheck)
- CORS configured to work with separate frontend domain
- Binds to `0.0.0.0` for external access

### `frontend/Caddyfile`
- Configures Caddy web server to serve React build
- Serves from `/app/dist` (Vite build output)
- Handles client-side routing (try_files)
- Enables gzip compression

### `frontend/nixpacks.toml`
- Downloads and installs Caddy during build
- Configures start command to run Caddy
- **Critical:** Without this, Railway uses npm dev server (bad!)

## 🐛 Troubleshooting

### Error: "Application failed to respond"
**Fix:** Check that your Flask app binds to `0.0.0.0`:
```python
app.run(host='0.0.0.0', port=port)
```

### Error: "Command not found: gunicorn"
**Fix:** Ensure `gunicorn` is in `requirements.txt`

### Error: CORS errors in browser console
**Fix:** Check backend environment variable `ALLOWED_ORIGINS` matches frontend domain

### Error: Frontend shows blank page
**Fix:** 
1. Check browser console for errors
2. Verify `VITE_API_URL` environment variable is set
3. Ensure Caddy is serving from correct directory

### Build fails on backend
**Fix:**
1. Check `requirements.txt` for typos
2. Ensure Python version is compatible (3.8-3.12)
3. Clear build cache: Add env var `NO_CACHE=1`, deploy, then remove

### Build fails on frontend
**Fix:**
1. Check `package.json` for correct scripts
2. Ensure `npm run build` creates `dist/` folder
3. Verify `nixpacks.toml` and `Caddyfile` are in `/frontend`

## 📊 Railway Dashboard Navigation

**To view logs:**
Service → Click latest deployment → View "Build Logs" or "Deploy Logs"

**To update environment variables:**
Service → Variables tab → Add/Edit → Click "Update Variables"

**To change settings:**
Service → Settings tab → Modify → Changes auto-save

**To redeploy:**
Service → Click "Deploy" button or push to GitHub (auto-deploys)

## 🎯 Key Differences from Failed Deployment

| Old (Failed) | New (Working) |
|--------------|---------------|
| Single service deployment | Two separate services |
| No root directory set | `/backend` and `/frontend` set |
| Railway confused by monorepo | Each service isolated |
| Missing production config | Gunicorn + Caddy configured |
| No watch paths | Prevents cross-service rebuilds |

## 🔐 Security Notes

- **Never commit `.env` files to Git** (included in `.gitignore`)
- Use Railway's environment variables instead
- Change `SECRET_KEY` to a random string in production
- Keep `ALLOWED_ORIGINS` specific (don't use `*` in production)

## 💡 Pro Tips

1. **Use Railway's variable references** (`${{ServiceName.VAR}}`) - they auto-update!
2. **Set watch paths** - prevents unnecessary rebuilds
3. **Always check logs first** when debugging
4. **Test backend alone** before adding frontend
5. **Generate domains** for both services to enable HTTPS

## 📞 Need Help?

- Railway Docs: https://docs.railway.com
- Railway Discord: https://discord.gg/railway
- Check logs in Railway dashboard for specific errors

---

**Success Indicator:** When both services show green "Active" status and you can access both domains! 🎉
