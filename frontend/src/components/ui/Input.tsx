import React, { forwardRef, InputHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'
import { AlertCircle } from 'lucide-react'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  fullWidth?: boolean
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`

    const baseStyles = 'h-10 px-4 rounded-md border transition-all duration-200 bg-white text-gray-900 placeholder:text-gray-400'
    const focusStyles = 'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
    const errorStyles = error ? 'border-error-500 focus:ring-error-500' : 'border-gray-300'
    const disabledStyles = disabled ? 'bg-gray-100 cursor-not-allowed opacity-60' : ''
    const iconPadding = leftIcon ? 'pl-10' : rightIcon ? 'pr-10' : ''

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-gray-700"
          >
            {label}
            {props.required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            className={cn(
              baseStyles,
              focusStyles,
              errorStyles,
              disabledStyles,
              iconPadding,
              fullWidth && 'w-full',
              className
            )}
            disabled={disabled}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
            {...props}
          />

          {rightIcon && !error && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              {rightIcon}
            </div>
          )}

          {error && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-error-500">
              <AlertCircle className="h-5 w-5" />
            </div>
          )}
        </div>

        {error && (
          <p id={`${inputId}-error`} className="text-sm text-error-500 flex items-center gap-1">
            {error}
          </p>
        )}

        {helperText && !error && (
          <p id={`${inputId}-helper`} className="text-sm text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input
