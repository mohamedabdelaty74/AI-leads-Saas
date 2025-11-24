# 🚀 Quick Setup Guide

Get your modern frontend running in 5 minutes!

## Step-by-Step Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

This will install:
- Next.js 14 (React framework)
- TypeScript (type safety)
- Tailwind CSS (styling)
- Framer Motion (animations)
- Axios (API client)
- React Hook Form (forms)
- React Hot Toast (notifications)
- Lucide React (icons)

### 2. Configure Environment
```bash
# Create environment file
cp .env.local.example .env.local

# Edit .env.local with your settings
# Default values work if your backend is on http://localhost:8000
```

### 3. Start Backend (Required)
Make sure your FastAPI backend is running:
```bash
# In the root directory
python gradio_saas_integrated.py
# or
uvicorn backend.main:app --reload
```

### 4. Start Frontend
```bash
npm run dev
```

### 5. Open Browser
Navigate to: **http://localhost:3000**

You should see the login page!

## 🎯 First Steps

### 1. Create an Account
- Click "Sign up for free" on login page
- Fill in your organization details
- Complete registration

### 2. Explore Dashboard
- View analytics cards (leads, campaigns, emails sent)
- Check recent campaigns
- Use quick actions to navigate

### 3. Generate Leads (Coming Soon)
- Navigate to "Lead Generation" in sidebar
- Choose source (Google Maps, LinkedIn, Instagram)
- Configure scraping parameters
- Generate and preview leads

## 🔧 Development Tips

### Hot Reload
The dev server has hot reload enabled. Changes to files will automatically refresh the browser.

### Component Development
1. Create new components in `src/components/ui/`
2. Use existing components as templates
3. Follow TypeScript types strictly

### API Calls
Use the API client for all backend requests:
```typescript
import { api } from '@/lib/api-client'

// Example: Get campaigns
const response = await api.campaigns.list()
```

### Toast Notifications
Show feedback to users:
```typescript
import { toast } from '@/components/ui/Toast'

toast.success('Lead generated!')
toast.error('Something went wrong')
toast.info('Processing...')
```

## 🐞 Troubleshooting

### Problem: npm install fails
**Solution**:
```bash
# Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Problem: "Cannot connect to backend"
**Solutions**:
1. Check if backend is running on port 8000
2. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check CORS settings in backend

### Problem: TypeScript errors
**Solution**:
```bash
# Run type check
npm run type-check

# Fix common issues
npm install --save-dev @types/node @types/react @types/react-dom
```

### Problem: Styles not loading
**Solution**:
```bash
# Rebuild Tailwind
rm -rf .next
npm run dev
```

## 📦 Production Build

### Test Production Build Locally
```bash
npm run build
npm run start
```

### Deploy to Vercel
1. Push code to GitHub
2. Import project on [vercel.com](https://vercel.com)
3. Add environment variables:
   - `NEXT_PUBLIC_API_URL` = your production API URL
4. Deploy

## 🎨 Customization Quick Guide

### Change Primary Color
Edit `tailwind.config.ts`:
```typescript
colors: {
  primary: {
    500: '#YOUR_COLOR',
    600: '#YOUR_DARKER_COLOR',
    // ...
  }
}
```

### Change Logo
Replace in `src/components/layout/Sidebar.tsx`:
```tsx
<div className="h-8 w-8 ...">
  <Image src="/your-logo.png" alt="Logo" />
</div>
```

### Add New Page
1. Create `src/app/your-page/page.tsx`
2. Wrap in `<DashboardLayout>`
3. Add route to sidebar navigation

## 🚀 Next Steps

1. **Explore Components**: Check `src/components/ui/` for all available components
2. **Build Pages**: Create Lead Generation, Campaigns, and Settings pages
3. **Add Features**: Integrate charts, file uploads, bulk actions
4. **Customize**: Adjust colors, fonts, and layout to match your brand
5. **Deploy**: Push to production when ready

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [TypeScript](https://www.typescriptlang.org/docs/)

---

**Need help?** Check the main README.md for detailed documentation.
