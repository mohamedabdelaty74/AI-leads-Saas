'use client'

import React, { useState } from 'react'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { toast } from 'react-hot-toast'
import {
  Play,
  Loader2,
  AlertTriangle,
  Eye,
  Lock,
  Sparkles,
  X
} from 'lucide-react'

interface ScrapingFormProps {
  campaignId: string
  onSuccess: () => void
}

export default function ScrapingForm({ campaignId, onSuccess }: ScrapingFormProps) {
  // Form State
  const [query, setQuery] = useState('')
  const [source, setSource] = useState<'google_maps' | 'linkedin' | 'instagram'>('google_maps')
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
  const [running, setRunning] = useState(false)
  const [cancelling, setCancelling] = useState(false)

  const sourceOptions = [
    { value: 'google_maps', label: 'Google Maps' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'instagram', label: 'Instagram' }
  ]

  const handleCancelGeneration = async () => {
    if (!confirm('Are you sure you want to cancel the current generation?')) {
      return
    }

    try {
      setCancelling(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/cancel-generation`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('Failed to cancel generation')
      }

      const data = await response.json()
      toast.success(data.message || 'Generation cancelled')
      setRunning(false)
    } catch (error: any) {
      console.error('Cancel error:', error)
      toast.error(error.message || 'Failed to cancel')
    } finally {
      setCancelling(false)
    }
  }

  const handleRunAutomation = async () => {
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

    if (!confirm(`Run full automation? This will:\n1. Scrape ${maxResults} leads from ${source}\n2. ${generateDescriptions ? 'Generate AI descriptions' : 'Skip descriptions'}\n3. ${generateEmails ? 'Generate fully custom AI emails (NO templates!)' : 'Skip emails'}\n4. ${autoSendEmails ? 'Send emails automatically' : 'Save emails for manual sending'}\n\nProceed?`)) {
      return
    }

    try {
      setRunning(true)

      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/run-automation`,
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

      if (data.success) {
        toast.success(`Automation completed! ${data.stats.leads_collected} leads generated.`)
        onSuccess()
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

  return (
    <div className="space-y-6">
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

      {/* Lead Scraping Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>1. Configure Lead Scraping</CardTitle>
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
                onChange={(e) => setSource(e.target.value as 'google_maps' | 'linkedin' | 'instagram')}
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
          <CardTitle>2. AI Features</CardTitle>
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
                  placeholder="Example: We are Elite Creatif, a digital marketing agency based in Dubai. We specialize in SEO, social media management, and targeted advertising for restaurants and retail businesses."
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
                  placeholder="Example: Focus on how we can help increase online visibility and customer engagement. Keep tone professional but friendly."
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
          <CardTitle>3. Email Sending (Optional)</CardTitle>
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
      <div className="space-y-3">
        <Button
          onClick={handleRunAutomation}
          disabled={running || !query.trim()}
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

        {running && (
          <Button
            onClick={handleCancelGeneration}
            disabled={cancelling}
            variant="outline"
            className="w-full border-red-300 text-red-600 hover:bg-red-50"
            size="lg"
          >
            {cancelling ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Cancelling...
              </>
            ) : (
              <>
                <X className="w-5 h-5 mr-2" />
                Cancel Generation
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  )
}
