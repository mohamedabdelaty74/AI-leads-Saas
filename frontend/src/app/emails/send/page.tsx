'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import { toast } from '@/components/ui/Toast'
import {
  Send,
  Mail,
  Users,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Eye,
  Lock
} from 'lucide-react'

interface Campaign {
  id: string
  name: string
  status: string
}

interface SendResult {
  message: string
  sent: number
  failed: number
  total: number
}

export default function EmailSendPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState('')
  const [senderEmail, setSenderEmail] = useState('')
  const [senderPassword, setSenderPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [minDelay, setMinDelay] = useState(5)
  const [maxDelay, setMaxDelay] = useState(15)
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [testingConnection, setTestingConnection] = useState(false)
  const [result, setResult] = useState<SendResult | null>(null)
  const [connectionTested, setConnectionTested] = useState(false)

  // Fetch campaigns
  const fetchCampaigns = async () => {
    try {
      setLoading(true)
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
    } finally {
      setLoading(false)
    }
  }

  // Test Gmail connection
  const handleTestConnection = async () => {
    if (!senderEmail || !senderPassword) {
      toast.error('Please enter both email and password')
      return
    }

    try {
      setTestingConnection(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/test-email-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          sender_email: senderEmail,
          sender_password: senderPassword
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Connection test failed')
      }

      setConnectionTested(true)
      toast.success('Gmail connection successful!')
    } catch (error: any) {
      console.error('Connection test failed:', error)
      toast.error(error.message || 'Failed to connect to Gmail')
      setConnectionTested(false)
    } finally {
      setTestingConnection(false)
    }
  }

  // Send emails
  const handleSendEmails = async () => {
    if (!selectedCampaignId) {
      toast.error('Please select a campaign')
      return
    }

    if (!senderEmail || !senderPassword) {
      toast.error('Please enter Gmail credentials')
      return
    }

    if (!connectionTested) {
      toast.error('Please test your Gmail connection first')
      return
    }

    if (!confirm('Are you sure you want to send emails to all leads in this campaign? This action cannot be undone.')) {
      return
    }

    try {
      setSending(true)
      setResult(null)

      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${selectedCampaignId}/send-emails`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            sender_email: senderEmail,
            sender_password: senderPassword,
            min_delay: minDelay,
            max_delay: maxDelay
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to send emails')
      }

      const data = await response.json()
      setResult(data)
      toast.success(`Successfully sent ${data.sent} emails!`)
    } catch (error: any) {
      console.error('Error sending emails:', error)
      toast.error(error.message || 'Failed to send emails')
    } finally {
      setSending(false)
    }
  }

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const campaignOptions = campaigns.map(c => ({
    value: c.id,
    label: `${c.name} (${c.status})`
  }))

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Send className="w-8 h-8 text-blue-600" />
            Email Campaign Manager
          </h1>
          <p className="text-gray-600 mt-1">
            Send AI-generated emails to your campaign leads via Gmail
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <>
            {/* Warning Card */}
            <Card className="bg-amber-50 border-amber-200">
              <CardContent className="py-4">
                <div className="flex gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-amber-900">
                    <p className="font-semibold mb-1">Important: Gmail App Password Required</p>
                    <p className="text-amber-800">
                      Do NOT use your regular Gmail password. You must create a Gmail App Password:
                    </p>
                    <ol className="list-decimal list-inside mt-2 space-y-1 text-amber-800">
                      <li>Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline font-semibold">myaccount.google.com/apppasswords</a></li>
                      <li>Sign in and create a new app password</li>
                      <li>Copy the 16-character password and paste it below</li>
                    </ol>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Campaign Selection */}
            <Card>
              <CardHeader>
                <CardTitle>Select Campaign</CardTitle>
                <CardDescription>
                  Choose which campaign to send emails for
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Select
                  options={campaignOptions}
                  value={selectedCampaignId}
                  onChange={(e) => setSelectedCampaignId(e.target.value)}
                  placeholder="Choose a campaign..."
                />
                {campaigns.length === 0 && (
                  <p className="text-sm text-amber-600 mt-2">
                    No campaigns found. Please create a campaign and generate emails first.
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Gmail Configuration */}
            <Card>
              <CardHeader>
                <CardTitle>Gmail SMTP Configuration</CardTitle>
                <CardDescription>
                  Enter your Gmail credentials to send emails
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  type="email"
                  label="Gmail Address"
                  placeholder="your.email@gmail.com"
                  value={senderEmail}
                  onChange={(e) => {
                    setSenderEmail(e.target.value)
                    setConnectionTested(false)
                  }}
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gmail App Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="16-character app password"
                      value={senderPassword}
                      onChange={(e) => {
                        setSenderPassword(e.target.value)
                        setConnectionTested(false)
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword ? <Eye className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Must be a Gmail App Password, not your regular password
                  </p>
                </div>

                <Button
                  onClick={handleTestConnection}
                  disabled={testingConnection || !senderEmail || !senderPassword}
                  variant="outline"
                  className="w-full"
                >
                  {testingConnection ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Testing Connection...
                    </>
                  ) : connectionTested ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 mr-2 text-green-600" />
                      Connection Verified
                    </>
                  ) : (
                    <>
                      <Mail className="w-4 h-4 mr-2" />
                      Test Gmail Connection
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Rate Limiting Settings */}
            <Card>
              <CardHeader>
                <CardTitle>Rate Limiting Settings</CardTitle>
                <CardDescription>
                  Configure delays between emails to avoid spam filters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Delay (seconds)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={maxDelay}
                      onChange={(e) => setMaxDelay(Number(e.target.value))}
                    />
                  </div>
                </div>
                <div className="flex gap-2 text-xs text-gray-600">
                  <Info className="w-4 h-4 flex-shrink-0" />
                  <p>
                    Emails will be sent with random delays between {minDelay}-{maxDelay} seconds
                    to avoid spam detection. Longer delays are safer but slower.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Send Button */}
            <Button
              onClick={handleSendEmails}
              disabled={sending || !connectionTested || !selectedCampaignId}
              className="w-full"
              size="lg"
            >
              {sending ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Sending Emails...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5 mr-2" />
                  Send Emails to Campaign Leads
                </>
              )}
            </Button>

            {/* Results Card */}
            {result && (
              <Card className={result.sent > 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}>
                <CardContent className="py-6">
                  <div className="flex items-start gap-3">
                    {result.sent > 0 ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <h3 className={`font-semibold mb-2 ${result.sent > 0 ? 'text-green-900' : 'text-red-900'}`}>
                        {result.message}
                      </h3>
                      <div className={`grid grid-cols-3 gap-4 text-sm ${result.sent > 0 ? 'text-green-800' : 'text-red-800'}`}>
                        <div>
                          <p className="text-xs opacity-75">Sent</p>
                          <p className="text-2xl font-bold text-green-600">{result.sent}</p>
                        </div>
                        <div>
                          <p className="text-xs opacity-75">Failed</p>
                          <p className="text-2xl font-bold text-red-600">{result.failed}</p>
                        </div>
                        <div>
                          <p className="text-xs opacity-75">Total</p>
                          <p className="text-2xl font-bold">{result.total}</p>
                        </div>
                      </div>
                      {result.sent > 0 && (
                        <p className="text-sm text-green-700 mt-4">
                          Check <strong>Email Analytics</strong> to track opens, clicks, and replies.
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
                <CardTitle className="text-lg">Best Practices</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-gray-700">
                <div>
                  <p className="font-semibold text-gray-900 mb-1">
                    Avoid Spam Filters
                  </p>
                  <p>
                    Use delays of 5-15 seconds between emails. Gmail has sending limits:
                    ~100 emails/day for regular accounts, ~500/day for Google Workspace.
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-gray-900 mb-1">
                    Monitor Sending Progress
                  </p>
                  <p>
                    The system will log each email sent. After every 50 emails, it takes a 5-minute
                    break to avoid rate limits.
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-gray-900 mb-1">
                    What if sending fails?
                  </p>
                  <p>
                    The system automatically retries failed emails 3 times. If an email still fails,
                    it's logged and you can review it in the analytics dashboard.
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
