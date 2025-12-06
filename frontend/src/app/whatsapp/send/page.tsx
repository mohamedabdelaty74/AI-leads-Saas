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
  MessageCircle,
  Users,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Eye,
  Lock,
  Link as LinkIcon
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

export default function WhatsAppSendPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState('')
  const [phoneNumberId, setPhoneNumberId] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [showToken, setShowToken] = useState(false)
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

  // Test WhatsApp connection
  const handleTestConnection = async () => {
    if (!phoneNumberId || !accessToken) {
      toast.error('Please enter both Phone Number ID and Access Token')
      return
    }

    try {
      setTestingConnection(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/test-whatsapp-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          phone_number_id: phoneNumberId,
          access_token: accessToken
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Connection test failed')
      }

      setConnectionTested(true)
      toast.success('WhatsApp Business API connection successful!')
    } catch (error: any) {
      console.error('Connection test failed:', error)
      toast.error(error.message || 'Failed to connect to WhatsApp Business API')
      setConnectionTested(false)
    } finally {
      setTestingConnection(false)
    }
  }

  // Send WhatsApp messages
  const handleSendWhatsApp = async () => {
    if (!selectedCampaignId) {
      toast.error('Please select a campaign')
      return
    }

    if (!phoneNumberId || !accessToken) {
      toast.error('Please enter WhatsApp Business API credentials')
      return
    }

    if (!connectionTested) {
      toast.error('Please test your WhatsApp connection first')
      return
    }

    if (!confirm('Are you sure you want to send WhatsApp messages to all leads in this campaign? This action cannot be undone.')) {
      return
    }

    try {
      setSending(true)
      setResult(null)

      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${selectedCampaignId}/send-whatsapp-all`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            phone_number_id: phoneNumberId,
            access_token: accessToken,
            min_delay: minDelay,
            max_delay: maxDelay
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to send WhatsApp messages')
      }

      const data = await response.json()
      setResult(data)
      toast.success(`Successfully sent ${data.sent} WhatsApp messages!`)
    } catch (error: any) {
      console.error('Error sending WhatsApp messages:', error)
      toast.error(error.message || 'Failed to send WhatsApp messages')
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
            <MessageCircle className="w-8 h-8 text-emerald-600" />
            WhatsApp Campaign Manager
          </h1>
          <p className="text-gray-600 mt-1">
            Send AI-generated WhatsApp messages to your campaign leads via WhatsApp Business API
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
          </div>
        ) : (
          <>
            {/* Warning Card */}
            <Card className="bg-amber-50 border-amber-200">
              <CardHeader>
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-6 h-6 text-amber-600 mt-1" />
                  <div>
                    <CardTitle className="text-amber-900">Important WhatsApp Setup Requirements</CardTitle>
                    <CardDescription className="text-amber-800 mt-2">
                      <ul className="list-disc list-inside space-y-1 text-sm">
                        <li>You need a verified <strong>WhatsApp Business Account</strong></li>
                        <li>Obtain your <strong>Phone Number ID</strong> and <strong>Access Token</strong> from Meta Business Suite</li>
                        <li>Ensure your WhatsApp Business Profile is complete</li>
                        <li>Test your connection before sending messages</li>
                        <li>Messages will be sent with random delays (5-15 seconds) to avoid rate limits</li>
                      </ul>
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Setup Guide Card */}
            <Card className="bg-blue-50 border-blue-200">
              <CardHeader>
                <div className="flex items-start gap-3">
                  <Info className="w-6 h-6 text-blue-600 mt-1" />
                  <div>
                    <CardTitle className="text-blue-900">How to Get Your WhatsApp Credentials</CardTitle>
                    <CardDescription className="text-blue-800 mt-2">
                      <ol className="list-decimal list-inside space-y-2 text-sm">
                        <li>Go to <a href="https://business.facebook.com" target="_blank" rel="noopener noreferrer" className="underline text-blue-700 hover:text-blue-900">Meta Business Suite</a></li>
                        <li>Navigate to <strong>WhatsApp Business Platform Settings</strong></li>
                        <li>Find your <strong>Phone Number ID</strong> (looks like: 123456789012345)</li>
                        <li>Generate a <strong>Temporary or Permanent Access Token</strong></li>
                        <li>Copy both credentials and paste them below</li>
                      </ol>
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Select Campaign */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Select Campaign
                </CardTitle>
                <CardDescription>Choose which campaign to send WhatsApp messages to</CardDescription>
              </CardHeader>
              <CardContent>
                <Select
                  options={campaignOptions}
                  value={selectedCampaignId}
                  onChange={(value) => setSelectedCampaignId(value)}
                  placeholder="Select a campaign..."
                />
              </CardContent>
            </Card>

            {/* WhatsApp Credentials */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lock className="w-5 h-5" />
                  WhatsApp Business API Credentials
                </CardTitle>
                <CardDescription>Enter your WhatsApp Business API credentials to send messages</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Phone Number ID
                  </label>
                  <Input
                    type="text"
                    value={phoneNumberId}
                    onChange={(e) => {
                      setPhoneNumberId(e.target.value)
                      setConnectionTested(false)
                    }}
                    placeholder="123456789012345"
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Your WhatsApp Business Phone Number ID from Meta Business Suite
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Access Token
                  </label>
                  <div className="relative">
                    <Input
                      type={showToken ? 'text' : 'password'}
                      value={accessToken}
                      onChange={(e) => {
                        setAccessToken(e.target.value)
                        setConnectionTested(false)
                      }}
                      placeholder="Your WhatsApp Business API Access Token"
                      className="w-full pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowToken(!showToken)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showToken ? <Eye className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Your WhatsApp Business API Access Token (temporary or permanent)
                  </p>
                </div>

                <div className="pt-2">
                  <Button
                    onClick={handleTestConnection}
                    disabled={testingConnection || !phoneNumberId || !accessToken}
                    leftIcon={testingConnection ? <Loader2 className="w-4 h-4 animate-spin" /> : <LinkIcon className="w-4 h-4" />}
                    variant="outline"
                    className={connectionTested ? 'border-emerald-500 text-emerald-700 bg-emerald-50' : ''}
                  >
                    {testingConnection ? 'Testing Connection...' : connectionTested ? 'Connection Verified ✓' : 'Test Connection'}
                  </Button>
                  {connectionTested && (
                    <p className="text-sm text-emerald-600 mt-2 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" />
                      WhatsApp Business API connection successful!
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Delay Settings */}
            <Card>
              <CardHeader>
                <CardTitle>Sending Delay Settings</CardTitle>
                <CardDescription>Configure random delays between messages to avoid rate limits</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Minimum Delay (seconds)
                    </label>
                    <Input
                      type="number"
                      min="3"
                      max="30"
                      value={minDelay}
                      onChange={(e) => setMinDelay(Math.max(3, parseInt(e.target.value) || 3))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Maximum Delay (seconds)
                    </label>
                    <Input
                      type="number"
                      min="5"
                      max="60"
                      value={maxDelay}
                      onChange={(e) => setMaxDelay(Math.max(5, parseInt(e.target.value) || 15))}
                      className="w-full"
                    />
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  A random delay between <strong>{minDelay}</strong> and <strong>{maxDelay}</strong> seconds will be added between each message to prevent rate limiting.
                </p>
              </CardContent>
            </Card>

            {/* Send Button */}
            <Card>
              <CardContent className="py-6">
                <Button
                  onClick={handleSendWhatsApp}
                  disabled={sending || !selectedCampaignId || !phoneNumberId || !accessToken || !connectionTested}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-6 text-lg"
                  leftIcon={sending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                >
                  {sending ? 'Sending WhatsApp Messages...' : 'Send WhatsApp Messages to Campaign'}
                </Button>
                {!connectionTested && phoneNumberId && accessToken && (
                  <p className="text-sm text-amber-600 mt-3 text-center">
                    Please test your connection before sending messages
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Results */}
            {result && (
              <Card className={result.failed > 0 ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'}>
                <CardHeader>
                  <CardTitle className={result.failed > 0 ? 'text-amber-900' : 'text-emerald-900'}>
                    Sending Results
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-emerald-700">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="font-semibold">{result.sent}</span> messages sent successfully
                    </div>
                    {result.failed > 0 && (
                      <div className="flex items-center gap-2 text-red-700">
                        <XCircle className="w-5 h-5" />
                        <span className="font-semibold">{result.failed}</span> messages failed
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-gray-700">
                      <Users className="w-5 h-5" />
                      <span className="font-semibold">{result.total}</span> total leads
                    </div>
                    <p className="text-sm text-gray-600 mt-2">{result.message}</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
