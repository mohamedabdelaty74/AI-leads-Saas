import React, { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'primary'
export type BadgeSize = 'sm' | 'md' | 'lg'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: BadgeSize
  dot?: boolean
  children: React.ReactNode
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', dot = false, children, ...props }, ref) => {
    const variants: Record<BadgeVariant, string> = {
      default: 'bg-gray-100 text-gray-700 border-gray-200',
      success: 'bg-success-100 text-success-700 border-success-200',
      warning: 'bg-warning-100 text-warning-700 border-warning-200',
      error: 'bg-error-100 text-error-700 border-error-200',
      info: 'bg-info-100 text-info-700 border-info-200',
      primary: 'bg-primary-100 text-primary-700 border-primary-200',
    }

    const sizes: Record<BadgeSize, string> = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-sm',
      lg: 'px-3 py-1.5 text-base',
    }

    const dotColors: Record<BadgeVariant, string> = {
      default: 'bg-gray-500',
      success: 'bg-success-500',
      warning: 'bg-warning-500',
      error: 'bg-error-500',
      info: 'bg-info-500',
      primary: 'bg-primary-500',
    }

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center gap-1.5 font-medium rounded-full border transition-colors',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span className={cn('w-1.5 h-1.5 rounded-full', dotColors[variant])} aria-hidden="true" />
        )}
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'

export default Badge
