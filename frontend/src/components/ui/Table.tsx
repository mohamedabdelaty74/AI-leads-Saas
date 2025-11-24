import React from 'react'
import { cn } from '@/lib/utils'

interface Column<T = any> {
  key: string
  label: string
  sortable?: boolean
  render?: (value: any, row: T, index: number) => React.ReactNode
  width?: string
  align?: 'left' | 'center' | 'right'
}

interface TableProps<T = any> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  emptyMessage?: string
  onRowClick?: (row: T, index: number) => void
  className?: string
}

function Table<T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  emptyMessage = 'No data available',
  onRowClick,
  className,
}: TableProps<T>) {
  const alignmentClasses = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  }

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="animate-pulse space-y-4 p-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    )
  }

  if (!data.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-12">
        <div className="text-center">
          <p className="text-gray-500">{emptyMessage}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('bg-white border border-gray-200 rounded-lg overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <table className="w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={cn(
                    'px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider',
                    alignmentClasses[column.align || 'left']
                  )}
                  style={{ width: column.width }}
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                onClick={() => onRowClick?.(row, rowIndex)}
                className={cn(
                  'transition-colors',
                  onRowClick && 'cursor-pointer hover:bg-gray-50'
                )}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={cn(
                      'px-6 py-4 whitespace-nowrap text-sm text-gray-900',
                      alignmentClasses[column.align || 'left']
                    )}
                  >
                    {column.render
                      ? column.render(row[column.key], row, rowIndex)
                      : row[column.key] || '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Table
