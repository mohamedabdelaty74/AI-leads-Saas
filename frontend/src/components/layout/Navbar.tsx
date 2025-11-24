'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Bell, Search, Menu, User, Sparkles, Mail, AlertCircle, Settings, LogOut, Moon, Sun } from 'lucide-react'
import { cn } from '@/lib/utils'
import Badge from '@/components/ui/Badge'
import { useTheme } from '@/contexts/ThemeContext'

interface Notification {
  id: string
  type: string
  title: string
  message: string
  time_ago: string
  campaign_id?: string
  read: boolean
}

interface NavbarProps {
  onMenuClick?: () => void
  showMenuButton?: boolean
}

interface UserData {
  first_name?: string
  last_name?: string
  email: string
  role: string
  company_name?: string
}

const Navbar: React.FC<NavbarProps> = ({ onMenuClick, showMenuButton = false }) => {
  const router = useRouter()
  const { theme, toggleTheme } = useTheme()
  const [showNotifications, setShowNotifications] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [userData, setUserData] = useState<UserData | null>(null)

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  const fetchNotifications = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      if (!token) return

      const response = await fetch('http://localhost:8000/api/v1/notifications', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setNotifications(data.notifications || [])
        setUnreadCount(data.unread_count || 0)
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchUserData = async () => {
    try {
      // First try to get from localStorage
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        const parsed = JSON.parse(storedUser)
        setUserData(parsed)
        return
      }

      // If not in localStorage, fetch from API
      const token = localStorage.getItem('access_token')
      if (!token) return

      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setUserData(data)
        // Store in localStorage for future use
        localStorage.setItem('user', JSON.stringify(data))
      }
    } catch (error) {
      console.error('Failed to fetch user data:', error)
    }
  }

  useEffect(() => {
    fetchNotifications()
    fetchUserData()
    // Refresh notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'leads_generated':
        return <Sparkles className="h-4 w-4 text-primary-600" />
      case 'emails_sent':
        return <Mail className="h-4 w-4 text-green-600" />
      case 'info':
        return <AlertCircle className="h-4 w-4 text-gray-400" />
      default:
        return <Sparkles className="h-4 w-4 text-primary-600" />
    }
  }

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 fixed top-0 right-0 left-0 md:left-64 z-30">
      <div className="h-full px-4 md:px-6 flex items-center justify-between">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          {showMenuButton && (
            <button
              onClick={onMenuClick}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors md:hidden"
              aria-label="Toggle menu"
            >
              <Menu className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </button>
          )}

          {/* Search */}
          <div className="hidden md:flex items-center">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search leads, campaigns..."
                className="w-64 lg:w-96 h-9 pl-10 pr-4 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-3">
          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => {
                setShowNotifications(!showNotifications)
                if (!showNotifications) {
                  fetchNotifications()
                }
              }}
              className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-error-500 rounded-full" />
              )}
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <div className="absolute right-0 top-12 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Notifications</h3>
                  {unreadCount > 0 && (
                    <span className="text-xs text-gray-500">{unreadCount} unread</span>
                  )}
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {loading ? (
                    <div className="p-4 text-center text-sm text-gray-500">
                      Loading...
                    </div>
                  ) : notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={cn(
                          "p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700",
                          !notification.read && "bg-primary-50/30 dark:bg-primary-900/20"
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <div className={cn(
                            "h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0",
                            notification.type === 'leads_generated' && "bg-primary-100 dark:bg-primary-900/50",
                            notification.type === 'emails_sent' && "bg-green-100 dark:bg-green-900/50",
                            notification.type === 'info' && "bg-gray-100 dark:bg-gray-700"
                          )}>
                            {getNotificationIcon(notification.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-900 dark:text-gray-100 font-medium">
                              {notification.title}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {notification.message}
                            </p>
                            {notification.time_ago && (
                              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{notification.time_ago}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
                      No notifications
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User Menu */}
          <div className="relative flex items-center gap-2 pl-3 border-l border-gray-200 dark:border-gray-700">
            <button
              onClick={() => {
                setShowUserMenu(!showUserMenu)
                setShowNotifications(false)
              }}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {userData?.first_name ? userData.first_name.charAt(0).toUpperCase() : <User className="h-4 w-4" />}
                </span>
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {userData ? `${userData.first_name || ''} ${userData.last_name || ''}`.trim() || 'User' : 'Loading...'}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                  {userData?.role || 'User'}
                </p>
              </div>
            </button>

            {/* User Dropdown */}
            {showUserMenu && (
              <div className="absolute right-0 top-12 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden z-50">
                <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {userData ? `${userData.first_name || ''} ${userData.last_name || ''}`.trim() || 'User' : 'User'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {userData?.email || ''}
                  </p>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => {
                      toggleTheme()
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    {theme === 'light' ? (
                      <>
                        <Moon className="h-4 w-4" />
                        Dark Mode
                      </>
                    ) : (
                      <>
                        <Sun className="h-4 w-4" />
                        Light Mode
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setShowUserMenu(false)
                      router.push('/settings')
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Settings className="h-4 w-4" />
                    Settings
                  </button>
                  <button
                    onClick={() => {
                      setShowUserMenu(false)
                      handleLogout()
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Navbar
