// UI Component Types

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

export type InputType = 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'

export type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastConfig {
  type: ToastType
  message: string
  duration?: number
}

// Tab System
export interface Tab {
  id: string
  label: string
  icon?: React.ReactNode
  content: React.ReactNode
  disabled?: boolean
}

// Table
export interface Column<T = any> {
  key: string
  label: string
  sortable?: boolean
  render?: (value: any, row: T) => React.ReactNode
  width?: string
}

export interface TableProps<T = any> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  emptyMessage?: string
  onRowClick?: (row: T) => void
}

// Chart Data
export interface ChartDataPoint {
  label: string
  value: number
  color?: string
}

export interface TimeSeriesData {
  date: string
  value: number
}

// Stat Card
export interface StatCardData {
  label: string
  value: string | number
  change?: number
  changeLabel?: string
  icon?: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
}

// Form
export interface FormField {
  name: string
  label: string
  type: InputType
  placeholder?: string
  required?: boolean
  validation?: any
  defaultValue?: any
  helperText?: string
}

// Notification
export interface Notification {
  id: string
  title: string
  message: string
  type: ToastType
  read: boolean
  created_at: string
  action_url?: string
}

// Sidebar Navigation
export interface NavItem {
  id: string
  label: string
  icon: React.ReactNode
  href: string
  badge?: string | number
  children?: NavItem[]
  disabled?: boolean
}

// Settings
export interface SettingsSection {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  fields: FormField[]
}

// File Upload
export interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  url: string
  uploaded_at: string
}

// Activity Log
export interface ActivityLog {
  id: string
  user_name: string
  action: string
  resource: string
  timestamp: string
  details?: Record<string, any>
}

// Dashboard Widget
export interface DashboardWidget {
  id: string
  title: string
  type: 'stat' | 'chart' | 'table' | 'list'
  data: any
  span?: number // Grid column span
}
