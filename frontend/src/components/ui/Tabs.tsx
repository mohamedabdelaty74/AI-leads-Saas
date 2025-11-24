'use client'

import React, { createContext, useContext, useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface TabsContextType {
  activeTab: string
  setActiveTab: (value: string) => void
}

const TabsContext = createContext<TabsContextType | undefined>(undefined)

const useTabsContext = () => {
  const context = useContext(TabsContext)
  if (!context) {
    throw new Error('Tabs components must be used within a Tabs provider')
  }
  return context
}

interface TabsProps {
  defaultValue: string
  children: React.ReactNode
  className?: string
  onValueChange?: (value: string) => void
}

export const Tabs: React.FC<TabsProps> = ({
  defaultValue,
  children,
  className,
  onValueChange,
}) => {
  const [activeTab, setActiveTab] = useState(defaultValue)

  const handleTabChange = (value: string) => {
    setActiveTab(value)
    onValueChange?.(value)
  }

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleTabChange }}>
      <div className={cn('w-full', className)}>{children}</div>
    </TabsContext.Provider>
  )
}

interface TabsListProps {
  children: React.ReactNode
  className?: string
}

export const TabsList: React.FC<TabsListProps> = ({ children, className }) => {
  return (
    <div
      className={cn(
        'inline-flex h-10 items-center justify-start rounded-lg bg-gray-100 p-1 gap-1',
        className
      )}
      role="tablist"
    >
      {children}
    </div>
  )
}

interface TabsTriggerProps {
  value: string
  children: React.ReactNode
  disabled?: boolean
  className?: string
  icon?: React.ReactNode
}

export const TabsTrigger: React.FC<TabsTriggerProps> = ({
  value,
  children,
  disabled = false,
  className,
  icon,
}) => {
  const { activeTab, setActiveTab } = useTabsContext()
  const isActive = activeTab === value

  return (
    <button
      onClick={() => !disabled && setActiveTab(value)}
      disabled={disabled}
      role="tab"
      aria-selected={isActive}
      aria-controls={`tabpanel-${value}`}
      className={cn(
        'relative inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium transition-all',
        'focus-ring disabled:pointer-events-none disabled:opacity-50',
        isActive
          ? 'text-gray-900'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50',
        className
      )}
    >
      {isActive && (
        <motion.div
          layoutId="activeTab"
          className="absolute inset-0 bg-white rounded-md shadow-sm"
          initial={false}
          transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
        />
      )}
      <span className="relative z-10 inline-flex items-center gap-2">
        {icon}
        {children}
      </span>
    </button>
  )
}

interface TabsContentProps {
  value: string
  children: React.ReactNode
  className?: string
}

export const TabsContent: React.FC<TabsContentProps> = ({
  value,
  children,
  className,
}) => {
  const { activeTab } = useTabsContext()

  if (activeTab !== value) return null

  return (
    <motion.div
      id={`tabpanel-${value}`}
      role="tabpanel"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.3 }}
      className={cn('mt-4', className)}
    >
      {children}
    </motion.div>
  )
}
