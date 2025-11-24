'use client'

import React, { useState, useEffect, useRef } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Select from '@/components/ui/Select'
import { toast } from '@/components/ui/Toast'
import {
  Sparkles,
  Mail,
  Users,
  FileText,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Info,
  X
} from 'lucide-react'

interface Campaign {
  id: string
  name: string
  status: string
}

interface EmailTemplate {
  id: string
  name: string
  subject: string
  body: string
  use_ai_personalization: boolean
}

interface GenerateResult {
  message: string
  generated_count: number
  failed_count: number
  total: number
}

export default function EmailComposePage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState('')
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [companyInfo, setCompanyInfo] = useState('')
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<GenerateResult | null>(null)

  // AbortController for cancellation
  const abortControllerRef = useRef<AbortController | null>(null)

  // Cancel generation handler
  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setGenerating(false)
      toast.info('Email generation cancelled')
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // Fetch campaigns
  const fetchCampaigns = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/campaigns', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) throw new Error('Failed to fetch campaigns')

      const data = await response.json()
      setCampaigns(data)
    } catch (error) {
      console.error('Error fetching campaigns:', error)
      toast.error('Failed to load campaigns')
    }
  }

  // Fetch templates
  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/email-templates', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) throw new Error('Failed to fetch templates')

      const data = await response.json()
      setTemplates(data.filter((t: EmailTemplate) => t.use_ai_personalization))
    } catch (error) {
      console.error('Error fetching templates:', error)
      toast.error('Failed to load email templates')
    }
  }

  // Generate AI emails
  const handleGenerateEmails = async () => {
    if (!selectedCampaignId) {
      toast.error('Please select a campaign')
      return
    }

    if (!selectedTemplateId) {
      toast.error('Please select an email template')
      return
    }

    if (!companyInfo.trim()) {
      toast.error('Please enter your company information')
      return
    }

    if (companyInfo.trim().length < 10) {
      toast.error('Company information should be at least 10 characters')
      return
    }

    try {
      setGenerating(true)
      setResult(null)

      // Create AbortController for cancellation
      abortControllerRef.current = new AbortController()

      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${selectedCampaignId}/generate-emails`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            template_id: selectedTemplateId,
            company_info: companyInfo
          }),
          signal: abortControllerRef.current.signal
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate emails')
      }

      const data = await response.json()
      setResult(data)
      toast.success(`Successfully generated ${data.generated_count} AI-personalized emails!`)
    } catch (error: any) {
      if (error.name === 'AbortError') {
        // Request was cancelled - don't show error
        return
      }
      console.error('Error generating emails:', error)
      toast.error(error.message || 'Failed to generate emails')
    } finally {
      setGenerating(false)
      abortControllerRef.current = null
    }
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchCampaigns(), fetchTemplates()]).finally(() => setLoading(false))
  }, [])

  const selectedCampaign = campaigns.find(c => c.id === selectedCampaignId)
  const selectedTemplate = templates.find(t => t.id === selectedTemplateId)

  const campaignOptions = campaigns.map(c => ({
    value: c.id,
    label: `${c.name} (${c.status})`
  }))

  const templateOptions = templates.map(t => ({
    value: t.id,
    label: t.name
  }))

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-purple-600" />
            AI Email Composer
          </h1>
          <p className="text-gray-600 mt-1">
            Generate personalized emails for your campaign leads using AI
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <>
            {/* Info Card */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="py-4">
                <div className="flex gap-3">
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-900">
                    <p className="font-semibold mb-1">How AI Email Generation Works:</p>
                    <ol className="list-decimal list-inside space-y-1 text-blue-800">
                      <li>Select a campaign with leads</li>
                      <li>Choose an email template with AI personalization enabled</li>
                      <li>Provide your company information for context</li>
                      <li>AI will generate unique, personalized emails for each lead</li>
                    </ol>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Configuration Form */}
            <Card>
              <CardHeader>
                <CardTitle>Email Generation Settings</CardTitle>
                <CardDescription>
                  Configure your AI email generation parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Campaign Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Users className="w-4 h-4 inline mr-2" />
                    Select Campaign
                  </label>
                  <Select
                    options={campaignOptions}
                    value={selectedCampaignId}
                    onChange={(e) => setSelectedCampaignId(e.target.value)}
                    placeholder="Choose a campaign..."
                  />
                  {campaigns.length === 0 && (
                    <p className="text-sm text-amber-600 mt-2">
                      No campaigns found. Please create a campaign first.
                    </p>
                  )}
                </div>

                {/* Template Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FileText className="w-4 h-4 inline mr-2" />
                    Select Email Template
                  </label>
                  <Select
                    options={templateOptions}
                    value={selectedTemplateId}
                    onChange={(e) => setSelectedTemplateId(e.target.value)}
                    placeholder="Choose an email template..."
                  />
                  {templates.length === 0 && (
                    <p className="text-sm text-amber-600 mt-2">
                      No AI templates found. Create a template with AI personalization enabled.
                    </p>
                  )}
                </div>

                {/* Template Preview */}
                {selectedTemplate && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-xs font-semibold text-gray-500 mb-2">TEMPLATE PREVIEW</p>
                    <div className="space-y-2">
                      <div>
                        <p className="text-xs text-gray-600">Subject:</p>
                        <p className="text-sm font-medium text-gray-900">{selectedTemplate.subject}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Body:</p>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {selectedTemplate.body.substring(0, 200)}
                          {selectedTemplate.body.length > 200 && '...'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Company Info */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company Information
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    rows={6}
                    placeholder="Example:&#10;&#10;Company: Elite Creatif Digital Marketing&#10;Services: Social media marketing, content creation, SEO&#10;Target: Restaurants and cafes in Dubai&#10;Contact: John Smith, john@elitecreatif.com&#10;&#10;Provide details about your company, services, and target audience..."
                    value={companyInfo}
                    onChange={(e) => setCompanyInfo(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    AI will use this information to personalize emails for each lead
                  </p>
                </div>

                {/* Generate Button */}
                <div className="space-y-3">
                  {generating ? (
                    <div className="space-y-3">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                            <div>
                              <p className="font-medium text-blue-900">Generating AI Emails...</p>
                              <p className="text-sm text-blue-700">This may take several minutes depending on the number of leads</p>
                            </div>
                          </div>
                          <button
                            onClick={handleCancel}
                            className="px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors flex items-center gap-1"
                          >
                            <X className="w-4 h-4" />
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <Button
                      onClick={handleGenerateEmails}
                      disabled={!selectedCampaignId || !selectedTemplateId || !companyInfo.trim()}
                      className="w-full"
                      size="lg"
                    >
                      <Sparkles className="w-5 h-5 mr-2" />
                      Generate AI-Personalized Emails
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Results Card */}
            {result && (
              <Card className={result.generated_count > 0 ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}>
                <CardContent className="py-6">
                  <div className="flex items-start gap-3">
                    {result.generated_count > 0 ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
                    ) : (
                      <AlertCircle className="w-6 h-6 text-amber-600 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <h3 className={`font-semibold mb-2 ${result.generated_count > 0 ? 'text-green-900' : 'text-amber-900'}`}>
                        {result.message}
                      </h3>
                      <div className={`grid grid-cols-3 gap-4 text-sm ${result.generated_count > 0 ? 'text-green-800' : 'text-amber-800'}`}>
                        <div>
                          <p className="text-xs opacity-75">Generated</p>
                          <p className="text-2xl font-bold">{result.generated_count}</p>
                        </div>
                        <div>
                          <p className="text-xs opacity-75">Failed</p>
                          <p className="text-2xl font-bold">{result.failed_count}</p>
                        </div>
                        <div>
                          <p className="text-xs opacity-75">Total Leads</p>
                          <p className="text-2xl font-bold">{result.total}</p>
                        </div>
                      </div>
                      {result.generated_count > 0 && (
                        <p className="text-sm text-green-700 mt-4">
                          You can now send these emails from the <strong>Email Campaign Manager</strong>.
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Help Section */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Need Help?</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-gray-700">
                <div>
                  <p className="font-semibold text-gray-900 mb-1">
                    What information should I provide?
                  </p>
                  <p>
                    Include your company name, services, target audience, unique value proposition,
                    and contact details. The more context you provide, the better the AI can personalize emails.
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-gray-900 mb-1">
                    How long does generation take?
                  </p>
                  <p>
                    AI generation takes approximately 5-10 seconds per email. For a campaign with 50 leads,
                    expect the process to take 5-8 minutes.
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-gray-900 mb-1">
                    Can I regenerate emails?
                  </p>
                  <p>
                    Yes! You can regenerate emails for leads that don't have generated emails yet.
                    The system will only generate for leads without existing emails.
                  </p>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
