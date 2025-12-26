# Deploy AI Leads SaaS to Production - Step by Step Guide

**Time Required:** 20-30 minutes
**Cost:** ~$15-25/month

---

## Prerequisites (COMPLETED)

- [x] Docker Desktop running
- [x] Redis container running locally
- [x] Backend connected to Redis
- [x] AI Model (1.5B) downloaded and working
- [x] Railway CLI installed
- [x] Configuration files created

---

## Part 1: Deploy Backend to Railway (15 minutes)

### Step 1: Create Railway Account

1. **Open your browser** and go to: **https://railway.app**

2. **Click "Login"** in the top right

3. **Select "GitHub"** to sign up with GitHub
   - This is recommended as it makes connecting your repo easier
   - Click "Authorize Railway" when prompted

4. **You're now logged in!** You should see the Railway dashboard

---

### Step 2: Create New Project

1. **Click "+ New Project"** button (big purple button)

2. **Select "Deploy from GitHub repo"**

3. **If prompted, install Railway app on GitHub:**
   - Click "Configure GitHub App"
   - Select "Only select repositories"
   - Choose your `AI-leads-Saas-main` repository (or whatever you named it)
   - Click "Install"

4. **Select your repository** from the list
   - Choose `AI-leads-Saas-main`

5. **Railway will start deploying** - WAIT! We need to add databases first!
   - Click "Cancel" or stop the deployment if it starts

---

### Step 3: Add PostgreSQL Database

1. **In your project, click "+ New"** button

2. **Select "Database" → "PostgreSQL"**

3. **Railway will create a PostgreSQL instance**
   - This takes 30-60 seconds
   - You'll see a new PostgreSQL service in your project

4. **IMPORTANT: Copy the DATABASE_URL**
   - Click on the PostgreSQL service
   - Go to "Variables" tab
   - You'll see `DATABASE_URL` - this is automatically set!
   - No need to copy, Railway handles this automatically

---

### Step 4: Add Redis

1. **Click "+ New"** button again

2. **Select "Database" → "Redis"**

3. **Railway will create a Redis instance**
   - Takes 30-60 seconds
   - You'll see a new Redis service

4. **REDIS_URL is auto-set** (same as PostgreSQL)

---

### Step 5: Configure Backend Environment Variables

1. **Click on your backend service** (the main app, not PostgreSQL or Redis)

2. **Go to "Variables" tab**

3. **Click "Raw Editor"** button (top right of variables section)

4. **Copy and paste ALL of these variables:**

```bash
# Security (from .env.production)
JWT_SECRET=1QLp18kNHK6Gaq5lXruEN0_GD6CSEeakETZy89s_8yuSjOsvV6jJPMuKGb3P-hrax4YxA8tD16-_GhC26Zn3oA
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
BCRYPT_ROUNDS=12
ENCRYPTION_KEY=acd7f6dad5f743561c0adf6b5807ea9f71ed34c9f346bb06b29c2dff2aea1bfa

# Admin
ADMIN_PASSWORD=1K6opWXMswIs&xbaINfKgrY0
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_FIRST_NAME=Admin
ADMIN_LAST_NAME=User

# AI Model
AI_MODEL_PATH=Qwen/Qwen2.5-1.5B-Instruct

# API Keys (YOUR ACTUAL KEYS)
GOOGLE_API_KEY=AIzaSyDNwosJJWa3pztf9Se6zgE4yHGDEaT4f3I
HUGGINGFACE_API_KEY=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
SERPAPI_KEY=6857485bd5b475fd64d777c6f2d8de8797cc2512349f4ba1182132e41c274860

# Email (GET SENDGRID KEY)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
SUPPORT_EMAIL=support@yourdomain.com

# Stripe (Optional - use test keys for now)
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=1aagLajzST2rGSN8wffl4JIY6pCCRA30aOO9kxRiECs

# Application
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com

# Feature Flags
ENABLE_AI_GENERATION=true
ENABLE_WHATSAPP=true
ENABLE_ANALYTICS=true
ENABLE_EXPORT=true

# Security Settings
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
MAX_LOGIN_ATTEMPTS=5
SESSION_EXPIRE_MINUTES=30
```

5. **Click "Update Variables"**

6. **IMPORTANT:** Railway automatically sets these (don't add manually):
   - `DATABASE_URL` (from PostgreSQL service)
   - `REDIS_URL` (from Redis service)
   - `PORT` (Railway sets this)

---

### Step 6: Deploy Backend

1. **Go to "Settings" tab** of your backend service

2. **Scroll to "Deploy"** section

3. **Click "Deploy"** button

4. **Watch the build logs:**
   - Click on "Deployments" tab
   - Click on the latest deployment
   - Watch the logs scroll - this takes 5-10 minutes

5. **Wait for:**
   - "Build successful"
   - "Deployment successful"
   - Status should show "Active"

---

### Step 7: Get Your Backend URL

1. **Go to "Settings" tab**

2. **Scroll to "Domains"** section

3. **Click "Generate Domain"**

4. **Copy the URL** - it will look like:
   ```
   https://your-app-production.up.railway.app
   ```

5. **Save this URL** - you'll need it for frontend!

6. **Test your backend:**
   - Open browser: `https://your-app-production.up.railway.app/health`
   - Should see: `{"status": "ok"}`

---

## Part 2: Deploy Frontend to Vercel (10 minutes)

### Step 1: Create Vercel Account

1. **Go to:** **https://vercel.com**

2. **Click "Sign Up"**

3. **Sign up with GitHub**

4. **Authorize Vercel**

---

### Step 2: Deploy Frontend

1. **Click "Add New..."** → **"Project"**

2. **Import your Git repository:**
   - Find `AI-leads-Saas-main`
   - Click "Import"

3. **Configure Project:**
   - **Framework Preset:** Next.js (should auto-detect)
   - **Root Directory:** Click "Edit" → Select `frontend`
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)

4. **Add Environment Variables:**
   Click "Environment Variables" and add:

```bash
NEXT_PUBLIC_API_URL=https://your-app-production.up.railway.app
```

Replace `your-app-production.up.railway.app` with YOUR Railway backend URL!

5. **Click "Deploy"**

6. **Wait 3-5 minutes** for deployment

7. **Get your frontend URL:**
   - Will look like: `https://ai-leads-saas.vercel.app`

---

### Step 3: Update Backend CORS Settings

**IMPORTANT:** Go back to Railway and update backend:

1. **Go to Railway → Your backend service → Variables**

2. **Update these variables:**

```bash
FRONTEND_URL=https://ai-leads-saas.vercel.app
ALLOWED_ORIGINS=https://ai-leads-saas.vercel.app,https://www.ai-leads-saas.vercel.app
```

Replace with YOUR Vercel URL!

3. **Click "Update Variables"**

4. **Railway will auto-redeploy** (takes 2-3 minutes)

---

## Part 3: Test Your Production Deployment

### Step 1: Test Backend

1. **Open:** `https://your-backend.railway.app/health`
   - Should see: `{"status": "ok"}`

2. **Check logs** in Railway:
   - Go to "Deployments" tab
   - Click latest deployment
   - Look for:
     - "AI model loaded successfully"
     - "Redis cache connected successfully"
     - "Application startup complete"

---

### Step 2: Test Frontend

1. **Open your Vercel URL:** `https://ai-leads-saas.vercel.app`

2. **Try to:**
   - Create account
   - Login
   - Navigate around

3. **If you see connection errors:**
   - Check CORS settings in Railway (ALLOWED_ORIGINS)
   - Check NEXT_PUBLIC_API_URL in Vercel

---

### Step 3: Test Full Flow

1. **Create a campaign**

2. **Add some leads**

3. **Generate emails:**
   - Should be 6-10x faster than before!
   - Qwen2.5-1.5B model is blazing fast

4. **Check database:**
   - Data should persist
   - PostgreSQL is working

---

## Troubleshooting

### Backend won't start?

**Check Railway logs:**
- Go to Deployments → Latest → Logs
- Look for errors

**Common issues:**
- Missing environment variables
- DATABASE_URL not set (Railway should auto-set this)
- Model download failing (first deploy takes longer ~10 min)

---

### Frontend can't connect to backend?

**Check:**
1. CORS settings in Railway (ALLOWED_ORIGINS)
2. NEXT_PUBLIC_API_URL in Vercel
3. Both should match your actual URLs

**Fix:**
- Update variables
- Redeploy both services

---

### Database connection errors?

**Check:**
- PostgreSQL service is running in Railway
- DATABASE_URL is set (Railway does this automatically)
- Check logs for connection errors

---

## Post-Deployment Checklist

- [ ] Backend deployed and health check passes
- [ ] Frontend deployed and loads
- [ ] Can create account / login
- [ ] Can create campaigns
- [ ] Can generate leads
- [ ] Emails generate successfully (6-10x faster!)
- [ ] Database persists data
- [ ] Redis caching works

---

## Your Production URLs

**Backend:** `https://_____.up.railway.app`
**Frontend:** `https://_____.vercel.app`

**Fill these in when you get them!**

---

## What You're Paying

**Railway:**
- PostgreSQL: ~$5/month
- Redis: ~$5/month
- Backend hosting: ~$5-15/month
- **Total: ~$15-25/month**

**Vercel:**
- Frontend: FREE (hobby tier)

**Total Monthly Cost: ~$15-25**

**With 100 users @ $49/mo:**
- Revenue: $4,900/month
- Costs: $25/month
- **Profit: $4,875/month (99% margin!)**

---

## Need Help?

**Check:**
1. Railway logs for backend issues
2. Vercel logs for frontend issues
3. Browser console for connection errors

**Common fixes:**
- Update CORS settings
- Verify environment variables
- Check database connection
- Ensure model downloaded (first deploy is slow)

---

## You're Almost Live!

**Next steps:**
1. Follow this guide step by step
2. Deploy to Railway (Part 1)
3. Deploy to Vercel (Part 2)
4. Test everything (Part 3)
5. Start getting users!

**Your SaaS with 6-10x faster AI is ready to launch! 🚀**
