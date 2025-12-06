'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import FileUpload from '@/components/ui/FileUpload'
import { toast } from 'react-hot-toast'
import {
  Upload,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileText,
  ArrowRight
} from 'lucide-react'

interface CSVImporterProps {
  campaignId: string
  onSuccess: () => void
}

interface PreviewData {
  headers: string[]
  rows: any[][]
  totalRows: number
}

interface ProcessResult {
  success: boolean
  message: string
  stats: {
    total_rows: number
    leads_created: number
    leads_failed: number
    descriptions_generated: number
    emails_generated: number
  }
  failed_rows?: Array<{ row: number; reason: string }>
  campaign_id: string
}

export default function CSVImporter({ campaignId, onSuccess }: CSVImporterProps) {
  const router = useRouter()
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [generateDescriptions, setGenerateDescriptions] = useState(true)
  const [generateEmails, setGenerateEmails] = useState(true)
  const [companyInfo, setCompanyInfo] = useState('')
  const [processing, setProcessing] = useState(false)
  const [processingStatus, setProcessingStatus] = useState('')
  const [processResult, setProcessResult] = useState<ProcessResult | null>(null)
  const [currentStep, setCurrentStep] = useState<'upload' | 'configure' | 'results'>('upload')
  const [processingProgress, setProcessingProgress] = useState(0)
  const [estimatedTime, setEstimatedTime] = useState<string>('')

  const handleFileSelect = async (file: File) => {
    setUploadedFile(file)
    setProcessResult(null)

    // Parse CSV for preview
    try {
      const text = await file.text()
      const lines = text.split('\n').filter(line => line.trim())

      if (lines.length === 0) {
        toast.error('File is empty')
        return
      }

      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
      const rows = lines.slice(1, Math.min(6, lines.length)).map(line => {
        return line.split(',').map(cell => cell.trim().replace(/"/g, ''))
      })

      setPreviewData({
        headers,
        rows,
        totalRows: lines.length - 1
      })

      setCurrentStep('configure')
      toast.success(`Parsed ${lines.length - 1} rows from CSV`)
    } catch (error) {
      console.error('Error parsing CSV:', error)
      toast.error('Failed to parse CSV file')
    }
  }

  const handleProcess = async () => {
    if (!uploadedFile) {
      toast.error('Please select a file first')
      return
    }

    if (generateEmails && !companyInfo.trim()) {
      toast.error('Company information is required for email generation')
      return
    }

    setProcessing(true)
    setProcessResult(null)
    setProcessingProgress(0)
    setProcessingStatus('Preparing upload...')

    // Calculate estimated time
    const estimatedMinutes = previewData
      ? Math.ceil(previewData.totalRows * (generateDescriptions ? 0.5 : 0.1))
      : 5
    setEstimatedTime(`Estimated time: ${estimatedMinutes} minute${estimatedMinutes > 1 ? 's' : ''}`)

    // Progress simulation
    const progressInterval = setInterval(() => {
      setProcessingProgress(prev => {
        if (prev >= 90) return prev
        return prev + Math.random() * 10
      })
    }, 2000)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        clearInterval(progressInterval)
        router.push('/login')
        return
      }

      setProcessingStatus('Uploading CSV file...')
      setProcessingProgress(10)
      const formData = new FormData()
      formData.append('file', uploadedFile)

      const url = new URL(`http://localhost:8000/api/v1/campaigns/${campaignId}/upload-leads`)
      url.searchParams.append('generate_descriptions', generateDescriptions.toString())
      url.searchParams.append('generate_emails', generateEmails.toString())
      if (generateEmails && companyInfo.trim()) {
        url.searchParams.append('company_info', companyInfo.trim())
      }

      setProcessingStatus('Parsing CSV and validating data...')
      setProcessingProgress(20)

      if (generateDescriptions) {
        setProcessingStatus('Searching Google for real-time company data...')
        setProcessingProgress(30)
      }

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      if (generateDescriptions) {
        setProcessingStatus('Generating AI business research reports...')
        setProcessingProgress(50)
      } else if (generateEmails) {
        setProcessingStatus('Generating personalized emails...')
        setProcessingProgress(50)
      }

      const data: ProcessResult = await response.json()

      setProcessingStatus('Finalizing import...')
      setProcessingProgress(95)

      clearInterval(progressInterval)
      setProcessingProgress(100)

      setProcessResult(data)
      setCurrentStep('results')

      if (data.stats.leads_created > 0) {
        toast.success(`Successfully imported ${data.stats.leads_created} leads!`)
      }

      if (data.stats.leads_failed > 0) {
        toast.error(`${data.stats.leads_failed} rows failed to import`)
      }

      // Call onSuccess after a short delay to show results
      setTimeout(() => {
        onSuccess()
      }, 2000)

    } catch (error: any) {
      console.error('Error uploading file:', error)
      toast.error(error.message || 'Failed to process file')
      clearInterval(progressInterval)
    } finally {
      setProcessing(false)
    }
  }

  const handleReset = () => {
    setUploadedFile(null)
    setPreviewData(null)
    setGenerateDescriptions(false)
    setGenerateEmails(false)
    setCompanyInfo('')
    setProcessResult(null)
    setCurrentStep('upload')
    setProcessingProgress(0)
    setEstimatedTime('')
  }

  return (
    <div className="space-y-6">
      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-4">
        <div className={`flex items-center gap-2 ${currentStep === 'upload' ? 'text-primary-600 font-semibold' : currentStep === 'configure' || currentStep === 'results' ? 'text-success-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'upload' ? 'bg-primary-100 border-2 border-primary-600' : currentStep === 'configure' || currentStep === 'results' ? 'bg-success-100 border-2 border-success-600' : 'bg-gray-100 border-2 border-gray-300'}`}>
            {currentStep === 'configure' || currentStep === 'results' ? <CheckCircle2 className="w-5 h-5" /> : '1'}
          </div>
          <span>Upload File</span>
        </div>

        <ArrowRight className="w-5 h-5 text-gray-400" />

        <div className={`flex items-center gap-2 ${currentStep === 'configure' ? 'text-primary-600 font-semibold' : currentStep === 'results' ? 'text-success-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'configure' ? 'bg-primary-100 border-2 border-primary-600' : currentStep === 'results' ? 'bg-success-100 border-2 border-success-600' : 'bg-gray-100 border-2 border-gray-300'}`}>
            {currentStep === 'results' ? <CheckCircle2 className="w-5 h-5" /> : '2'}
          </div>
          <span>Configure & Process</span>
        </div>

        <ArrowRight className="w-5 h-5 text-gray-400" />

        <div className={`flex items-center gap-2 ${currentStep === 'results' ? 'text-primary-600 font-semibold' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'results' ? 'bg-primary-100 border-2 border-primary-600' : 'bg-gray-100 border-2 border-gray-300'}`}>
            3
          </div>
          <span>View Results</span>
        </div>
      </div>

      {/* Step 1: Upload File */}
      {currentStep === 'upload' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Upload Lead Data
            </CardTitle>
            <CardDescription>
              Upload a CSV or Excel file containing your lead information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FileUpload
              onFileSelect={handleFileSelect}
              accept=".csv,.xlsx,.xls"
              maxSizeMB={10}
            />

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Required CSV Format
              </h4>
              <ul className="text-sm text-blue-800 space-y-1 ml-6 list-disc">
                <li>Must include a column for company name (Name, Company, Title, or Business)</li>
                <li>Optional columns: Email, Phone, Address, Website</li>
                <li>First row should contain column headers</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Configure & Preview */}
      {currentStep === 'configure' && previewData && (
        <div className="space-y-6">
          {/* Preview */}
          <Card>
            <CardHeader>
              <CardTitle>Data Preview</CardTitle>
              <CardDescription>
                Showing first 5 rows of {previewData.totalRows} total rows
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      {previewData.headers.map((header, idx) => (
                        <th key={idx} className="border border-gray-200 px-4 py-2 text-left text-sm font-semibold text-gray-700">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.rows.map((row, rowIdx) => (
                      <tr key={rowIdx} className="hover:bg-gray-50">
                        {row.map((cell, cellIdx) => (
                          <td key={cellIdx} className="border border-gray-200 px-4 py-2 text-sm text-gray-600">
                            {cell || '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                AI Enrichment Configuration
              </CardTitle>
              <CardDescription>
                Select which AI features to apply to your imported leads
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* AI Options */}
              <div className="space-y-4">
                <div className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <input
                    type="checkbox"
                    id="generateDescriptions"
                    checked={generateDescriptions}
                    onChange={(e) => setGenerateDescriptions(e.target.checked)}
                    className="mt-1 w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                  />
                  <label htmlFor="generateDescriptions" className="flex-1 cursor-pointer">
                    <div className="font-semibold text-gray-900">Generate AI Descriptions</div>
                    <div className="text-sm text-gray-600">
                      Automatically create professional company descriptions for each lead
                    </div>
                  </label>
                </div>

                <div className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <input
                    type="checkbox"
                    id="generateEmails"
                    checked={generateEmails}
                    onChange={(e) => setGenerateEmails(e.target.checked)}
                    className="mt-1 w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                  />
                  <label htmlFor="generateEmails" className="flex-1 cursor-pointer">
                    <div className="font-semibold text-gray-900">Generate Personalized Emails</div>
                    <div className="text-sm text-gray-600">
                      Create custom outreach emails for each lead based on your company info
                    </div>
                  </label>
                </div>

                {generateEmails && (
                  <div className="ml-8 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Your Company Information *
                    </label>
                    <textarea
                      value={companyInfo}
                      onChange={(e) => setCompanyInfo(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                      rows={4}
                      placeholder="Example: We are Elite Creatif, a digital marketing agency based in Dubai. We specialize in SEO, social media management, and targeted advertising..."
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      AI uses this to introduce your company and explain your services to each lead
                    </p>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  onClick={handleProcess}
                  disabled={processing}
                  className="flex-1"
                >
                  {processing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing... {Math.round(processingProgress)}%
                    </>
                  ) : (
                    'Process & Import'
                  )}
                </Button>
                <Button
                  onClick={handleReset}
                  variant="outline"
                  disabled={processing}
                >
                  Cancel
                </Button>
              </div>

              {/* Processing Status */}
              {processing && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>{processingStatus}</span>
                    <span>{estimatedTime}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${processingProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 3: Results */}
      {currentStep === 'results' && processResult && (
        <Card className={processResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}>
          <CardContent className="py-6">
            <div className="flex items-start gap-3">
              {processResult.success ? (
                <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
              )}
              <div className="flex-1">
                <h3 className={`font-semibold mb-3 ${processResult.success ? 'text-green-900' : 'text-red-900'}`}>
                  {processResult.message}
                </h3>

                {processResult.success && processResult.stats && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{processResult.stats.leads_created}</p>
                      <p className="text-xs text-gray-600">Leads Created</p>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <p className="text-2xl font-bold text-purple-600">{processResult.stats.descriptions_generated}</p>
                      <p className="text-xs text-gray-600">Descriptions</p>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <p className="text-2xl font-bold text-indigo-600">{processResult.stats.emails_generated}</p>
                      <p className="text-xs text-gray-600">Emails Generated</p>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <p className="text-2xl font-bold text-red-600">{processResult.stats.leads_failed}</p>
                      <p className="text-xs text-gray-600">Failed</p>
                    </div>
                  </div>
                )}

                <div className="mt-4 flex gap-3">
                  <Button onClick={onSuccess} variant="primary">
                    View Leads
                  </Button>
                  <Button onClick={handleReset} variant="outline">
                    Import More Leads
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
