# 🚀 Production Deployment Guide

This guide will help you deploy your AI Leads SaaS platform to production.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [API Configuration](#api-configuration)
7. [Security Checklist](#security-checklist)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🎯 Prerequisites

Before deploying, ensure you have:

- ✅ PostgreSQL database (14 or higher)
- ✅ Python 3.10+ installed
- ✅ Node.js 18+ and npm installed
- ✅ Domain name (for production)
- ✅ SSL certificate (Let's Encrypt recommended)
- ✅ Cloud hosting account (AWS, DigitalOcean, etc.)

### Required API Keys

1. **Google Maps API** - For lead scraping
   - Get from: https://console.cloud.google.com
   - Enable: Places API, Geocoding API

2. **SendGrid API** - For email sending
   - Get from: https://sendgrid.com
   - Free tier: 100 emails/day

3. **Stripe API** (Optional) - For payments
   - Get from: https://stripe.com

---

## 🔧 Environment Setup

### 1. Clone and Install

```bash
# Clone repository
git clone <your-repo-url>
cd AI-leads-Saas-main

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment Variables

Copy the example .env file and update with your production values:

```bash
cp .env .env.production
```

**Critical Environment Variables:**

```env
# ===== Security =====
JWT_SECRET=<generate-strong-random-secret>  # Use: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
BCRYPT_ROUNDS=12

# ===== Database =====
DATABASE_URL=postgresql://user:password@hostname:5432/database_name

# ===== API Keys =====
GOOGLE_API_KEY=<your-google-maps-api-key>
SENDGRID_API_KEY=<your-sendgrid-api-key>
STRIPE_SECRET_KEY=<your-stripe-secret-key>

# ===== Application =====
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com

# ===== Email =====
FROM_EMAIL=noreply@yourdomain.com
SUPPORT_EMAIL=support@yourdomain.com

# ===== Rate Limiting =====
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# ===== Monitoring =====
SENTRY_DSN=<your-sentry-dsn>  # Optional but recommended
```

---

## 💾 Database Setup

### Option A: Managed PostgreSQL (Recommended)

**Popular Providers:**
- AWS RDS: https://aws.amazon.com/rds/
- DigitalOcean Managed Database: https://www.digitalocean.com/products/managed-databases
- Heroku Postgres: https://www.heroku.com/postgres
- Supabase: https://supabase.com

**Steps:**
1. Create a PostgreSQL 14+ instance
2. Note down connection string
3. Update `DATABASE_URL` in .env
4. Run database initialization

```bash
python reset_database.py  # Creates all tables
```

### Option B: Self-Hosted PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE elite_creatif_saas;
CREATE USER elite_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE elite_creatif_saas TO elite_user;
\q

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://elite_user:your_secure_password@localhost:5432/elite_creatif_saas
```

---

## 🖥️ Backend Deployment

### Option 1: Deploy with Railway

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repository
4. Add environment variables from .env
5. Railway will auto-detect Python and deploy

### Option 2: Deploy with Docker

```bash
# Create Dockerfile (already included)
docker build -t elite-creatif-backend .
docker run -d -p 8000:8000 --env-file .env elite-creatif-backend
```

### Option 3: Deploy with Gunicorn (Ubuntu/Debian)

```bash
# Install Gunicorn
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/elite-api.service
```

**Service file content:**

```ini
[Unit]
Description=Elite Creatif API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/elite-creatif
Environment="PATH=/var/www/elite-creatif/venv/bin"
EnvironmentFile=/var/www/elite-creatif/.env
ExecStart=/var/www/elite-creatif/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl start elite-api
sudo systemctl enable elite-api

# Check status
sudo systemctl status elite-api
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🌐 Frontend Deployment

### Option 1: Deploy to Vercel (Recommended)

1. Go to https://vercel.com
2. Import your GitHub repository
3. Framework: Next.js (auto-detected)
4. Root Directory: `frontend`
5. Add environment variables:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_VERSION=v1
```

6. Deploy!

### Option 2: Deploy with Netlify

Similar to Vercel:
1. Connect GitHub repo
2. Build command: `cd frontend && npm run build`
3. Publish directory: `frontend/.next`
4. Add environment variables

### Option 3: Self-Host with PM2

```bash
cd frontend

# Build for production
npm run build

# Install PM2
npm install -g pm2

# Start with PM2
pm2 start npm --name "elite-frontend" -- start

# Save PM2 config
pm2 save
pm2 startup
```

---

## 🔑 API Configuration

### Google Maps API Setup

1. Go to https://console.cloud.google.com
2. Create new project or select existing
3. Enable APIs:
   - Places API
   - Geocoding API
   - Maps JavaScript API
4. Create credentials → API Key
5. Restrict key (recommended):
   - Application restrictions: HTTP referrers or IP addresses
   - API restrictions: Select only needed APIs
6. Copy key to `GOOGLE_API_KEY` in .env

### SendGrid Email Setup

1. Sign up at https://sendgrid.com
2. Create API Key: Settings → API Keys
3. Verify sender email: Settings → Sender Authentication
4. Copy key to `SENDGRID_API_KEY` in .env
5. Update `FROM_EMAIL` with verified email

---

## 🔒 Security Checklist

### Before Going Live:

- [ ] Change all default passwords
- [ ] Generate new JWT_SECRET (use `openssl rand -hex 32`)
- [ ] Enable HTTPS/SSL for all domains
- [ ] Update ALLOWED_ORIGINS to production domains only
- [ ] Enable rate limiting (`RATE_LIMIT_ENABLED=true`)
- [ ] Set secure database password
- [ ] Restrict database access to backend server IP only
- [ ] Enable firewall on server
- [ ] Set up automated backups
- [ ] Configure monitoring (Sentry)
- [ ] Review and remove debug endpoints
- [ ] Enable CORS only for your domains
- [ ] Set secure session cookies
- [ ] Implement HTTPS-only cookie flag
- [ ] Add Content Security Policy headers
- [ ] Enable SQL injection protection (already handled by SQLAlchemy)

### Recommended Security Headers

Add to Nginx config:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

---

## 📊 Monitoring & Maintenance

### Setup Monitoring

1. **Sentry for Error Tracking**
   ```bash
   pip install sentry-sdk
   ```

   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))
   ```

2. **Uptime Monitoring**
   - Use UptimeRobot (free)
   - Monitor: https://api.yourdomain.com/health

3. **Log Management**
   ```bash
   # Configure logging
   import logging
   logging.basicConfig(
       filename='/var/log/elite-api.log',
       level=logging.INFO
   )
   ```

### Automated Backups

```bash
# Create backup script
cat > /usr/local/bin/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump DATABASE_NAME > /backups/db_$DATE.sql
find /backups -name "db_*.sql" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-db.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /usr/local/bin/backup-db.sh
```

### Health Checks

Monitor these endpoints:
- `GET /health` - API health
- `GET /api/v1/campaigns` (with auth) - Database connectivity

---

## 🚦 Post-Deployment Testing

1. **Test User Registration**
   ```bash
   curl -X POST https://api.yourdomain.com/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test1234","company_name":"Test Co","company_email":"test@example.com"}'
   ```

2. **Test Authentication**
   - Register new user
   - Login with credentials
   - Verify JWT token works

3. **Test Campaign Creation**
   - Create campaign via UI
   - Verify data persists in database

4. **Test Lead Generation**
   - Generate leads from Google Maps
   - Verify real API integration works

5. **Test Team Invitations**
   - Invite team member
   - Verify invitation email sent

6. **Test Rate Limiting**
   - Send 100+ requests quickly
   - Verify 429 error after limit

---

## 📝 Maintenance Tasks

### Daily
- Check error logs
- Monitor API response times
- Review failed email sends

### Weekly
- Review database size
- Check backup integrity
- Update dependencies (if needed)

### Monthly
- Security audit
- Performance optimization
- Review user feedback
- Update documentation

---

## 🆘 Troubleshooting

### Common Issues

**Issue: API returns 500 errors**
```bash
# Check logs
sudo journalctl -u elite-api -n 100

# Check database connection
psql $DATABASE_URL
```

**Issue: Frontend can't connect to API**
```bash
# Check CORS settings
# Verify ALLOWED_ORIGINS includes frontend domain
# Check if API is accessible: curl https://api.yourdomain.com/health
```

**Issue: Google Maps returns no results**
```bash
# Test API key
curl "https://maps.googleapis.com/maps/api/place/textsearch/json?query=restaurants&key=YOUR_API_KEY"

# Check billing enabled
# Verify APIs are enabled
```

---

## 📞 Support

- Documentation: Check README.md
- Issues: Create GitHub issue
- Email: support@yourdomain.com

---

## ✅ Deployment Checklist

Copy this checklist for your deployment:

```
Pre-Deployment:
[ ] All tests passing
[ ] Environment variables configured
[ ] Database schema up to date
[ ] API keys obtained and configured
[ ] Security review completed
[ ] Backup strategy in place

Deployment:
[ ] Backend deployed and accessible
[ ] Frontend deployed and accessible
[ ] Database connected and initialized
[ ] SSL certificates installed
[ ] DNS configured correctly
[ ] Monitoring set up

Post-Deployment:
[ ] Health checks passing
[ ] User registration works
[ ] Lead generation works
[ ] Emails sending correctly
[ ] Team invitations work
[ ] Rate limiting active
[ ] Backups running
[ ] Error tracking configured
```

---

**🎉 Congratulations! Your platform is now live!**

For questions or issues, refer to the troubleshooting section or contact support.
