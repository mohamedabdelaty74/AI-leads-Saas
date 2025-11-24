'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Select from '@/components/ui/Select'
import { toast } from '@/components/ui/Toast'
import {
  BarChart3,
  Mail,
  Eye,
  MousePointer,
  MessageSquare,
  XCircle,
  Loader2,
  TrendingUp,
  Calendar
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface Campaign {
  id: string
  name: string
  status: string
}

interface EmailAnalytics {
  total_sent: number
  total_opened: number
  total_clicked: number
  total_replied: number
  total_failed: number
  open_rate: number
  click_rate: number
  reply_rate: number
}

interface EmailLog {
  id: string
  lead_id: string
  campaign_id: string
  recipient_email: string
  subject: string
  status: string
  sent_at: string | null
  opened_at: string | null
  error_message: string | null
  created_at: string
}

export default function EmailAnalyticsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState('')
  const [analytics, setAnalytics] = useState<EmailAnalytics | null>(null)
  const [emailLogs, setEmailLogs] = useState<EmailLog[]>([])
  const [loading, setLoading] = useState(false)
  const [logsLoading, setLogsLoading] = useState(false)

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

      // Auto-select first campaign
      if (data.length > 0 && !selectedCampaignId) {
        setSelectedCampaignId(data[0].id)
      }
    } catch (error) {
      console.error('Error fetching campaigns:', error)
      toast.error('Failed to load campaigns')
    }
  }

  // Fetch analytics
  const fetchAnalytics = async (campaignId: string) => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/email-analytics`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) throw new Error('Failed to fetch analytics')

      const data = await response.json()
      setAnalytics(data)
    } catch (error) {
      console.error('Error fetching analytics:', error)
      toast.error('Failed to load email analytics')
    } finally {
      setLoading(false)
    }
  }

  // Fetch email logs
  const fetchEmailLogs = async (campaignId: string) => {
    try {
      setLogsLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/email-logs`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) throw new Error('Failed to fetch email logs')

      const data = await response.json()
      setEmailLogs(data)
    } catch (error) {
      console.error('Error fetching email logs:', error)
      toast.error('Failed to load email logs')
    } finally {
      setLogsLoading(false)
    }
  }

  useEffect(() => {
    fetchCampaigns()
  }, [])

  useEffect(() => {
    if (selectedCampaignId) {
      fetchAnalytics(selectedCampaignId)
      fetchEmailLogs(selectedCampaignId)
    }
  }, [selectedCampaignId])

  const campaignOptions = campaigns.map(c => ({
    value: c.id,
    label: `${c.name} (${c.status})`
  }))

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'sent':
        return <Badge variant="success">Sent</Badge>
      case 'opened':
        return <Badge variant="info">Opened</Badge>
      case 'clicked':
        return <Badge variant="success">Clicked</Badge>
      case 'replied':
        return <Badge variant="success">Replied</Badge>
      case 'failed':
        return <Badge variant="danger">Failed</Badge>
      case 'bounced':
        return <Badge variant="warning">Bounced</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-blue-600" />
              Email Analytics
            </h1>
            <p className="text-gray-600 mt-1">
              Track your email campaign performance and engagement
            </p>
          </div>
        </div>

        {/* Campaign Selection */}
        <Card>
          <CardContent className="py-4">
            <Select
              options={campaignOptions}
              value={selectedCampaignId}
              onChange={(e) => setSelectedCampaignId(e.target.value)}
              placeholder="Select a campaign to view analytics..."
            />
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : analytics ? (
          <>
            {/* Analytics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Total Sent */}
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Total Sent</p>
                      <p className="text-3xl font-bold text-gray-900 mt-1">
                        {analytics.total_sent}
                      </p>
                    </div>
                    <Mail className="w-12 h-12 text-blue-600 opacity-50" />
                  </div>
                </CardContent>
              </Card>

              {/* Opened */}
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Opened</p>
                      <p className="text-3xl font-bold text-purple-600 mt-1">
                        {analytics.total_opened}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {analytics.open_rate}% open rate
                      </p>
                    </div>
                    <Eye className="w-12 h-12 text-purple-600 opacity-50" />
                  </div>
                </CardContent>
              </Card>

              {/* Clicked */}
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Clicked</p>
                      <p className="text-3xl font-bold text-green-600 mt-1">
                        {analytics.total_clicked}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {analytics.click_rate}% click rate
                      </p>
                    </div>
                    <MousePointer className="w-12 h-12 text-green-600 opacity-50" />
                  </div>
                </CardContent>
              </Card>

              {/* Replied */}
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Replied</p>
                      <p className="text-3xl font-bold text-amber-600 mt-1">
                        {analytics.total_replied}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {analytics.reply_rate}% reply rate
                      </p>
                    </div>
                    <MessageSquare className="w-12 h-12 text-amber-600 opacity-50" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Performance Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Campaign Performance</CardTitle>
                <CardDescription>
                  Overall engagement metrics for this campaign
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Open Rate Bar */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Open Rate</span>
                      <span className="text-sm font-bold text-purple-600">{analytics.open_rate}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-purple-600 h-3 rounded-full transition-all"
                        style={{ width: `${Math.min(analytics.open_rate, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Click Rate Bar */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Click Rate</span>
                      <span className="text-sm font-bold text-green-600">{analytics.click_rate}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-green-600 h-3 rounded-full transition-all"
                        style={{ width: `${Math.min(analytics.click_rate, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Reply Rate Bar */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Reply Rate</span>
                      <span className="text-sm font-bold text-amber-600">{analytics.reply_rate}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-amber-600 h-3 rounded-full transition-all"
                        style={{ width: `${Math.min(analytics.reply_rate, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Failed */}
                  {analytics.total_failed > 0 && (
                    <div className="pt-2 border-t">
                      <div className="flex items-center gap-2 text-sm">
                        <XCircle className="w-4 h-4 text-red-600" />
                        <span className="text-gray-700">
                          {analytics.total_failed} emails failed to send
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Email Logs Table */}
            <Card>
              <CardHeader>
                <CardTitle>Email Activity Log</CardTitle>
                <CardDescription>
                  Detailed log of all emails sent in this campaign
                </CardDescription>
              </CardHeader>
              <CardContent>
                {logsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                  </div>
                ) : emailLogs.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Mail className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>No emails sent yet for this campaign</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="px-4 py-3 text-left font-semibold text-gray-700">Recipient</th>
                          <th className="px-4 py-3 text-left font-semibold text-gray-700">Subject</th>
                          <th className="px-4 py-3 text-left font-semibold text-gray-700">Status</th>
                          <th className="px-4 py-3 text-left font-semibold text-gray-700">Sent At</th>
                          <th className="px-4 py-3 text-left font-semibold text-gray-700">Opened At</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {emailLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-gray-900">
                              {log.recipient_email}
                            </td>
                            <td className="px-4 py-3 text-gray-700 max-w-xs truncate">
                              {log.subject}
                            </td>
                            <td className="px-4 py-3">
                              {getStatusBadge(log.status)}
                            </td>
                            <td className="px-4 py-3 text-gray-600">
                              {log.sent_at ? formatDate(log.sent_at) : '-'}
                            </td>
                            <td className="px-4 py-3 text-gray-600">
                              {log.opened_at ? formatDate(log.opened_at) : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Insights */}
            {analytics.total_sent > 0 && (
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="py-4">
                  <div className="flex gap-3">
                    <TrendingUp className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-900">
                      <p className="font-semibold mb-2">Performance Insights:</p>
                      <ul className="space-y-1 text-blue-800">
                        {analytics.open_rate > 20 && (
                          <li>Great open rate! Your subject lines are working well.</li>
                        )}
                        {analytics.open_rate < 15 && analytics.total_sent > 10 && (
                          <li>Consider improving your subject lines to increase open rates.</li>
                        )}
                        {analytics.reply_rate > 5 && (
                          <li>Excellent reply rate! Your emails are engaging prospects.</li>
                        )}
                        {analytics.total_failed > analytics.total_sent * 0.1 && (
                          <li>High failure rate detected. Check email addresses for validity.</li>
                        )}
                        {analytics.total_sent < 10 && (
                          <li>Send more emails to get meaningful analytics data.</li>
                        )}
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <BarChart3 className="w-16 h-16 text-gray-400 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No Analytics Available
              </h3>
              <p className="text-gray-600">
                Select a campaign to view email analytics
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
