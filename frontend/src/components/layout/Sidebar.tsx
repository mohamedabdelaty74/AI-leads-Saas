'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Users,
  FolderKanban,
  Sparkles,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Mail,
  FileText,
  Send,
  BarChart3,
  Zap,
  Upload,
  MessageCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  id: string
  label: string
  icon: React.ReactNode
  href: string
  badge?: string | number
}

interface SidebarProps {
  collapsed?: boolean
  onCollapse?: (collapsed: boolean) => void
}

const navItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <LayoutDashboard className="h-5 w-5" />,
    href: '/dashboard',
  },
  {
    id: 'automation',
    label: 'AI Automation',
    icon: <Zap className="h-5 w-5" />,
    href: '/automation',
    badge: 'NEW',
  },
  {
    id: 'import-enrich',
    label: 'Import & Enrich',
    icon: <Upload className="h-5 w-5" />,
    href: '/import-enrich',
    badge: 'NEW',
  },
  {
    id: 'leads',
    label: 'Lead Generation',
    icon: <Sparkles className="h-5 w-5" />,
    href: '/leads',
  },
  {
    id: 'campaigns',
    label: 'Campaigns',
    icon: <FolderKanban className="h-5 w-5" />,
    href: '/campaigns',
  },
  {
    id: 'email-templates',
    label: 'Email Templates',
    icon: <FileText className="h-5 w-5" />,
    href: '/emails/templates',
  },
  {
    id: 'email-compose',
    label: 'AI Email Composer',
    icon: <Sparkles className="h-5 w-5" />,
    href: '/emails/compose',
  },
  {
    id: 'email-send',
    label: 'Send Emails',
    icon: <Send className="h-5 w-5" />,
    href: '/emails/send',
  },
  {
    id: 'whatsapp-send',
    label: 'Send WhatsApp',
    icon: <MessageCircle className="h-5 w-5" />,
    href: '/whatsapp/send',
  },
  {
    id: 'email-analytics',
    label: 'Email Analytics',
    icon: <BarChart3 className="h-5 w-5" />,
    href: '/emails/analytics',
  },
  {
    id: 'team',
    label: 'Team',
    icon: <Users className="h-5 w-5" />,
    href: '/team',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <Settings className="h-5 w-5" />,
    href: '/settings',
  },
]

const Sidebar: React.FC<SidebarProps> = ({ collapsed = false, onCollapse }) => {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = () => {
    // Clear authentication tokens
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')

    // Redirect to login page
    router.push('/login')
  }

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 80 : 256 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed left-0 top-0 h-screen bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 z-40 flex flex-col"
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
            <span className="text-white font-bold text-lg">E</span>
          </div>
          {!collapsed && (
            <span className="font-bold text-lg text-gray-900 dark:text-gray-100">Elite Creatif</span>
          )}
        </Link>

        {onCollapse && (
          <button
            onClick={() => onCollapse(!collapsed)}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronLeft className="h-4 w-4 text-gray-500" />
            )}
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')

          return (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative',
                isActive
                  ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100'
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute inset-0 bg-primary-50 rounded-lg"
                  initial={false}
                  transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                />
              )}

              <span className="relative z-10">{item.icon}</span>

              {!collapsed && (
                <>
                  <span className="relative z-10 font-medium">{item.label}</span>
                  {item.badge && (
                    <span className="relative z-10 ml-auto px-2 py-0.5 text-xs font-medium bg-primary-100 text-primary-700 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
          )
        })}
      </nav>

      {/* User Section */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={handleLogout}
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100 transition-colors',
            collapsed && 'justify-center'
          )}
        >
          <LogOut className="h-5 w-5" />
          {!collapsed && <span className="font-medium">Logout</span>}
        </button>
      </div>
    </motion.aside>
  )
}

export default Sidebar
