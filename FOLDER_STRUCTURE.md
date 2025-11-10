# 📁 Complete Folder Structure After Setup

## Your GitHub Repository Structure

```
zeitec-verifier-app/                    ← Your repository root
│
├── backend/                             ← Flask Backend
│   ├── app.py                          ✅ (updated with Railway config)
│   ├── requirements.txt                ✅ (from this package)
│   ├── .python-version                 ✅ (from this package)
│   ├── .env.example                    ✅ (from this package)
│   └── (your other Flask files...)
│
├── frontend/                            ← React Frontend
│   ├── src/                            (your React source code)
│   ├── public/                         (your public assets)
│   ├── package.json                    (your existing file)
│   ├── vite.config.js or similar       (your build config)
│   ├── Caddyfile                       ✅ (from this package - CRITICAL!)
│   ├── nixpacks.toml                   ✅ (from this package - CRITICAL!)
│   └── (your other React files...)
│
├── .gitignore                          ✅ (from this package)
├── DEPLOYMENT_GUIDE.md                 ✅ (reference documentation)
├── QUICK_START_CHECKLIST.md            ✅ (step-by-step checklist)
└── README.md                           (your project readme)
```

## ✅ Files You MUST Add/Update

### Backend Files (in `/backend` directory):
1. **requirements.txt** - Replace or merge with yours
2. **.python-version** - Add this file
3. **.env.example** - Add for reference
4. **app.py** - Update to include health endpoint and proper CORS

### Frontend Files (in `/frontend` directory):
1. **Caddyfile** - Add this file (CRITICAL!)
2. **nixpacks.toml** - Add this file (CRITICAL!)

### Root Directory Files:
1. **.gitignore** - Add or merge with existing

## 🎯 Railway Project Structure (After Deployment)

```
Zeitec Verifier App (Railway Project)
│
├── 🗄️ Postgres                          ← Database Service
│   └── Auto-generated connection variables
│
├── 🐍 Backend                          ← Flask Service
│   ├── Source: GitHub repo
│   ├── Root Directory: /backend
│   ├── Start Command: gunicorn app:app...
│   ├── Public Domain: backend-xyz.railway.app
│   └── Environment Variables:
│       - DATABASE_URL → ${{Postgres.DATABASE_URL}}
│       - ALLOWED_ORIGINS → ${{Frontend.RAILWAY_PUBLIC_DOMAIN}}
│       - PYTHONUNBUFFERED=1
│       - SECRET_KEY
│
└── ⚛️ Frontend                         ← React Service
    ├── Source: GitHub repo (same repo!)
    ├── Root Directory: /frontend
    ├── Start Command: ./caddy run... (from nixpacks.toml)
    ├── Public Domain: frontend-xyz.railway.app
    └── Environment Variables:
        - VITE_API_URL → ${{Backend.RAILWAY_PUBLIC_DOMAIN}}
```

## 🔄 Data Flow Architecture

```
User Browser
    ↓
    ↓ HTTPS
    ↓
Frontend Service (Caddy serving React build)
    │ Domain: frontend-xyz.railway.app
    │ Files: /app/dist/index.html, etc.
    │
    ↓ API Calls
    ↓ (VITE_API_URL environment variable)
    ↓
Backend Service (Gunicorn serving Flask)
    │ Domain: backend-xyz.railway.app
    │ Endpoints: /health, /api/*, etc.
    │ CORS: Allows Frontend domain
    │
    ↓ Database Queries
    ↓ (DATABASE_URL environment variable)
    ↓
PostgreSQL Database
    │ Private connection within Railway
    │ Data: registrants, devices, etc.
```

## 🚦 Environment Variable Flow

```
Railway Internal Variable References:

Backend Service needs Frontend domain:
    ALLOWED_ORIGINS = ${{Frontend.RAILWAY_PUBLIC_DOMAIN}}
                            ↓
                    Automatically resolves to:
                    "frontend-xyz.railway.app"

Frontend Service needs Backend domain:
    VITE_API_URL = https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}
                            ↓
                    Automatically resolves to:
                    "https://backend-xyz.railway.app"

Backend Service needs Database:
    DATABASE_URL = ${{Postgres.DATABASE_URL}}
                            ↓
                    Automatically resolves to:
                    "postgresql://user:pass@host:port/db"
```

## 📦 What Gets Deployed Where

### Backend Deployment:
```
Railway clones: /backend directory
Railway installs: pip install -r requirements.txt
Railway runs: gunicorn app:app --host=0.0.0.0 --port=$PORT
Result: Flask API running on assigned port
Access: https://backend-xyz.railway.app
```

### Frontend Deployment:
```
Railway clones: /frontend directory
Railway installs: npm install
Railway builds: npm run build → creates /dist folder
Railway downloads: Caddy web server (from nixpacks.toml)
Railway runs: ./caddy run --config Caddyfile
Result: Caddy serving /app/dist on assigned port
Access: https://frontend-xyz.railway.app
```

## 🎨 Visual Deployment Map

```
┌─────────────────────────────────────────────────────────┐
│                  GitHub Repository                       │
│  ┌──────────────┐              ┌──────────────┐        │
│  │   backend/   │              │  frontend/   │        │
│  │              │              │              │        │
│  │ Flask code   │              │ React code   │        │
│  │ + Railway    │              │ + Railway    │        │
│  │   config     │              │   config     │        │
│  └──────┬───────┘              └──────┬───────┘        │
└─────────┼──────────────────────────────┼───────────────┘
          │                              │
          ↓                              ↓
┌─────────────────────────────────────────────────────────┐
│                  Railway Platform                        │
│  ┌──────────────┐              ┌──────────────┐        │
│  │   Backend    │              │  Frontend    │        │
│  │   Service    │◄────CORS────►│  Service     │        │
│  │              │              │              │        │
│  │  gunicorn    │              │   Caddy      │        │
│  │   + Flask    │              │  + React     │        │
│  └──────┬───────┘              └──────────────┘        │
│         │                                                │
│         ↓                                                │
│  ┌──────────────┐                                       │
│  │  PostgreSQL  │                                       │
│  │   Database   │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

## 📝 File Importance Key

🔴 **CRITICAL** - Deployment will fail without these
🟡 **IMPORTANT** - Strongly recommended
🟢 **OPTIONAL** - Nice to have

### Backend:
- 🔴 requirements.txt (must include gunicorn)
- 🔴 app.py (must bind to 0.0.0.0)
- 🟡 .python-version (specifies Python 3.11)
- 🟢 .env.example (reference only)

### Frontend:
- 🔴 Caddyfile (serves production build)
- 🔴 nixpacks.toml (configures Caddy installation)
- 🟡 package.json (must have build script)

### Root:
- 🟡 .gitignore (prevents committing secrets)

---

This visual guide shows how everything connects. Follow QUICK_START_CHECKLIST.md to implement this structure step-by-step!
