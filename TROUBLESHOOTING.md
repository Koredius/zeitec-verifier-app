# 🆘 Railway Deployment Troubleshooting Quick Reference

## 🔍 How to Read Railway Error Messages

### Where to Find Errors:
1. Click on your service (Backend or Frontend)
2. Click on the latest deployment
3. Check **"Build Logs"** tab (for build errors)
4. Check **"Deploy Logs"** tab (for runtime errors)

---

## ⚡ Quick Fixes by Error Message

### ❌ Error: "Error creating build plan with Railpack"

**What it means:** Railway can't figure out how to build your app

**Immediate Fix:**
1. Go to Service → Settings
2. Set **Root Directory** to `/backend` or `/frontend`
3. Click anywhere to save (auto-saves)
4. Redeploy

---

### ❌ Error: "Application failed to respond"

**What it means:** Your app started but Railway can't connect to it

**Immediate Fix for Flask:**
Check your app.py has:
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)  # ← Must be 0.0.0.0
```

**Immediate Fix for Gunicorn:**
Start command must be:
```
gunicorn app:app --host=0.0.0.0 --port=$PORT
```

---

### ❌ Error: "Command not found: gunicorn"

**What it means:** Gunicorn isn't installed

**Immediate Fix:**
1. Add to `requirements.txt`:
   ```
   gunicorn==21.2.0
   ```
2. Commit and push
3. Railway auto-redeploys

---

### ❌ Error: "No module named 'flask'"

**What it means:** Dependencies didn't install

**Immediate Fix:**
1. Check `requirements.txt` exists in `/backend` directory
2. Check file has correct spelling: `Flask==3.0.0`
3. Verify Root Directory is set to `/backend`
4. Redeploy

---

### ❌ Error: CORS errors in browser console

**What it means:** Backend blocking frontend requests

**Immediate Fix:**
1. Backend → Variables tab
2. Check `ALLOWED_ORIGINS` = `${{Frontend.RAILWAY_PUBLIC_DOMAIN}}`
3. In `app.py`, verify:
   ```python
   from flask_cors import CORS
   CORS(app, origins=[os.getenv('ALLOWED_ORIGINS')])
   ```
4. Redeploy backend

---

### ❌ Error: Frontend shows blank white page

**What it means:** React not loading or API not connecting

**Immediate Fix:**
1. Open browser console (F12)
2. Check for errors:
   
   **If seeing "Failed to fetch":**
   - Frontend → Variables → Check `VITE_API_URL` exists
   - Should be: `https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}`
   
   **If seeing module errors:**
   - Check `npm run build` works locally
   - Verify `package.json` has build script
   - Check frontend Root Directory is `/frontend`

---

### ❌ Error: "Bad Gateway 502"

**What it means:** Service crashed or not responding

**Immediate Fix:**
1. Check Deploy Logs for crash messages
2. Common causes:
   - Missing environment variables
   - Database connection failed
   - App error on startup
3. Look for Python traceback or JavaScript errors in logs

---

### ❌ Error: "Health check timeout"

**What it means:** Railway can't reach your /health endpoint

**Immediate Fix:**
1. Add to Flask app:
   ```python
   @app.route('/health')
   def health():
       return {'status': 'healthy'}, 200
   ```
2. OR temporarily disable health check:
   - Settings → Deploy → Health Check Path → Delete value
3. Redeploy

---

### ❌ Error: "Build failed during npm install"

**What it means:** Node.js can't install packages

**Immediate Fix:**
1. Check `package.json` for typos
2. Delete `package-lock.json` locally
3. Run `npm install` locally to regenerate
4. Commit and push
5. Or add to Frontend variables:
   ```
   NO_CACHE=1
   ```
   Deploy, then remove this variable

---

## 🔧 Universal Troubleshooting Steps

### When Deployment Fails:

**Step 1: Read the FULL logs**
- Scroll through ALL log messages
- Error is often in the middle, not just at bottom
- Look for red text or "ERROR" keywords

**Step 2: Check configuration settings**
- Root Directory set correctly?
- Start Command configured?
- Environment variables present?
- Watch Paths configured?

**Step 3: Verify files exist**
- `backend/requirements.txt` exists?
- `frontend/Caddyfile` exists?
- `frontend/nixpacks.toml` exists?
- Files committed to GitHub?

**Step 4: Test locally**
- Does `pip install -r requirements.txt` work?
- Does `npm run build` work?
- Does `gunicorn app:app` work locally?

**Step 5: Clear cache and retry**
- Add environment variable: `NO_CACHE=1`
- Deploy
- Remove `NO_CACHE=1`
- Deploy again

---

## 🎯 Quick Diagnostic Checklist

### Backend Not Working?
- [ ] `requirements.txt` has `gunicorn`
- [ ] Start command: `gunicorn app:app --host=0.0.0.0 --port=$PORT`
- [ ] Root Directory: `/backend`
- [ ] `/health` endpoint returns 200
- [ ] `DATABASE_URL` variable set
- [ ] `PYTHONUNBUFFERED=1` variable set

### Frontend Not Working?
- [ ] `Caddyfile` exists in `/frontend`
- [ ] `nixpacks.toml` exists in `/frontend`
- [ ] Root Directory: `/frontend`
- [ ] `npm run build` creates `dist/` folder
- [ ] `VITE_API_URL` variable points to backend

### Services Can't Talk to Each Other?
- [ ] Both domains generated
- [ ] Backend has `ALLOWED_ORIGINS=${{Frontend.RAILWAY_PUBLIC_DOMAIN}}`
- [ ] Frontend has `VITE_API_URL=https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}`
- [ ] CORS configured in Flask app

---

## 📞 Still Stuck?

### Check These Resources:
1. **DEPLOYMENT_GUIDE.md** - Full step-by-step instructions
2. **QUICK_START_CHECKLIST.md** - Deployment checklist
3. **Railway Logs** - Always check logs first
4. **Railway Docs** - https://docs.railway.com

### Before Asking for Help:
1. ✅ Read all error messages completely
2. ✅ Check deployment logs (Build + Deploy tabs)
3. ✅ Verify all settings match DEPLOYMENT_GUIDE.md
4. ✅ Try clearing cache (NO_CACHE=1)
5. ✅ Screenshot error messages for support

---

## 💡 Pro Tips

1. **Always check logs FIRST** - 90% of issues are explained in logs
2. **One change at a time** - Don't change multiple things, then you won't know what fixed it
3. **Domain changes take ~30 seconds** - Wait before testing
4. **Variable syntax matters** - Use `${{Service.VAR}}` not `${Service.VAR}`
5. **Commit and push** - Railway only deploys what's in GitHub

---

## 🎊 Success Indicators

### ✅ Backend is Working When:
- Build logs show "Successfully installed..."
- Deploy logs show "Listening at..."
- `https://your-backend.railway.app/health` returns `{"status":"healthy"}`
- No errors in Deploy Logs tab

### ✅ Frontend is Working When:
- Build logs show "npm run build" completed
- Deploy logs show Caddy started
- Website loads in browser
- No CORS errors in browser console

### ✅ Both Services Connected When:
- Frontend can call backend API
- No 502/503 errors
- Browser console shows successful API calls
- Data flows from frontend → backend → database

---

**Remember:** Most deployment issues are simple configuration mistakes. Check Root Directory and Start Command first - they fix 80% of problems!
