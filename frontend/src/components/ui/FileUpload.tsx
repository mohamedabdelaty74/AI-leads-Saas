import React, { useRef, useState, DragEvent, ChangeEvent } from 'react'
import { cn } from '@/lib/utils'
import { Upload, File, X, CheckCircle2, AlertCircle } from 'lucide-react'

export interface FileUploadProps {
  onFileSelect: (file: File) => void
  accept?: string
  maxSizeMB?: number
  disabled?: boolean
  className?: string
}

export default function FileUpload({
  onFileSelect,
  accept = '.csv,.xlsx,.xls',
  maxSizeMB = 10,
  disabled = false,
  className
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    const acceptedTypes = accept.split(',').map(t => t.trim())

    if (!acceptedTypes.includes(fileExtension)) {
      return `File type not supported. Please upload: ${accept}`
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024)
    if (fileSizeMB > maxSizeMB) {
      return `File size exceeds ${maxSizeMB}MB limit`
    }

    return null
  }

  const handleFile = (file: File) => {
    const validationError = validateFile(file)

    if (validationError) {
      setError(validationError)
      setSelectedFile(null)
      return
    }

    setError(null)
    setSelectedFile(file)
    onFileSelect(file)
  }

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFile(files[0])
    }
  }

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedFile(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className={cn('w-full', className)}>
      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'relative border-2 border-dashed rounded-lg transition-all duration-200 cursor-pointer',
          'hover:border-primary-400 hover:bg-primary-50/50',
          isDragging && 'border-primary-500 bg-primary-50 scale-[1.02]',
          disabled && 'opacity-50 cursor-not-allowed hover:border-gray-300 hover:bg-transparent',
          error && 'border-error-300 bg-error-50',
          selectedFile && !error && 'border-success-300 bg-success-50',
          !selectedFile && !error && !isDragging && 'border-gray-300 bg-gray-50'
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInputChange}
          disabled={disabled}
          className="hidden"
        />

        <div className="p-8 text-center">
          {selectedFile && !error ? (
            // File selected state
            <div className="space-y-3">
              <div className="flex items-center justify-center">
                <CheckCircle2 className="w-12 h-12 text-success-500" />
              </div>
              <div>
                <p className="font-semibold text-gray-900 flex items-center justify-center gap-2">
                  <File className="w-4 h-4" />
                  {selectedFile.name}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
              <button
                onClick={handleRemove}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
              >
                <X className="w-4 h-4" />
                Remove file
              </button>
            </div>
          ) : error ? (
            // Error state
            <div className="space-y-3">
              <div className="flex items-center justify-center">
                <AlertCircle className="w-12 h-12 text-error-500" />
              </div>
              <div>
                <p className="font-semibold text-error-700">Upload Failed</p>
                <p className="text-sm text-error-600 mt-1">{error}</p>
              </div>
              <button
                onClick={handleRemove}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              >
                Try again
              </button>
            </div>
          ) : (
            // Default state
            <div className="space-y-3">
              <div className="flex items-center justify-center">
                <Upload className={cn(
                  'w-12 h-12 transition-colors',
                  isDragging ? 'text-primary-500' : 'text-gray-400'
                )} />
              </div>
              <div>
                <p className="text-lg font-semibold text-gray-900">
                  {isDragging ? 'Drop your file here' : 'Upload CSV or Excel file'}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Drag and drop or{' '}
                  <span className="text-primary-600 font-medium">browse</span>
                </p>
              </div>
              <div className="text-xs text-gray-500 space-y-1">
                <p>Supported formats: {accept.replace(/\./g, '').toUpperCase()}</p>
                <p>Maximum file size: {maxSizeMB}MB</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
