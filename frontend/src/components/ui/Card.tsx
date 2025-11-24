import React, { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  hover?: boolean
  clickable?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, hover = false, clickable = false, padding = 'md', ...props }, ref) => {
    const paddingStyles = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    }

    return (
      <div
        ref={ref}
        className={cn(
          'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm',
          paddingStyles[padding],
          hover && 'transition-all duration-300 hover:shadow-md hover:-translate-y-0.5',
          clickable && 'cursor-pointer',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

export const CardHeader = ({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex flex-col space-y-1.5 mb-4', className)} {...props}>
    {children}
  </div>
)

export const CardTitle = ({ className, children, ...props }: HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={cn('text-xl font-semibold text-gray-900 dark:text-gray-100', className)} {...props}>
    {children}
  </h3>
)

export const CardDescription = ({ className, children, ...props }: HTMLAttributes<HTMLParagraphElement>) => (
  <p className={cn('text-sm text-gray-600 dark:text-gray-400', className)} {...props}>
    {children}
  </p>
)

export const CardContent = ({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn(className)} {...props}>
    {children}
  </div>
)

export const CardFooter = ({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex items-center gap-2 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700', className)} {...props}>
    {children}
  </div>
)

export default Card
