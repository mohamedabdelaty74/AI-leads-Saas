'use client'

import React from 'react'
import { Toaster as HotToaster, toast as hotToast, ToastBar } from 'react-hot-toast'
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ToastOptions {
  duration?: number
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right'
}

const toastIcons = {
  success: <CheckCircle2 className="h-5 w-5 text-success-600" />,
  error: <XCircle className="h-5 w-5 text-error-600" />,
  info: <Info className="h-5 w-5 text-info-600" />,
  warning: <AlertTriangle className="h-5 w-5 text-warning-600" />,
}

const toastStyles = {
  success: 'border-success-200 bg-success-50',
  error: 'border-error-200 bg-error-50',
  info: 'border-info-200 bg-info-50',
  warning: 'border-warning-200 bg-warning-50',
}

export const toast = {
  success: (message: string, options?: ToastOptions) => {
    hotToast.custom(
      (t) => (
        <div
          className={cn(
            'flex items-center gap-3 p-4 rounded-lg border-2 shadow-lg min-w-[300px]',
            toastStyles.success,
            t.visible ? 'animate-slide-in-right' : 'opacity-0'
          )}
        >
          {toastIcons.success}
          <span className="flex-1 text-sm font-medium text-gray-900">{message}</span>
          <button
            onClick={() => hotToast.dismiss(t.id)}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ),
      { duration: options?.duration || 3000, position: options?.position || 'top-right' }
    )
  },

  error: (message: string, options?: ToastOptions) => {
    hotToast.custom(
      (t) => (
        <div
          className={cn(
            'flex items-center gap-3 p-4 rounded-lg border-2 shadow-lg min-w-[300px]',
            toastStyles.error,
            t.visible ? 'animate-slide-in-right' : 'opacity-0'
          )}
        >
          {toastIcons.error}
          <span className="flex-1 text-sm font-medium text-gray-900">{message}</span>
          <button
            onClick={() => hotToast.dismiss(t.id)}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ),
      { duration: options?.duration || 4000, position: options?.position || 'top-right' }
    )
  },

  info: (message: string, options?: ToastOptions) => {
    hotToast.custom(
      (t) => (
        <div
          className={cn(
            'flex items-center gap-3 p-4 rounded-lg border-2 shadow-lg min-w-[300px]',
            toastStyles.info,
            t.visible ? 'animate-slide-in-right' : 'opacity-0'
          )}
        >
          {toastIcons.info}
          <span className="flex-1 text-sm font-medium text-gray-900">{message}</span>
          <button
            onClick={() => hotToast.dismiss(t.id)}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ),
      { duration: options?.duration || 3000, position: options?.position || 'top-right' }
    )
  },

  warning: (message: string, options?: ToastOptions) => {
    hotToast.custom(
      (t) => (
        <div
          className={cn(
            'flex items-center gap-3 p-4 rounded-lg border-2 shadow-lg min-w-[300px]',
            toastStyles.warning,
            t.visible ? 'animate-slide-in-right' : 'opacity-0'
          )}
        >
          {toastIcons.warning}
          <span className="flex-1 text-sm font-medium text-gray-900">{message}</span>
          <button
            onClick={() => hotToast.dismiss(t.id)}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ),
      { duration: options?.duration || 3000, position: options?.position || 'top-right' }
    )
  },

  promise: hotToast.promise,
  dismiss: hotToast.dismiss,
}

// Toaster Provider Component
export const ToastProvider: React.FC = () => {
  return <HotToaster position="top-right" />
}

export default toast
