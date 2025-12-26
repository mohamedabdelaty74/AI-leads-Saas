# AI Leads SaaS - Online Deployment Guide

**Complete guide to deploy your application to production**

---

## 🎯 Deployment Options Overview

| Platform | Best For | Cost | Difficulty | Time |
|----------|----------|------|------------|------|
| **Railway** | Quick start | $5-20/mo | Easy | 15 min |
| **Render** | Free tier available | $0-25/mo | Easy | 20 min |
| **DigitalOcean** | Full control | $24-50/mo | Medium | 45 min |
| **AWS/GCP** | Enterprise scale | $30-100+/mo | Hard | 2-3 hours |
| **Vercel + Railway** | Split deploy | $20-40/mo | Easy | 30 min |

**My Recommendation:** Start with Railway (easiest) or Render (free tier)

---

## 🚀 Option 1: Railway (Recommended for Beginners)

**Best for:** Fast deployment, minimal configuration
**Cost:** ~$5-20/month
**Time:** 15-20 minutes

### Step 1: Prepare Your Code

```bash
# 1. Create .gitignore if not exists
cat > .gitignore << EOF
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.log
node_modules/
.next/
.cache/
*.db
EOF

# 2. Initialize git (if not already)
git init
git add .
git commit -m "Prepare for Railway deployment"
```

### Step 2: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Choose "Deploy from GitHub repo"

### Step 3: Deploy Backend

```bash
# Create Procfile for Railway
cat > Procfile << EOF
web: uvicorn backend.main:app --host 0.0.0.0 --port \$PORT
EOF

# Create railway.json
cat > railway.json << EOF
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port \$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF
```

### Step 4: Set Environment Variables in Railway

Go to Railway dashboard → Your project → Variables:

```bash
# Required
JWT_SECRET=<generate-with-secrets-token-urlsafe>
DATABASE_URL=<railway-provides-postgres-url>
ENVIRONMENT=production

# API Keys (your actual keys)
GOOGLE_API_KEY=your-google-api-key
HUGGINGFACE_API_KEY=your-huggingface-key
SERPAPI_KEY=your-serpapi-key

# Email
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@yourdomain.com

# Admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=<strong-password>

# Frontend URL (update after deploying frontend)
FRONTEND_URL=https://your-frontend.vercel.app
ALLOWED_ORIGINS=https://your-frontend.vercel.app

# AI Model (use Hugging Face API instead of local)
ENABLE_AI_GENERATION=true

# Redis (Railway add-on)
REDIS_URL=<railway-provides>
```

### Step 5: Add PostgreSQL Database

1. In Railway dashboard → "New" → "Database" → "PostgreSQL"
2. Railway automatically sets DATABASE_URL
3. Run migrations:
   ```bash
   # Railway will auto-run on deploy, or manually:
   railway run python add_performance_indexes.py
   ```

### Step 6: Deploy Frontend

**Option A: Vercel (Recommended)**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend
vercel

# Follow prompts:
# - Link to existing project or create new
# - Set build command: npm run build
# - Set output directory: .next
# - Set environment variables
```

**Environment Variables for Frontend (Vercel):**
```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Step 7: Configure Domain

**In Railway:**
- Settings → Domains → Generate Domain or add custom domain

**In Vercel:**
- Settings → Domains → Add your domain

**Update CORS:**
```bash
# In Railway environment variables
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## 🆓 Option 2: Render (Free Tier Available)

**Best for:** Free testing, hobby projects
**Cost:** Free (with limitations) or $7+/month
**Time:** 20-30 minutes

### Step 1: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Connect your repository

### Step 2: Deploy Backend

1. **New** → **Web Service**
2. **Connect Repository**
3. **Settings:**
   ```
   Name: ai-leads-backend
   Environment: Python
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables** (same as Railway above)

### Step 3: Add PostgreSQL

1. **New** → **PostgreSQL**
2. Name: ai-leads-db
3. Copy DATABASE_URL to web service environment variables

### Step 4: Deploy Frontend

1. **New** → **Static Site**
2. **Settings:**
   ```
   Build Command: cd frontend && npm install && npm run build
   Publish Directory: frontend/.next
   ```

3. **Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```

---

## 💪 Option 3: DigitalOcean (Full Control)

**Best for:** Production apps, full control
**Cost:** ~$24-50/month
**Time:** 45-60 minutes

### Step 1: Create Droplet

1. Go to https://digitalocean.com
2. Create → Droplets
3. Choose:
   - **Image:** Ubuntu 22.04
   - **Plan:** Basic ($24/mo - 4GB RAM, 2 vCPUs)
   - **Add-ons:** Enable backups
   - **SSH Key:** Add your SSH key

### Step 2: Initial Server Setup

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3 python3-pip python3-venv postgresql redis-server nginx git

# Create app user
adduser --disabled-password --gecos "" appuser
usermod -aG sudo appuser
su - appuser
```

### Step 3: Setup PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE elite_creatif_saas;
CREATE USER elite_creatif_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE elite_creatif_saas TO elite_creatif_user;
\q
```

### Step 4: Deploy Application

```bash
# Clone repository
cd /home/appuser
git clone https://github.com/yourusername/ai-leads-saas.git
cd ai-leads-saas

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# (Add all your environment variables)

# Run migrations
python add_performance_indexes.py
```

### Step 5: Setup Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/ai-leads.service

# Add:
[Unit]
Description=AI Leads SaaS Backend
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/home/appuser/ai-leads-saas
Environment="PATH=/home/appuser/ai-leads-saas/venv/bin"
ExecStart=/home/appuser/ai-leads-saas/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable ai-leads
sudo systemctl start ai-leads
sudo systemctl status ai-leads
```

### Step 6: Configure Nginx

```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/ai-leads

# Add:
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/ai-leads /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Setup SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

### Step 8: Deploy Frontend

```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Build frontend
cd /home/appuser/ai-leads-saas/frontend
npm install
npm run build

# Install PM2
sudo npm install -g pm2

# Start frontend
pm2 start npm --name "frontend" -- start
pm2 save
pm2 startup
```

---

## 📋 Pre-Deployment Checklist

### Security
- [ ] Change all default passwords in .env
- [ ] Generate strong JWT_SECRET (64+ chars)
- [ ] Set ENVIRONMENT=production
- [ ] Configure ALLOWED_ORIGINS with your domain
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure backup strategy

### Database
- [ ] Use PostgreSQL (not SQLite)
- [ ] Run performance indexes migration
- [ ] Set up automated backups
- [ ] Configure connection pooling

### API Keys
- [ ] Get production API keys:
  - Google Maps API
  - Hugging Face
  - SerpAPI
  - SendGrid
  - Stripe (production keys)

### Environment Variables
- [ ] JWT_SECRET (strong, unique)
- [ ] DATABASE_URL (PostgreSQL)
- [ ] REDIS_URL
- [ ] All API keys
- [ ] FRONTEND_URL
- [ ] ALLOWED_ORIGINS
- [ ] Admin credentials

### Testing
- [ ] Test registration
- [ ] Test login
- [ ] Test lead generation
- [ ] Test email sending
- [ ] Test WhatsApp
- [ ] Check performance
- [ ] Verify security headers

---

## 🔥 Quick Deploy Commands

### Railway (Fastest)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Add PostgreSQL
railway add postgresql

# Set environment variables
railway variables set JWT_SECRET=<your-secret>
```

### Render
```bash
# Just connect GitHub repo in dashboard
# Render auto-detects and deploys
# Add environment variables in dashboard
```

### Docker (Any Platform)
```bash
# Build
docker build -t ai-leads-backend .
docker build -t ai-leads-frontend ./frontend

# Run
docker-compose up -d
```

---

## 💰 Cost Estimation

### Small Scale (0-1000 users)
- **Railway:** $15-25/month
- **Vercel (Frontend):** Free
- **Total:** ~$15-25/month

### Medium Scale (1000-10000 users)
- **DigitalOcean Droplet:** $24/month
- **Managed PostgreSQL:** $15/month
- **Vercel Pro:** $20/month
- **Total:** ~$60/month

### Large Scale (10000+ users)
- **AWS/GCP:** $100-500/month
- **Load balancer:** $20/month
- **CDN:** $50/month
- **Total:** $170-570/month

---

## 🐛 Common Deployment Issues

### Issue 1: AI Model Too Large
**Problem:** 14GB Qwen model won't fit in container

**Solution:** Use Hugging Face API instead
```python
# In .env
ENABLE_AI_GENERATION=true
HUGGINGFACE_API_KEY=your-key

# Use API endpoint instead of local model
```

### Issue 2: Database Connection Fails
**Problem:** Can't connect to PostgreSQL

**Solution:** Check DATABASE_URL format
```bash
# Correct format:
postgresql://username:password@host:port/database

# With SSL (required by some platforms):
postgresql://username:password@host:port/database?sslmode=require
```

### Issue 3: CORS Errors
**Problem:** Frontend can't connect to backend

**Solution:** Update ALLOWED_ORIGINS
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
# No trailing slashes!
```

### Issue 4: Port Already in Use
**Problem:** Port 8000 or 3000 in use

**Solution:** Platform assigns PORT automatically
```python
# Backend will use $PORT from environment
# Don't hardcode port 8000
```

---

## 📞 Need Help?

### Recommended Approach
1. **Start with Railway** (easiest, fast)
2. **Test everything** thoroughly
3. **Scale to DigitalOcean** when needed
4. **Move to AWS/GCP** for enterprise

### Resources
- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- DigitalOcean Tutorials: https://www.digitalocean.com/community/tutorials
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/

---

**Ready to deploy? Start with Railway - it's the fastest way to get online!**
