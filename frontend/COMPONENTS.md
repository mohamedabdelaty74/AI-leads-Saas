# 🎨 Component Library Reference

Complete guide to all UI components with usage examples.

## Button

### Variants
- **primary**: Main action button (blue background)
- **secondary**: Secondary actions (gray background)
- **outline**: Bordered button (transparent with border)
- **ghost**: Minimal button (no background)
- **danger**: Destructive actions (red background)

### Sizes
- **sm**: Small (h-9, px-3)
- **md**: Medium (h-10, px-4) - default
- **lg**: Large (h-11, px-6)

### Usage
```tsx
import Button from '@/components/ui/Button'
import { Plus, Save } from 'lucide-react'

// Basic
<Button variant="primary">Click Me</Button>

// With loading state
<Button variant="primary" loading={isLoading}>
  Submit
</Button>

// With icons
<Button
  variant="outline"
  leftIcon={<Plus className="h-4 w-4" />}
>
  Add Item
</Button>

<Button
  variant="primary"
  rightIcon={<Save className="h-4 w-4" />}
>
  Save Changes
</Button>

// Different sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// Disabled
<Button disabled>Can't Click</Button>
```

---

## Input

### Props
- **label**: Field label
- **error**: Error message (turns input red)
- **helperText**: Helper text below input
- **leftIcon**: Icon on left side
- **rightIcon**: Icon on right side
- **fullWidth**: Take full width of container

### Usage
```tsx
import Input from '@/components/ui/Input'
import { Mail, Lock, Search } from 'lucide-react'

// Basic
<Input
  label="Email"
  type="email"
  placeholder="you@company.com"
  fullWidth
/>

// With icon
<Input
  label="Search"
  type="text"
  leftIcon={<Search className="h-4 w-4" />}
  placeholder="Search leads..."
/>

// With error
<Input
  label="Password"
  type="password"
  error="Password is too short"
  leftIcon={<Lock className="h-4 w-4" />}
/>

// With helper text
<Input
  label="API Key"
  type="text"
  helperText="Found in your account settings"
/>
```

---

## Card

### Variants
- **hover**: Adds hover effect (shadow + lift)
- **clickable**: Shows cursor pointer

### Padding Options
- **none**: No padding
- **sm**: p-4
- **md**: p-6 (default)
- **lg**: p-8

### Usage
```tsx
import Card, {
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from '@/components/ui/Card'

// Basic card
<Card>
  <p>Content here</p>
</Card>

// Full featured card
<Card hover clickable>
  <CardHeader>
    <CardTitle>Lead Generation</CardTitle>
    <CardDescription>Generate leads from multiple sources</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Main content goes here...</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>

// No padding card (for images)
<Card padding="none">
  <img src="/banner.jpg" alt="Banner" />
  <div className="p-6">
    <h3>Content with padding</h3>
  </div>
</Card>
```

---

## Badge

### Variants
- **default**: Gray
- **success**: Green
- **warning**: Amber
- **error**: Red
- **info**: Blue
- **primary**: Indigo

### Usage
```tsx
import Badge from '@/components/ui/Badge'

// Basic
<Badge variant="success">Active</Badge>

// With dot indicator
<Badge variant="success" dot>Online</Badge>

// Sizes
<Badge size="sm">Small</Badge>
<Badge size="md">Medium</Badge>
<Badge size="lg">Large</Badge>

// Use cases
<Badge variant="success" dot>Active Campaign</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Failed</Badge>
<Badge variant="info">Draft</Badge>
```

---

## Modal

### Props
- **isOpen**: Control visibility
- **onClose**: Close handler
- **title**: Modal title
- **description**: Subtitle
- **footer**: Footer content (usually buttons)
- **size**: sm | md | lg | xl | full
- **closeOnOverlayClick**: Allow closing by clicking backdrop
- **showCloseButton**: Show X button

### Usage
```tsx
import { useState } from 'react'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'

const [isOpen, setIsOpen] = useState(false)

// Basic modal
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Confirm Delete"
  description="This action cannot be undone"
>
  <p>Are you sure you want to delete this campaign?</p>
</Modal>

// With footer
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Create Campaign"
  footer={
    <>
      <Button variant="ghost" onClick={() => setIsOpen(false)}>
        Cancel
      </Button>
      <Button variant="primary" onClick={handleCreate}>
        Create
      </Button>
    </>
  }
>
  <form>
    <Input label="Campaign Name" />
  </form>
</Modal>

// Large modal
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Lead Details"
  size="lg"
>
  <div>Detailed content...</div>
</Modal>
```

---

## Tabs

### Usage
```tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import { Mail, MessageSquare } from 'lucide-react'

<Tabs defaultValue="email">
  <TabsList>
    <TabsTrigger
      value="email"
      icon={<Mail className="h-4 w-4" />}
    >
      Email
    </TabsTrigger>
    <TabsTrigger
      value="whatsapp"
      icon={<MessageSquare className="h-4 w-4" />}
    >
      WhatsApp
    </TabsTrigger>
  </TabsList>

  <TabsContent value="email">
    <p>Email content here</p>
  </TabsContent>

  <TabsContent value="whatsapp">
    <p>WhatsApp content here</p>
  </TabsContent>
</Tabs>

// With onChange handler
<Tabs
  defaultValue="tab1"
  onValueChange={(value) => console.log(value)}
>
  {/* ... */}
</Tabs>
```

---

## Select

### Usage
```tsx
import Select from '@/components/ui/Select'

const options = [
  { value: 'us', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'ca', label: 'Canada' },
]

<Select
  label="Country"
  options={options}
  placeholder="Select a country"
  fullWidth
/>

// With error
<Select
  label="Industry"
  options={industries}
  error="Please select an industry"
  required
/>
```

---

## Table

### Usage
```tsx
import Table from '@/components/ui/Table'
import Badge from '@/components/ui/Badge'

const columns = [
  {
    key: 'name',
    label: 'Name',
    width: '30%',
  },
  {
    key: 'email',
    label: 'Email',
  },
  {
    key: 'status',
    label: 'Status',
    align: 'center' as const,
    render: (value) => (
      <Badge variant={value === 'active' ? 'success' : 'default'}>
        {value}
      </Badge>
    )
  },
  {
    key: 'actions',
    label: 'Actions',
    align: 'right' as const,
    render: (_, row) => (
      <Button size="sm" variant="ghost">Edit</Button>
    )
  },
]

const data = [
  { name: 'John Doe', email: 'john@example.com', status: 'active' },
  { name: 'Jane Smith', email: 'jane@example.com', status: 'inactive' },
]

<Table
  columns={columns}
  data={data}
  loading={isLoading}
  emptyMessage="No leads found"
  onRowClick={(row) => console.log(row)}
/>
```

---

## Toast Notifications

### Usage
```tsx
import { toast } from '@/components/ui/Toast'

// Success
toast.success('Campaign created successfully!')

// Error
toast.error('Failed to generate leads')

// Info
toast.info('Processing your request...')

// Warning
toast.warning('You have reached your quota limit')

// With custom duration
toast.success('Saved!', { duration: 5000 })

// Promise-based (for async operations)
toast.promise(
  saveData(),
  {
    loading: 'Saving...',
    success: 'Saved successfully!',
    error: 'Failed to save',
  }
)
```

---

## Skeleton Loaders

### Usage
```tsx
import Skeleton, {
  SkeletonCard,
  SkeletonTable,
  SkeletonList
} from '@/components/ui/Skeleton'

// Basic skeleton
<Skeleton variant="text" width="60%" height={20} />
<Skeleton variant="circular" width={48} height={48} />
<Skeleton variant="rectangular" width="100%" height={200} />

// Pre-built patterns
<SkeletonCard />
<SkeletonTable rows={5} />
<SkeletonList items={3} />

// Custom loading state
{isLoading ? (
  <Skeleton variant="rectangular" width="100%" height={300} />
) : (
  <YourComponent />
)}
```

---

## Layout Components

### DashboardLayout

Wraps all authenticated pages with sidebar and navbar.

```tsx
import DashboardLayout from '@/components/layout/DashboardLayout'

export default function MyPage() {
  return (
    <DashboardLayout>
      <h1>Page Title</h1>
      <p>Content here...</p>
    </DashboardLayout>
  )
}
```

### Sidebar

Automatically included in DashboardLayout. Shows:
- Logo
- Navigation items with icons
- Active state indicator
- Collapse/expand button (desktop)
- Mobile responsive drawer

### Navbar

Automatically included in DashboardLayout. Shows:
- Search bar
- Notifications bell
- User profile dropdown

---

## Utility Functions

### cn() - Class Name Merger
```tsx
import { cn } from '@/lib/utils'

// Merge classes with conditional logic
<div className={cn(
  'base-class',
  isActive && 'active-class',
  variant === 'primary' && 'primary-class'
)}>
  Content
</div>
```

### Formatting
```tsx
import {
  formatNumber,
  formatCurrency,
  formatDate,
  formatRelativeTime,
  truncate,
  getInitials
} from '@/lib/utils'

formatNumber(1234567) // "1,234,567"
formatCurrency(1234.56) // "$1,234.56"
formatDate(new Date()) // "Jan 1, 2024"
formatRelativeTime(yesterday) // "1 day ago"
truncate("Long text...", 10) // "Long text..."
getInitials("John Doe") // "JD"
```

---

## Icons

Using Lucide React icons throughout:

```tsx
import {
  Mail, Lock, User, Building2, Search, Bell,
  Plus, Edit, Trash, Download, Upload,
  Check, X, AlertCircle, Info,
  TrendingUp, TrendingDown, Activity,
  Settings, LogOut, Menu,
  // ... 1000+ more icons
} from 'lucide-react'

<Mail className="h-5 w-5 text-gray-600" />
```

Browse all icons: [lucide.dev](https://lucide.dev)

---

## Color Reference

Use Tailwind color classes:

```tsx
// Text colors
text-primary-600
text-success-600
text-warning-600
text-error-600

// Background colors
bg-primary-50
bg-success-100
bg-warning-100
bg-error-100

// Border colors
border-primary-300
border-gray-200

// Hover states
hover:bg-primary-700
hover:text-white
```

---

## Responsive Design

Tailwind breakpoints:
- **sm**: 640px (mobile landscape)
- **md**: 768px (tablet)
- **lg**: 1024px (desktop)
- **xl**: 1280px (large desktop)

```tsx
// Hide on mobile, show on desktop
<div className="hidden md:block">Desktop only</div>

// Stack on mobile, grid on desktop
<div className="flex flex-col md:grid md:grid-cols-3 gap-4">
  {/* ... */}
</div>

// Responsive text size
<h1 className="text-2xl md:text-4xl lg:text-5xl">
  Responsive Heading
</h1>
```

---

**For more examples, check the actual component files in `src/components/ui/`**
