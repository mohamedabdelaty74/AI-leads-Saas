'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import FileUpload from '@/components/ui/FileUpload'
import Button from '@/components/ui/Button'
import { toast } from 'react-hot-toast'
import { Upload, Sparkles, ArrowRight, CheckCircle2, AlertCircle, FileText, Loader2 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Campaign {
  id: string
  name: string
  description?: string
  status: string
  lead_source: string
  leads_count: number
  created_at: string
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

export default function ImportEnrichPage() {
  const router = useRouter()
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('')
  const [generateDescriptions, setGenerateDescriptions] = useState(false)
  const [generateEmails, setGenerateEmails] = useState(false)
  const [companyInfo, setCompanyInfo] = useState('')
  const [processing, setProcessing] = useState(false)
  const [processingStatus, setProcessingStatus] = useState('')
  const [loadingCampaigns, setLoadingCampaigns] = useState(true)
  const [processResult, setProcessResult] = useState<ProcessResult | null>(null)
  const [currentStep, setCurrentStep] = useState<'upload' | 'configure' | 'results'>('upload')
  const [processingProgress, setProcessingProgress] = useState(0)
  const [estimatedTime, setEstimatedTime] = useState<string>('')

  // Fetch campaigns on mount
  useEffect(() => {
    fetchCampaigns()
  }, [])

  const fetchCampaigns = async () => {
    setLoadingCampaigns(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/login')
        return
      }

      const response = await fetch(`${API_URL}/api/v1/campaigns`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (!response.ok) {
        if (response.status === 401) {
          router.push('/login')
          return
        }
        throw new Error('Failed to fetch campaigns')
      }

      const data = await response.json()
      setCampaigns(data)
    } catch (error) {
      console.error('Error fetching campaigns:', error)
      toast.error('Failed to load campaigns')
    } finally {
      setLoadingCampaigns(false)
    }
  }

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

    if (!selectedCampaignId) {
      toast.error('Please select a campaign')
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

    // Calculate estimated time based on rows and options
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

      const url = new URL(`${API_URL}/api/v1/campaigns/${selectedCampaignId}/upload-leads`)
      url.searchParams.append('generate_descriptions', generateDescriptions.toString())
      url.searchParams.append('generate_emails', generateEmails.toString())
      if (generateEmails && companyInfo.trim()) {
        url.searchParams.append('company_info', companyInfo.trim())
      }

      setProcessingStatus('Parsing CSV and validating data...')
      setProcessingProgress(20)

      // Update status based on what's enabled
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

      // Show success message
      if (data.stats.leads_created > 0) {
        toast.success(`Successfully imported ${data.stats.leads_created} leads!`)
      }

      // Show warnings for failed rows
      if (data.stats.leads_failed > 0) {
        toast.error(`${data.stats.leads_failed} rows failed to import`)
      }

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
    setSelectedCampaignId('')
    setGenerateDescriptions(false)
    setGenerateEmails(false)
    setCompanyInfo('')
    setProcessResult(null)
    setCurrentStep('upload')
    setProcessingProgress(0)
    setEstimatedTime('')
  }

  const handleViewLeads = () => {
    if (processResult?.campaign_id) {
      router.push(`/leads?campaign=${processResult.campaign_id}`)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <Sparkles className="w-10 h-10 text-primary-600" />
            Import & Enrich Leads
          </h1>
          <p className="text-gray-600 text-lg">
            Upload your lead data and automatically enrich it with AI-generated content
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8 flex items-center justify-center gap-4">
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
                {/* Campaign Selection */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Target Campaign *
                  </label>
                  {loadingCampaigns ? (
                    <div className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                      <span className="text-gray-500">Loading campaigns...</span>
                    </div>
                  ) : (
                    <select
                      value={selectedCampaignId}
                      onChange={(e) => setSelectedCampaignId(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      disabled={processing}
                    >
                      <option value="">Select a campaign...</option>
                      {campaigns.map(campaign => (
                        <option key={campaign.id} value={campaign.id}>
                          {campaign.name} ({campaign.leads_count} leads)
                        </option>
                      ))}
                    </select>
                  )}
                </div>

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
                    <div className="ml-7 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Your Company Information *
                      </label>
                      <textarea
                        value={companyInfo}
                        onChange={(e) => setCompanyInfo(e.target.value)}
                        placeholder="Example: We are a digital marketing agency specializing in SEO and social media management for small businesses..."
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                        rows={4}
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        This information will be used to personalize the outreach emails
                      </p>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  <Button
                    onClick={handleReset}
                    variant="outline"
                    className="flex-1"
                    disabled={processing}
                  >
                    Start Over
                  </Button>
                  <Button
                    onClick={handleProcess}
                    disabled={processing || !selectedCampaignId}
                    className="flex-1"
                  >
                    {processing ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Process & Import
                      </>
                    )}
                  </Button>
                </div>

              </CardContent>
            </Card>
          </div>
        )}

        {/* Step 3: Results */}
        {currentStep === 'results' && processResult && (
          <div className="space-y-6">
            {/* Success Summary */}
            <Card className="border-success-200 bg-success-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-success-900">
                  <CheckCircle2 className="w-6 h-6" />
                  Import Complete!
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-white rounded-lg">
                    <div className="text-3xl font-bold text-gray-900">{processResult.stats.total_rows}</div>
                    <div className="text-sm text-gray-600">Total Rows</div>
                  </div>
                  <div className="text-center p-4 bg-white rounded-lg">
                    <div className="text-3xl font-bold text-success-600">{processResult.stats.leads_created}</div>
                    <div className="text-sm text-gray-600">Leads Imported</div>
                  </div>
                  <div className="text-center p-4 bg-white rounded-lg">
                    <div className="text-3xl font-bold text-primary-600">{processResult.stats.descriptions_generated}</div>
                    <div className="text-sm text-gray-600">Descriptions Generated</div>
                  </div>
                  <div className="text-center p-4 bg-white rounded-lg">
                    <div className="text-3xl font-bold text-primary-600">{processResult.stats.emails_generated}</div>
                    <div className="text-sm text-gray-600">Emails Generated</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Failed Rows (if any) */}
            {processResult.stats.leads_failed > 0 && processResult.failed_rows && (
              <Card className="border-error-200 bg-error-50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-error-900">
                    <AlertCircle className="w-5 h-5" />
                    {processResult.stats.leads_failed} Rows Failed
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {processResult.failed_rows.slice(0, 10).map((fail, idx) => (
                      <div key={idx} className="p-3 bg-white border border-error-200 rounded text-sm">
                        <span className="font-semibold text-error-900">Row {fail.row}:</span>{' '}
                        <span className="text-gray-700">{fail.reason}</span>
                      </div>
                    ))}
                    {processResult.failed_rows.length > 10 && (
                      <p className="text-sm text-gray-600 text-center">
                        ... and {processResult.failed_rows.length - 10} more
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={handleReset}
                variant="outline"
                className="flex-1"
              >
                Import More Leads
              </Button>
              <Button
                onClick={handleViewLeads}
                className="flex-1"
              >
                View Leads in Campaign
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Full-Screen Processing Overlay */}
        {processing && (
          <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-8 animate-fadeIn">
              <div className="flex flex-col items-center space-y-6">
                {/* Animated Spinner */}
                <div className="relative">
                  <div className="w-20 h-20 border-8 border-primary-200 rounded-full"></div>
                  <div className="w-20 h-20 border-8 border-primary-600 rounded-full absolute top-0 left-0 animate-spin border-t-transparent"></div>
                  <Sparkles className="w-8 h-8 text-primary-600 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 animate-pulse" />
                </div>

                {/* Status Text */}
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-bold text-gray-900">Processing Your Leads</h3>
                  <p className="text-lg font-medium text-primary-600">{processingStatus}</p>
                  <p className="text-sm text-gray-500">{estimatedTime}</p>
                </div>

                {/* Progress Bar */}
                <div className="w-full space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Progress</span>
                    <span>{Math.round(processingProgress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-primary-500 to-primary-600 h-3 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${processingProgress}%` }}
                    ></div>
                  </div>
                </div>

                {/* Information Cards */}
                <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  {generateDescriptions && (
                    <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 text-center">
                      <Sparkles className="w-6 h-6 text-primary-600 mx-auto mb-2" />
                      <p className="text-xs font-semibold text-primary-900">AI Descriptions</p>
                      <p className="text-xs text-primary-700 mt-1">Researching companies</p>
                    </div>
                  )}
                  {generateEmails && (
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                      <Sparkles className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                      <p className="text-xs font-semibold text-purple-900">Email Generation</p>
                      <p className="text-xs text-purple-700 mt-1">Personalizing outreach</p>
                    </div>
                  )}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                    <FileText className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                    <p className="text-xs font-semibold text-blue-900">Data Import</p>
                    <p className="text-xs text-blue-700 mt-1">Validating & storing</p>
                  </div>
                </div>

                {/* Helpful Tips */}
                <div className="w-full bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <p className="text-xs text-gray-600 text-center">
                    <strong>Did you know?</strong>{' '}
                    {generateDescriptions
                      ? 'Our AI searches Google in real-time to gather the latest company information before generating descriptions.'
                      : 'You can enable AI descriptions to automatically research each company using real-time Google data.'}
                  </p>
                </div>

                {/* Warning Message */}
                <div className="w-full bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-xs text-yellow-800 text-center flex items-center justify-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Please don't close this window. The process may take several minutes depending on the number of leads.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
