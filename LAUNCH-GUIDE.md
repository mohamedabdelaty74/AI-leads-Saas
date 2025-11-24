# 🚀 Complete Launch Guide

**Get your full-stack AI Leads SaaS running in 5 minutes!**

---

## ✅ What's Been Fixed & Added

### **Critical Fixes**
✅ **Database Models** - Created all missing SQLAlchemy models (tenant, user, campaign, lead)
✅ **Backend Integration** - Backend now fully functional with FastAPI
✅ **Frontend Ready** - All 8 pages built and styled professionally
✅ **Startup Scripts** - One-click launch for both backend and frontend

### **Project Structure**
```
AI-leads-Saas-main/
├── backend/           ← FastAPI REST API
├── frontend/          ← Next.js React UI
├── models/            ← Database models (NEW!)
├── scrapers/          ← Web scrapers
├── gen/               ← AI content generation
├── start.bat          ← Windows launcher (NEW!)
├── start.sh           ← Mac/Linux launcher (NEW!)
└── .env               ← Configuration file
```

---

## 🎯 Quick Start

### **Windows (Easiest)**
```bash
# 1. Double-click this file:
start.bat

# That's it! Two windows will open:
# - Backend API (Python)
# - Frontend UI (React)
```

### **Mac/Linux**
```bash
# 1. Make script executable
chmod +x start.sh

# 2. Run it
./start.sh
```

### **Manual Start (If needed)**

**Terminal 1 - Backend:**
```bash
python backend/main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install  # First time only
npm run dev
```

---

## 🌐 Access Your Application

### **Frontend (User Interface)**
Open: **http://localhost:3000**

You'll see:
- ✅ Beautiful login page
- ✅ Registration form
- ✅ Dashboard with analytics
- ✅ Lead generation interface
- ✅ Campaign management
- ✅ Settings page

### **Backend (API Documentation)**
Open: **http://localhost:8000/docs**

You'll see:
- ✅ Interactive Swagger UI
- ✅ All API endpoints
- ✅ Test requests directly

---

## 📋 First Time Setup

### **Step 1: Install Dependencies**

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### **Step 2: Configure Environment**

Edit `.env` file:
```env
# Minimum Required
JWT_SECRET=your-secret-key-here
GOOGLE_API_KEY=your-google-api-key
HUGGINGFACE_API_KEY=your-huggingface-token

# Optional (for full features)
SERPAPI_KEY=your-serpapi-key
HUNTER_API_KEY=your-hunter-key
```

**Generate JWT Secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### **Step 3: Launch**
```bash
# Windows
start.bat

# Mac/Linux
./start.sh
```

---

## 🔑 API Keys - Where to Get Them

### **1. Google Maps API** (For lead scraping)
1. Go to: https://console.cloud.google.com/
2. Create new project
3. Enable "Places API" and "Geocoding API"
4. Create credentials → API Key
5. Add to `.env`: `GOOGLE_API_KEY=your-key`

### **2. Hugging Face** (For AI models)
1. Go to: https://huggingface.co/settings/tokens
2. Create new token
3. Add to `.env`: `HUGGINGFACE_API_KEY=your-token`

### **3. SerpAPI** (Optional - for web research)
1. Go to: https://serpapi.com/
2. Sign up for free account
3. Get API key from dashboard
4. Add to `.env`: `SERPAPI_KEY=your-key`

### **4. Hunter.io** (Optional - for email finding)
1. Go to: https://hunter.io/
2. Sign up for free account
3. Get API key
4. Add to `.env`: `HUNTER_API_KEY=your-key`

---

## 🎯 Testing Your Setup

### **1. Test Backend**
```bash
# Check backend is running
curl http://localhost:8000/health

# Should return: {"status":"healthy","version":"2.0.0"}
```

### **2. Test Frontend**
1. Open http://localhost:3000
2. You should see the login page
3. Click "Sign up for free"
4. Register a new account

### **3. Test Complete Flow**
1. **Register** → Create account
2. **Login** → Enter credentials
3. **Dashboard** → See analytics
4. **Leads** → Try generating leads
5. **Campaigns** → Create a campaign
6. **Settings** → Update profile

---

## 📊 What Each Service Does

### **Backend (Port 8000)**
- **What**: FastAPI REST API
- **Does**:
  - User authentication (JWT)
  - Campaign management
  - Lead storage
  - AI content generation
  - Web scraping
  - Email/WhatsApp sending

### **Frontend (Port 3000)**
- **What**: Next.js React UI
- **Does**:
  - Beautiful user interface
  - Dashboard with analytics
  - Lead generation forms
  - Campaign management
  - Settings and configuration
  - Real-time updates

---

## 🐛 Troubleshooting

### **Problem: Backend won't start**
**Solution:**
```bash
# Check Python version (need 3.10+)
python --version

# Install dependencies
pip install -r requirements.txt

# Check if models exist
ls models/

# Should see: base.py, tenant.py, user.py, campaign.py
```

### **Problem: Frontend won't start**
**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### **Problem: Port already in use**
**Solution:**
```bash
# Backend (change in backend/main.py line 620)
# Change port=8000 to port=8001

# Frontend (run with different port)
PORT=3001 npm run dev
```

### **Problem: Can't register/login**
**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS is configured: Look for "ALLOWED_ORIGINS" in .env
3. Check database exists: `ls database/`
4. Check browser console for errors (F12)

### **Problem: API errors in frontend**
**Solution:**
```bash
# Check frontend .env.local
cd frontend
cat .env.local

# Should have:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📈 Next Steps

### **1. Customize Branding**
- **Logo**: Replace in `frontend/src/components/layout/Sidebar.tsx`
- **Colors**: Edit `frontend/tailwind.config.ts`
- **Company Name**: Update in settings

### **2. Add Real Data**
- Get actual API keys
- Configure SMTP for emails
- Set up WhatsApp Business API
- Enable Google Maps scraping

### **3. Deploy to Production**
- **Frontend**: Deploy to Vercel (easiest)
- **Backend**: Deploy to Railway/Render/AWS
- **Database**: Use PostgreSQL (not SQLite)

---

## 🎉 You're Ready!

Your complete full-stack AI Leads SaaS is now running!

**What you have:**
- ✅ Professional frontend (8 pages, 10+ components)
- ✅ Production backend (FastAPI with JWT auth)
- ✅ Database models (multi-tenant isolation)
- ✅ Complete integration
- ✅ One-click startup

**What to do:**
1. Launch with `start.bat` (Windows) or `./start.sh` (Mac/Linux)
2. Open http://localhost:3000
3. Register an account
4. Start generating leads!

---

## 📚 Documentation

- **Frontend Docs**: `frontend/README.md`
- **Quick Setup**: `frontend/SETUP.md`
- **Components**: `frontend/COMPONENTS.md`
- **Complete Guide**: `frontend/COMPLETE-GUIDE.md`
- **Features**: `frontend/FEATURES-SHOWCASE.md`

---

## 🆘 Need Help?

### **Check Logs**
- Backend: Terminal window or `logs/backend.log`
- Frontend: Terminal window or `logs/frontend.log`

### **Verify Services**
```bash
# Backend health check
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

### **Reset Everything**
```bash
# Stop all services
# Delete database
rm -rf database/

# Restart
./start.sh  # or start.bat
```

---

**Your full-stack SaaS is complete and ready to use! 🚀**
