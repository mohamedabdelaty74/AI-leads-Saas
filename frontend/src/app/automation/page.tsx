'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import { toast } from '@/components/ui/Toast'
import {
  Zap,
  Sparkles,
  Mail,
  Users,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Info,
  Settings,
  Play,
  FileText,
  Eye,
  Lock,
  TrendingUp,
  ExternalLink,
  Download,
  Edit3,
  Save,
  X
} from 'lucide-react'
import Modal from '@/components/ui/Modal'

interface Campaign {
  id: string
  name: string
  status: string
}

interface Lead {
  id: string
  title: string
  address: string
  phone: string
  website: string
  email: string
  description: string
  generated_email: string
  lead_score: number
  email_sent: boolean
  created_at: string
}

interface AutomationResult {
  success: boolean
  message: string
  stats: {
    leads_collected: number
    descriptions_generated: number
    emails_generated: number
    emails_sent: number
    emails_failed: number
  }
  leads?: Array<{ id: string; name: string; email: string }>
  error?: string
}

export default function AutomationPage() {
  const router = useRouter()

  // Campaign Data
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(false)

  // Form Data
  const [selectedCampaignId, setSelectedCampaignId] = useState('')
  const [query, setQuery] = useState('')
  const [source, setSource] = useState('google_maps')
  const [maxResults, setMaxResults] = useState(50)
  const [generateDescriptions, setGenerateDescriptions] = useState(true)
  const [generateEmails, setGenerateEmails] = useState(true)
  const [companyInfo, setCompanyInfo] = useState('')
  const [customInstruction, setCustomInstruction] = useState('')
  const [autoSendEmails, setAutoSendEmails] = useState(false)
  const [senderEmail, setSenderEmail] = useState('')
  const [senderPassword, setSenderPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [minDelay, setMinDelay] = useState(5)
  const [maxDelay, setMaxDelay] = useState(15)

  // Execution State
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<AutomationResult | null>(null)

  // Modal & Leads State
  const [showLeadsModal, setShowLeadsModal] = useState(false)
  const [generatedLeads, setGeneratedLeads] = useState<Lead[]>([])
  const [loadingLeads, setLoadingLeads] = useState(false)
  const [editingLeadId, setEditingLeadId] = useState<string | null>(null)
  const [editedLead, setEditedLead] = useState<Partial<Lead>>({})

  // Fetch campaigns
  useEffect(() => {
    fetchCampaigns()
  }, [])

  // Auto-fetch leads when campaign changes (for persistence)
  useEffect(() => {
    if (selectedCampaignId) {
      fetchExistingLeads()
    } else {
      setGeneratedLeads([])
    }
  }, [selectedCampaignId])

  const fetchCampaigns = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/campaigns', {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!response.ok) throw new Error('Failed to fetch campaigns')

      const data = await response.json()
      setCampaigns(data)

      if (data.length > 0 && !selectedCampaignId) {
        setSelectedCampaignId(data[0].id)
      }
    } catch (error) {
      console.error('Error fetching campaigns:', error)
      toast.error('Failed to load campaigns')
    }
  }

  const fetchExistingLeads = async () => {
    if (!selectedCampaignId) return

    try {
      setLoadingLeads(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${selectedCampaignId}/leads`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      if (!response.ok) {
        // Silently fail if leads don't exist yet
        setGeneratedLeads([])
        return
      }

      const data = await response.json()
      setGeneratedLeads(data)
    } catch (error: any) {
      // Silently fail - leads might not exist yet
      console.log('No existing leads found for this campaign')
      setGeneratedLeads([])
    } finally {
      setLoadingLeads(false)
    }
  }

  const fetchGeneratedLeads = async () => {
    if (!selectedCampaignId) return

    try {
      setLoadingLeads(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${selectedCampaignId}/leads`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      if (!response.ok) throw new Error('Failed to fetch leads')

      const data = await response.json()
      setGeneratedLeads(data)
      setShowLeadsModal(true)
    } catch (error: any) {
      console.error('Error fetching leads:', error)
      toast.error(error.message || 'Failed to load generated leads')
    } finally {
      setLoadingLeads(false)
    }
  }

  const handleEditLead = (lead: Lead) => {
    setEditingLeadId(lead.id)
    setEditedLead({
      title: lead.title,
      description: lead.description,
      generated_email: lead.generated_email,
      email: lead.email
    })
  }

  const handleSaveLead = async (leadId: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/leads/${leadId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(editedLead)
        }
      )

      if (!response.ok) throw new Error('Failed to save changes')

      // Update local state
      setGeneratedLeads(prev => prev.map(lead =>
        lead.id === leadId ? { ...lead, ...editedLead } : lead
      ))

      setEditingLeadId(null)
      setEditedLead({})
      toast.success('Lead updated successfully!')
    } catch (error: any) {
      console.error('Error saving lead:', error)
      toast.error(error.message || 'Failed to save changes')
    }
  }

  const handleCancelEdit = () => {
    setEditingLeadId(null)
    setEditedLead({})
  }

  const exportToExcel = async () => {
    let leadsToExport = generatedLeads

    // If leads haven't been loaded, fetch them first
    if (leadsToExport.length === 0 && selectedCampaignId) {
      try {
        setLoadingLeads(true)
        const token = localStorage.getItem('access_token')
        const response = await fetch(
          `http://localhost:8000/api/v1/campaigns/${selectedCampaignId}/leads`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        )

        if (!response.ok) throw new Error('Failed to fetch leads')

        const data = await response.json()
        leadsToExport = data
        setGeneratedLeads(data)
      } catch (error: any) {
        console.error('Error fetching leads:', error)
        toast.error(error.message || 'Failed to load leads for export')
        return
      } finally {
        setLoadingLeads(false)
      }
    }

    if (leadsToExport.length === 0) {
      toast.error('No leads to export')
      return
    }

    // Create CSV content
    const headers = ['Name', 'Email', 'Phone', 'Website', 'Address', 'Description', 'Generated Email', 'Lead Score', 'Email Sent']
    const rows = leadsToExport.map(lead => [
      lead.title,
      lead.email || '',
      lead.phone || '',
      lead.website || '',
      lead.address || '',
      (lead.description || '').replace(/"/g, '""'),
      (lead.generated_email || '').replace(/"/g, '""'),
      lead.lead_score || 0,
      lead.email_sent ? 'Yes' : 'No'
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `leads_${selectedCampaignId}_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    toast.success('Leads exported successfully!')
  }

  const handleRunAutomation = async () => {
    if (!selectedCampaignId) {
      toast.error('Please select a campaign')
      return
    }

    if (!query.trim()) {
      toast.error('Please enter a search query')
      return
    }

    if (generateEmails && !companyInfo.trim()) {
      toast.error('Please enter your company information for AI email generation')
      return
    }

    if (autoSendEmails && (!senderEmail || !senderPassword)) {
      toast.error('Please enter Gmail credentials for automatic sending')
      return
    }

    if (!confirm(`Run full automation for campaign? This will:\n1. Scrape ${maxResults} leads from ${source}\n2. ${generateDescriptions ? 'Generate AI descriptions' : 'Skip descriptions'}\n3. ${generateEmails ? 'Generate fully custom AI emails (NO templates!)' : 'Skip emails'}\n4. ${autoSendEmails ? 'Send emails automatically' : 'Save emails for manual sending'}\n\nProceed?`)) {
      return
    }

    try {
      setRunning(true)
      setResult(null)

      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${selectedCampaignId}/run-automation`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            query: query.trim(),
            source,
            max_results: maxResults,
            generate_descriptions: generateDescriptions,
            generate_emails: generateEmails,
            company_info: generateEmails ? companyInfo.trim() : null,
            custom_instruction: customInstruction.trim() || null,
            auto_send_emails: autoSendEmails,
            sender_email: autoSendEmails ? senderEmail : null,
            sender_password: autoSendEmails ? senderPassword : null,
            min_delay: minDelay,
            max_delay: maxDelay
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Automation failed')
      }

      const data = await response.json()
      setResult(data)

      if (data.success) {
        toast.success('Automation completed successfully!')
        // Refresh leads to show newly generated content
        await fetchExistingLeads()
      } else {
        toast.error(data.error || 'Automation failed')
      }
    } catch (error: any) {
      console.error('Automation error:', error)
      toast.error(error.message || 'Failed to run automation')
    } finally {
      setRunning(false)
    }
  }

  const campaignOptions = campaigns.map(c => ({
    value: c.id,
    label: `${c.name} (${c.status})`
  }))

  const sourceOptions = [
    { value: 'google_maps', label: 'Google Maps' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'instagram', label: 'Instagram' }
  ]

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Zap className="w-8 h-8 text-purple-600" />
              AI Automation Pipeline
            </h1>
            <p className="text-gray-600 mt-1">
              Complete end-to-end lead generation with fully custom AI emails
            </p>
          </div>
        </div>

        {/* Info Card */}
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="py-4">
            <div className="flex gap-3">
              <Sparkles className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-purple-900">
                <p className="font-semibold mb-2">Full Automation - NO Templates Needed!</p>
                <p className="text-purple-800">
                  AI generates completely custom emails for each business. Just provide your company info,
                  and AI creates unique subject lines, body content, and calls-to-action tailored to each lead.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Campaign Selection */}
        <Card>
          <CardHeader>
            <CardTitle>1. Select Campaign</CardTitle>
            <CardDescription>Choose which campaign to add leads to</CardDescription>
          </CardHeader>
          <CardContent>
            <Select
              options={campaignOptions}
              value={selectedCampaignId}
              onChange={(e) => setSelectedCampaignId(e.target.value)}
              placeholder="Choose a campaign..."
            />
          </CardContent>
        </Card>

        {/* Lead Scraping Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>2. Configure Lead Scraping</CardTitle>
            <CardDescription>Define your target audience and source</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Search Query"
              placeholder="e.g., restaurants in Dubai Marina"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              required
            />

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lead Source
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                >
                  {sourceOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Results
                </label>
                <input
                  type="number"
                  min="1"
                  max={source === 'google_maps' ? 500 : source === 'linkedin' ? 200 : 300}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  value={maxResults}
                  onChange={(e) => {
                    const value = Number(e.target.value)
                    const max = source === 'google_maps' ? 500 : source === 'linkedin' ? 200 : 300
                    if (value > max) {
                      setMaxResults(max)
                      toast.error(`Maximum ${max} results allowed for ${source === 'google_maps' ? 'Google Maps' : source === 'linkedin' ? 'LinkedIn' : 'Instagram'}`)
                    } else if (value < 1) {
                      setMaxResults(1)
                      toast.error('Minimum 1 result required')
                    } else {
                      setMaxResults(value)
                    }
                  }}
                  onBlur={(e) => {
                    const value = Number(e.target.value)
                    if (!value || value < 1) {
                      setMaxResults(50)
                    }
                  }}
                />
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-500">
                    Maximum: {source === 'google_maps' ? '500' : source === 'linkedin' ? '200' : '300'} results for {source === 'google_maps' ? 'Google Maps' : source === 'linkedin' ? 'LinkedIn' : 'Instagram'}
                  </p>
                  {maxResults >= 100 && (
                    <div className="flex items-start gap-1 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                      <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                      <span>
                        Scraping {maxResults} results may take {Math.ceil(maxResults / 10)}-{Math.ceil(maxResults / 5)} minutes
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Features Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>3. AI Features</CardTitle>
            <CardDescription>Configure AI-powered automation steps</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Generate Descriptions */}
            <div className="flex items-start gap-3 p-4 border rounded-lg">
              <input
                type="checkbox"
                id="generate-descriptions"
                className="mt-1"
                checked={generateDescriptions}
                onChange={(e) => setGenerateDescriptions(e.target.checked)}
              />
              <div className="flex-1">
                <label htmlFor="generate-descriptions" className="font-medium text-gray-900 cursor-pointer">
                  Generate AI Business Descriptions
                </label>
                <p className="text-sm text-gray-600">
                  Create professional descriptions for each business using AI
                </p>
              </div>
            </div>

            {/* Generate Emails */}
            <div className="flex items-start gap-3 p-4 border rounded-lg">
              <input
                type="checkbox"
                id="generate-emails"
                className="mt-1"
                checked={generateEmails}
                onChange={(e) => setGenerateEmails(e.target.checked)}
              />
              <div className="flex-1">
                <label htmlFor="generate-emails" className="font-medium text-gray-900 cursor-pointer">
                  Generate Fully Custom AI Emails (NO Templates!)
                </label>
                <p className="text-sm text-gray-600">
                  AI creates completely unique emails for each lead with custom subject lines and body content
                </p>
              </div>
            </div>

            {/* Company Info & Custom Instructions */}
            {generateEmails && (
              <div className="ml-8 space-y-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Your Company Information * (Required for AI)
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={5}
                    placeholder="Example: We are Elite Creatif, a digital marketing agency based in Dubai. We specialize in SEO, social media management, and targeted advertising for restaurants and retail businesses. Our services help businesses increase online visibility, attract more customers, and boost revenue through strategic digital campaigns."
                    value={companyInfo}
                    onChange={(e) => setCompanyInfo(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    AI uses this to introduce your company and explain your services to each lead
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Custom Instructions (Optional)
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={3}
                    placeholder="Example: Focus on how we can help increase online visibility and customer engagement. Keep tone professional but friendly. Emphasize our track record with similar businesses."
                    value={customInstruction}
                    onChange={(e) => setCustomInstruction(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Optional: Add specific instructions for tone, style, or key points to emphasize
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Email Sending Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>4. Email Sending (Optional)</CardTitle>
            <CardDescription>Automatically send generated emails</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3 p-4 border rounded-lg">
              <input
                type="checkbox"
                id="auto-send-emails"
                className="mt-1"
                checked={autoSendEmails}
                onChange={(e) => setAutoSendEmails(e.target.checked)}
              />
              <div className="flex-1">
                <label htmlFor="auto-send-emails" className="font-medium text-gray-900 cursor-pointer">
                  Automatically Send Emails
                </label>
                <p className="text-sm text-gray-600">
                  Send emails immediately after generation via Gmail SMTP
                </p>
              </div>
            </div>

            {autoSendEmails && (
              <div className="ml-8 space-y-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex gap-2 text-sm text-amber-800">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <p>
                    Requires Gmail App Password (not regular password).
                    Create one at <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline font-semibold">myaccount.google.com/apppasswords</a>
                  </p>
                </div>

                <Input
                  type="email"
                  label="Gmail Address"
                  placeholder="your.email@gmail.com"
                  value={senderEmail}
                  onChange={(e) => setSenderEmail(e.target.value)}
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gmail App Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="16-character app password"
                      value={senderPassword}
                      onChange={(e) => setSenderPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword ? <Eye className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Delay (seconds)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      value={minDelay}
                      onChange={(e) => setMinDelay(Number(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Delay (seconds)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="120"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      value={maxDelay}
                      onChange={(e) => setMaxDelay(Number(e.target.value))}
                    />
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Run Automation Button */}
        <Button
          onClick={handleRunAutomation}
          disabled={running || !selectedCampaignId || !query.trim()}
          className="w-full"
          size="lg"
        >
          {running ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Running Automation Pipeline...
            </>
          ) : (
            <>
              <Play className="w-5 h-5 mr-2" />
              Run Full Automation
            </>
          )}
        </Button>

        {/* Existing Leads - Persistent Section */}
        {selectedCampaignId && generatedLeads.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-600" />
                    Generated Leads ({generatedLeads.length})
                  </CardTitle>
                  <CardDescription>
                    View and manage your generated leads from this campaign
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() => setShowLeadsModal(true)}
                    variant="primary"
                    size="sm"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View & Edit All
                  </Button>
                  <Button
                    onClick={exportToExcel}
                    variant="outline"
                    size="sm"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-600 font-medium">Total Leads</p>
                    <p className="text-2xl font-bold text-blue-700">{generatedLeads.length}</p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-600 font-medium">With Emails</p>
                    <p className="text-2xl font-bold text-green-700">
                      {generatedLeads.filter(l => l.email).length}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm text-purple-600 font-medium">AI Content</p>
                    <p className="text-2xl font-bold text-purple-700">
                      {generatedLeads.filter(l => l.generated_email).length}
                    </p>
                  </div>
                  <div className="p-3 bg-amber-50 rounded-lg">
                    <p className="text-sm text-amber-600 font-medium">Emails Sent</p>
                    <p className="text-2xl font-bold text-amber-700">
                      {generatedLeads.filter(l => l.email_sent).length}
                    </p>
                  </div>
                </div>

                {/* Preview of first 3 leads */}
                <div className="border rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b">
                    <p className="text-sm font-medium text-gray-700">Recent Leads Preview</p>
                  </div>
                  <div className="divide-y">
                    {generatedLeads.slice(0, 3).map((lead, idx) => (
                      <div key={lead.id} className="p-4 hover:bg-gray-50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold text-gray-900">{lead.title}</h4>
                              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                                lead.lead_score >= 80 ? 'bg-green-100 text-green-700' :
                                lead.lead_score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                                'bg-gray-100 text-gray-600'
                              }`}>
                                Score: {lead.lead_score || 0}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{lead.address}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                              {lead.email && (
                                <span className="flex items-center gap-1">
                                  <Mail className="w-3 h-3" />
                                  {lead.email}
                                </span>
                              )}
                              {lead.phone && (
                                <span>{lead.phone}</span>
                              )}
                            </div>
                          </div>
                          <div className="flex flex-col gap-1 text-right">
                            {lead.generated_email && (
                              <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                                AI Email ✓
                              </span>
                            )}
                            {lead.email_sent && (
                              <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                                Sent ✓
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  {generatedLeads.length > 3 && (
                    <div className="bg-gray-50 px-4 py-2 text-center border-t">
                      <button
                        onClick={() => setShowLeadsModal(true)}
                        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                      >
                        View all {generatedLeads.length} leads →
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {result && (
          <Card className={result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}>
            <CardContent className="py-6">
              <div className="flex items-start gap-3">
                {result.success ? (
                  <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
                )}
                <div className="flex-1">
                  <h3 className={`font-semibold mb-3 ${result.success ? 'text-green-900' : 'text-red-900'}`}>
                    {result.message}
                  </h3>

                  {result.success && result.stats && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="text-center p-3 bg-white rounded-lg">
                        <p className="text-2xl font-bold text-blue-600">{result.stats.leads_collected}</p>
                        <p className="text-xs text-gray-600">Leads Collected</p>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg">
                        <p className="text-2xl font-bold text-purple-600">{result.stats.descriptions_generated}</p>
                        <p className="text-xs text-gray-600">Descriptions</p>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg">
                        <p className="text-2xl font-bold text-indigo-600">{result.stats.emails_generated}</p>
                        <p className="text-xs text-gray-600">Custom Emails</p>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg">
                        <p className="text-2xl font-bold text-green-600">{result.stats.emails_sent}</p>
                        <p className="text-xs text-gray-600">Emails Sent</p>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg">
                        <p className="text-2xl font-bold text-red-600">{result.stats.emails_failed}</p>
                        <p className="text-xs text-gray-600">Failed</p>
                      </div>
                    </div>
                  )}

                  {result.error && (
                    <p className="text-sm text-red-800 mt-2">{result.error}</p>
                  )}

                  {result.success && (
                    <>
                      <div className="mt-4 flex gap-2 text-sm text-green-700">
                        <Info className="w-4 h-4" />
                        <p>
                          View and edit your generated content below, or export to Excel for offline use.
                        </p>
                      </div>

                      <div className="mt-4 flex gap-3">
                        <Button
                          onClick={fetchGeneratedLeads}
                          disabled={loadingLeads}
                          variant="primary"
                          size="md"
                        >
                          {loadingLeads ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Loading...
                            </>
                          ) : (
                            <>
                              <Eye className="w-4 h-4 mr-2" />
                              View & Edit Generated Content
                            </>
                          )}
                        </Button>

                        <Button
                          onClick={exportToExcel}
                          variant="outline"
                          size="md"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Export to Excel
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* How It Works */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">How AI Email Generation Works (No Templates!)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-gray-700">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">
                1
              </div>
              <div>
                <p className="font-semibold text-gray-900">Lead Scraping</p>
                <p>Searches Google Maps/LinkedIn/Instagram for businesses matching your query and extracts contact information</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center font-bold text-xs">
                2
              </div>
              <div>
                <p className="font-semibold text-gray-900">AI Business Descriptions</p>
                <p>AI analyzes each business and generates professional descriptions based on their category and location</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs">
                3
              </div>
              <div>
                <p className="font-semibold text-gray-900">Fully Custom AI Email Generation</p>
                <p className="font-semibold text-indigo-600">NO TEMPLATES NEEDED!</p>
                <p className="mt-1">AI creates completely unique emails for each business including:</p>
                <ul className="list-disc list-inside ml-2 mt-1 text-gray-600">
                  <li>Custom subject line tailored to their business</li>
                  <li>Personalized greeting (uses first name if available)</li>
                  <li>Custom body content addressing their specific needs</li>
                  <li>Clear call-to-action</li>
                  <li>Professional signature with your contact details</li>
                </ul>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center font-bold text-xs">
                4
              </div>
              <div>
                <p className="font-semibold text-gray-900">Automatic Email Sending</p>
                <p>Sends emails via Gmail with smart rate limiting (5-15 second delays) to avoid spam filters</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Generated Content Modal */}
        <Modal
          isOpen={showLeadsModal}
          onClose={() => setShowLeadsModal(false)}
          title="Generated Leads & Content"
          size="full"
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                {generatedLeads.length} leads generated • Click on any field to edit
              </p>
              <Button
                onClick={exportToExcel}
                variant="outline"
                size="sm"
              >
                <Download className="w-4 h-4 mr-2" />
                Export to Excel
              </Button>
            </div>

            <div className="overflow-x-auto max-h-[70vh] border rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Name</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Email</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Phone</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">AI Description</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Generated Email</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Score</th>
                    <th className="px-4 py-3 text-center font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {generatedLeads.map((lead) => (
                    <tr key={lead.id} className="border-t hover:bg-gray-50">
                      <td className="px-4 py-3">
                        {editingLeadId === lead.id ? (
                          <input
                            type="text"
                            className="w-full px-2 py-1 border rounded text-sm"
                            value={editedLead.title || ''}
                            onChange={(e) => setEditedLead({ ...editedLead, title: e.target.value })}
                          />
                        ) : (
                          <div className="font-medium text-gray-900">{lead.title}</div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">{lead.address}</div>
                      </td>
                      <td className="px-4 py-3">
                        {editingLeadId === lead.id ? (
                          <input
                            type="email"
                            className="w-full px-2 py-1 border rounded text-sm"
                            value={editedLead.email || ''}
                            onChange={(e) => setEditedLead({ ...editedLead, email: e.target.value })}
                          />
                        ) : (
                          <div className="text-gray-700">{lead.email || 'N/A'}</div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">{lead.website}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {lead.phone || 'N/A'}
                      </td>
                      <td className="px-4 py-3">
                        {editingLeadId === lead.id ? (
                          <textarea
                            className="w-full px-2 py-1 border rounded text-sm"
                            rows={3}
                            value={editedLead.description || ''}
                            onChange={(e) => setEditedLead({ ...editedLead, description: e.target.value })}
                          />
                        ) : (
                          <div className="text-gray-700 max-w-xs line-clamp-3">
                            {lead.description || 'Not generated'}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editingLeadId === lead.id ? (
                          <textarea
                            className="w-full px-2 py-1 border rounded text-sm"
                            rows={5}
                            value={editedLead.generated_email || ''}
                            onChange={(e) => setEditedLead({ ...editedLead, generated_email: e.target.value })}
                          />
                        ) : (
                          <div className="text-gray-700 max-w-md line-clamp-5">
                            {lead.generated_email || 'Not generated'}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full font-bold ${
                          lead.lead_score >= 80 ? 'bg-green-100 text-green-700' :
                          lead.lead_score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {lead.lead_score || 0}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-2">
                          {editingLeadId === lead.id ? (
                            <>
                              <button
                                onClick={() => handleSaveLead(lead.id)}
                                className="p-2 text-green-600 hover:bg-green-50 rounded"
                                title="Save changes"
                              >
                                <Save className="w-4 h-4" />
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="p-2 text-red-600 hover:bg-red-50 rounded"
                                title="Cancel"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => handleEditLead(lead)}
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                              title="Edit lead"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {generatedLeads.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No leads generated yet</p>
              </div>
            )}
          </div>
        </Modal>
      </div>
    </DashboardLayout>
  )
}
