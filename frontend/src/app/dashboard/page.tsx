'use client'

import React from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { Users, TrendingUp, Mail, MessageSquare, ArrowRight, Plus, Loader2 } from 'lucide-react'
import { formatNumber } from '@/lib/utils'
import Button from '@/components/ui/Button'
import Link from 'next/link'
import { useDashboard } from '@/hooks/useDashboard'
import { useCampaigns } from '@/hooks/useCampaigns'

export default function DashboardPage() {
  const { stats, loading: statsLoading } = useDashboard()
  const { campaigns, loading: campaignsLoading } = useCampaigns()

  // Calculate percentage change for leads
  const leadsChange = stats && stats.leads_last_month > 0
    ? ((stats.leads_this_month - stats.leads_last_month) / stats.leads_last_month * 100)
    : 0

  // Get recent campaigns (last 5)
  const recentCampaigns = campaigns.slice(0, 5)

  // Format relative time
  const getRelativeTime = (dateString: string) => {
    const now = new Date()
    const date = new Date(dateString)
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 60) return `${diffMins} minutes ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    const diffWeeks = Math.floor(diffDays / 7)
    return `${diffWeeks} week${diffWeeks > 1 ? 's' : ''} ago`
  }

  // Map lead source to display name
  const getSourceName = (source: string) => {
    const sourceMap: Record<string, string> = {
      'google_maps': 'Google Maps',
      'linkedin': 'LinkedIn',
      'instagram': 'Instagram',
      'manual': 'Manual'
    }
    return sourceMap[source] || source
  }

  const statsData = stats ? [
    {
      label: 'Total Leads',
      value: formatNumber(stats.total_leads),
      change: leadsChange,
      changeLabel: 'vs last month',
      icon: <Users className="h-5 w-5" />,
      trend: leadsChange >= 0 ? 'up' as const : 'down' as const,
    },
    {
      label: 'Active Campaigns',
      value: stats.active_campaigns.toString(),
      change: 0,
      changeLabel: `${stats.total_campaigns} total`,
      icon: <TrendingUp className="h-5 w-5" />,
      trend: 'up' as const,
    },
    {
      label: 'Emails Sent',
      value: formatNumber(stats.emails_sent),
      change: 0,
      changeLabel: 'this month',
      icon: <Mail className="h-5 w-5" />,
      trend: 'up' as const,
    },
    {
      label: 'Response Rate',
      value: `${stats.response_rate}%`,
      change: stats.response_rate,
      changeLabel: 'engagement',
      icon: <MessageSquare className="h-5 w-5" />,
      trend: stats.response_rate > 20 ? 'up' as const : 'down' as const,
    },
  ] : []

  const quickActions = [
    {
      title: 'Generate New Leads',
      description: 'Start scraping leads from multiple sources',
      href: '/leads',
      icon: <Plus className="h-5 w-5" />,
      color: 'bg-primary-50 text-primary-600',
    },
    {
      title: 'Create Campaign',
      description: 'Organize your leads into campaigns',
      href: '/campaigns',
      icon: <TrendingUp className="h-5 w-5" />,
      color: 'bg-success-50 text-success-600',
    },
  ]

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Welcome back! Here's what's happening with your lead generation.
        </p>
      </div>

      {/* Stats Grid */}
      {statsLoading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsData.map((stat, index) => (
            <Card key={index} hover padding="md">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.label}</p>
                  <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-gray-100">{stat.value}</p>
                  <div className="mt-2 flex items-center gap-2">
                    {stat.change !== 0 && (
                      <Badge
                        variant={stat.trend === 'up' ? 'success' : 'error'}
                        size="sm"
                      >
                        {stat.change > 0 ? '+' : ''}{Math.round(stat.change)}%
                      </Badge>
                    )}
                    <span className="text-xs text-gray-500 dark:text-gray-500">{stat.changeLabel}</span>
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${stat.trend === 'up' ? 'bg-success-50 dark:bg-success-900/30' : 'bg-error-50 dark:bg-error-900/30'}`}>
                  <div className={stat.trend === 'up' ? 'text-success-600' : 'text-error-600'}>
                    {stat.icon}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Campaigns */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Recent Campaigns</CardTitle>
                  <CardDescription>Your latest lead generation campaigns</CardDescription>
                </div>
                <Link href="/campaigns">
                  <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="h-4 w-4" />}>
                    View All
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {campaignsLoading ? (
                <div className="flex justify-center items-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
                </div>
              ) : recentCampaigns.length > 0 ? (
                <div className="space-y-4">
                  {recentCampaigns.map((campaign) => (
                    <div
                      key={campaign.id}
                      className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 hover:bg-primary-50/50 dark:hover:bg-primary-900/20 transition-all cursor-pointer"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h4 className="font-semibold text-gray-900 dark:text-gray-100">{campaign.name}</h4>
                          <Badge
                            variant={campaign.status === 'active' ? 'success' : 'default'}
                            size="sm"
                          >
                            {campaign.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                          <span>{formatNumber(campaign.leads_count || 0)} leads</span>
                          <span>•</span>
                          <span>{getSourceName(campaign.lead_source)}</span>
                          <span>•</span>
                          <span>{getRelativeTime(campaign.created_at)}</span>
                        </div>
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-600 dark:text-gray-400 mb-4">No campaigns yet</p>
                  <Link href="/campaigns">
                    <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />}>
                      Create Campaign
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Get started with common tasks</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {quickActions.map((action, index) => (
                  <Link key={index} href={action.href}>
                    <div className="flex items-start gap-3 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 hover:bg-primary-50/50 dark:hover:bg-primary-900/20 transition-all cursor-pointer group">
                      <div className={`p-2 rounded-lg ${action.color}`}>
                        {action.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-700 dark:group-hover:text-primary-400">
                          {action.title}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                          {action.description}
                        </p>
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-primary-600 transition-colors flex-shrink-0 mt-1" />
                    </div>
                  </Link>
                ))}

                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <Link href="/settings">
                    <Button variant="outline" size="sm" className="w-full">
                      Configure Settings
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Activity Chart Placeholder */}
      <div className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Lead Generation Activity</CardTitle>
            <CardDescription>Leads generated over the last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
              <p className="text-gray-500 dark:text-gray-400">Chart visualization would go here (using Recharts)</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
