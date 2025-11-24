# Elite Creatif - Modern Frontend

A professional, modern B2B SaaS UI/UX built with Next.js 14, TypeScript, and Tailwind CSS. Inspired by industry-leading products like Intercom, Jeeva AI, and Toggl.

## 🎨 Design System

### Color Palette
- **Primary**: Indigo (#6366F1) - Trust, technology, innovation
- **Success**: Green (#10B981) - Positive actions, confirmations
- **Warning**: Amber (#F59E0B) - Cautions, important notices
- **Error**: Red (#EF4444) - Errors, destructive actions
- **Neutral**: Gray scale (50-950) - Text, backgrounds, borders

### Typography
- **Font Family**: Inter (Variable font with weights 400-700)
- **Scale**: Display (72px), H1 (48px), H2 (36px), H3 (30px), H4 (24px), Body (16px)

### Component Library
- ✅ Button (5 variants, 3 sizes, loading states)
- ✅ Input (with labels, errors, icons)
- ✅ Card (with hover effects)
- ✅ Badge (6 variants with dot indicators)
- ✅ Modal (with animations, 5 sizes)
- ✅ Tabs (with smooth transitions)
- ✅ Select (with validation)
- ✅ Table (with sorting, loading, empty states)
- ✅ Skeleton loaders
- ✅ Toast notifications

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm 9+
- Your FastAPI backend running on `http://localhost:8000`

### Installation

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Create environment file**:
   ```bash
   cp .env.local.example .env.local
   ```

4. **Configure environment variables** (`.env.local`):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_API_VERSION=v1
   ```

5. **Run the development server**:
   ```bash
   npm run dev
   ```

6. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router
│   │   ├── login/             # Authentication pages
│   │   ├── register/
│   │   ├── dashboard/         # Main dashboard
│   │   └── layout.tsx         # Root layout
│   │
│   ├── components/
│   │   ├── ui/                # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   └── Toast.tsx
│   │   │
│   │   └── layout/            # Layout components
│   │       ├── Sidebar.tsx
│   │       ├── Navbar.tsx
│   │       └── DashboardLayout.tsx
│   │
│   ├── lib/
│   │   ├── api-client.ts      # Axios API client
│   │   └── utils.ts           # Utility functions
│   │
│   ├── hooks/
│   │   └── useAuth.ts         # Authentication hook
│   │
│   ├── types/
│   │   ├── api.ts             # API types
│   │   └── models.ts          # UI model types
│   │
│   └── styles/
│       └── globals.css        # Global styles + Tailwind
│
├── public/
├── tailwind.config.ts         # Tailwind configuration
├── tsconfig.json              # TypeScript configuration
├── next.config.js             # Next.js configuration
└── package.json
```

## 🛠️ Available Scripts

```bash
# Development
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

## 🔌 API Integration

The frontend connects to your FastAPI backend through the API client (`src/lib/api-client.ts`).

### Authentication Flow
1. User logs in via `/login` page
2. Access token and refresh token stored in localStorage
3. API client automatically adds `Authorization: Bearer <token>` to requests
4. Token refresh handled automatically on 401 responses

### API Endpoints Used
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/campaigns` - List campaigns
- `POST /api/v1/campaigns` - Create campaign
- `GET /api/v1/campaigns/:id/leads` - Get campaign leads

## 🎭 Features Implemented

### ✅ Phase 1: Foundation
- [x] Design system with Tailwind CSS
- [x] Next.js 14 with TypeScript
- [x] Framer Motion animations
- [x] React Hot Toast notifications

### ✅ Phase 2: Core Components
- [x] 10+ reusable UI components
- [x] Sidebar navigation with active states
- [x] Top navbar with search and notifications
- [x] Responsive dashboard layout
- [x] Accessibility (ARIA labels, keyboard navigation)

### ✅ Phase 3: Pages
- [x] Login page (split-screen design)
- [x] Register page (multi-field form)
- [x] Dashboard with analytics cards
- [x] Recent campaigns list
- [x] Quick actions panel

### ✅ Phase 4: Integration
- [x] FastAPI backend integration
- [x] JWT authentication with auto-refresh
- [x] Toast notifications for success/error
- [x] Loading states and skeleton loaders
- [x] Fully responsive design

### 🚧 To Be Built
- [ ] Lead Generation pages (Google Maps, LinkedIn, Instagram tabs)
- [ ] Campaigns management page (CRUD operations)
- [ ] Settings page (Company Profile, API Keys, Team)
- [ ] Analytics charts (Recharts integration)
- [ ] File upload for bulk lead import
- [ ] Email/WhatsApp campaign execution UI

## 📱 Responsive Design

The UI is fully responsive with breakpoints:
- **Mobile**: < 768px (stacked layout, hamburger menu)
- **Tablet**: 768px - 1024px (collapsible sidebar)
- **Desktop**: > 1024px (full sidebar, expanded layout)

## ♿ Accessibility

- All interactive elements have ARIA labels
- Keyboard navigation supported (Tab, Enter, Esc)
- Focus indicators visible (ring-2 ring-offset-2)
- Color contrast meets WCAG AA standards (4.5:1 minimum)
- Screen reader friendly with semantic HTML

## 🎨 Customization

### Colors
Edit `tailwind.config.ts` to change the color palette:
```typescript
colors: {
  primary: {
    500: '#YOUR_COLOR',
    // ...
  }
}
```

### Fonts
Replace Inter with your preferred font in `src/app/layout.tsx`:
```typescript
import { YourFont } from 'next/font/google'
```

### Components
All components are in `src/components/ui/` and can be customized by editing the component files.

## 🐛 Common Issues

### Issue: "Cannot connect to API"
**Solution**: Ensure your FastAPI backend is running on `http://localhost:8000` or update `NEXT_PUBLIC_API_URL` in `.env.local`

### Issue: "Module not found" errors
**Solution**: Run `npm install` to ensure all dependencies are installed

### Issue: "Port 3000 already in use"
**Solution**: Kill the process on port 3000 or change the port:
```bash
PORT=3001 npm run dev
```

## 🚀 Deployment

### Production Build
```bash
npm run build
npm run start
```

### Deploy to Vercel (Recommended)
1. Push your code to GitHub
2. Import project in Vercel
3. Add environment variables
4. Deploy automatically

### Deploy to Other Platforms
- **Netlify**: Use `npm run build` and deploy the `.next` folder
- **AWS/Azure**: Use Docker or build and serve with Node.js
- **Self-hosted**: Use PM2 or similar process manager

## 📚 Documentation

### Component Usage Examples

**Button**:
```tsx
<Button variant="primary" size="lg" loading={isLoading}>
  Submit
</Button>
```

**Input**:
```tsx
<Input
  label="Email"
  type="email"
  error={errors.email}
  leftIcon={<Mail />}
  fullWidth
/>
```

**Modal**:
```tsx
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Confirm Action"
>
  <p>Are you sure?</p>
</Modal>
```

**Toast**:
```tsx
import { toast } from '@/components/ui/Toast'

toast.success('Campaign created!')
toast.error('Something went wrong')
```

## 🤝 Contributing

When adding new features:
1. Follow the existing component structure
2. Use TypeScript for type safety
3. Add proper ARIA labels for accessibility
4. Test on mobile, tablet, and desktop
5. Ensure responsive design

## 📄 License

This project is part of Elite Creatif SaaS platform.

## 🙋 Support

For questions or issues:
1. Check the existing components in `src/components/ui/`
2. Review the API client in `src/lib/api-client.ts`
3. Check the backend API documentation at `http://localhost:8000/docs`

---

**Built with ❤️ using Next.js 14, TypeScript, and Tailwind CSS**
