import React, { forwardRef, SelectHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  label?: string
  error?: string
  helperText?: string
  options?: SelectOption[]
  fullWidth?: boolean
  placeholder?: string
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      className,
      label,
      error,
      helperText,
      options,
      fullWidth = false,
      disabled,
      placeholder,
      id,
      children,
      ...props
    },
    ref
  ) => {
    const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`

    const baseStyles = 'h-10 pl-4 pr-10 rounded-md border transition-all duration-200 bg-white text-gray-900 appearance-none cursor-pointer'
    const focusStyles = 'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
    const errorStyles = error ? 'border-error-500 focus:ring-error-500' : 'border-gray-300'
    const disabledStyles = disabled ? 'bg-gray-100 cursor-not-allowed opacity-60' : ''

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={selectId}
            className="text-sm font-medium text-gray-700"
          >
            {label}
            {props.required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={cn(
              baseStyles,
              focusStyles,
              errorStyles,
              disabledStyles,
              fullWidth && 'w-full',
              className
            )}
            disabled={disabled}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options ? options.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            )) : children}
          </select>

          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
        </div>

        {error && (
          <p id={`${selectId}-error`} className="text-sm text-error-500">
            {error}
          </p>
        )}

        {helperText && !error && (
          <p id={`${selectId}-helper`} className="text-sm text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'

export default Select
