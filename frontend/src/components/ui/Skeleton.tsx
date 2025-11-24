import React, { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
  className?: string
}

const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'rectangular',
  width,
  height,
  className,
  ...props
}) => {
  const variants = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-md',
  }

  const style: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  }

  return (
    <div
      className={cn(
        'skeleton bg-gray-200',
        variants[variant],
        !width && 'w-full',
        !height && variant === 'text' && 'h-4',
        !height && variant === 'rectangular' && 'h-20',
        !height && variant === 'circular' && 'h-12 w-12',
        className
      )}
      style={style}
      aria-busy="true"
      aria-live="polite"
      {...props}
    />
  )
}

// Skeleton components for common UI patterns
export const SkeletonCard: React.FC = () => (
  <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
    <Skeleton variant="text" width="60%" height={24} />
    <Skeleton variant="text" width="100%" height={16} />
    <Skeleton variant="text" width="80%" height={16} />
    <div className="flex gap-2 mt-4">
      <Skeleton variant="rectangular" width={100} height={36} />
      <Skeleton variant="rectangular" width={100} height={36} />
    </div>
  </div>
)

export const SkeletonTable: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
    <div className="border-b border-gray-200 p-4">
      <div className="flex gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} variant="text" width="20%" height={16} />
        ))}
      </div>
    </div>
    <div className="divide-y divide-gray-200">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-4">
          <div className="flex gap-4">
            {[1, 2, 3, 4].map((j) => (
              <Skeleton key={j} variant="text" width="20%" height={16} />
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
)

export const SkeletonList: React.FC<{ items?: number }> = ({ items = 3 }) => (
  <div className="space-y-3">
    {Array.from({ length: items }).map((_, i) => (
      <div key={i} className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="40%" height={16} />
          <Skeleton variant="text" width="60%" height={14} />
        </div>
      </div>
    ))}
  </div>
)

export default Skeleton
