'use client'

import React, { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import { toast } from 'react-hot-toast'
import {
  Zap,
  Upload,
  Users,
  Sparkles,
  TrendingUp,
  Info
} from 'lucide-react'

// Import components (to be created)
import ScrapingForm from '@/components/leads/ScrapingForm'
import CSVImporter from '@/components/leads/CSVImporter'
import LeadsTable from '@/components/leads/LeadsTable'

interface Campaign {
  id: string
  name: string
  description?: string
  status: string
  lead_source: string
  leads_count: number
  created_at: string
}

export default function UnifiedLeadsPage() {
  const params = useParams()
  const router = useRouter()
  const campaignId = params?.id as string

  // State
  const [activeTab, setActiveTab] = useState<'generate' | 'import' | 'manage'>('generate')
  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [loading, setLoading] = useState(true)
  const [leadsRefreshKey, setLeadsRefreshKey] = useState(0)

  // Fetch campaign details
  useEffect(() => {
    if (campaignId) {
      fetchCampaign()
    }
  }, [campaignId])

  // Check URL params for initial tab
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const tab = params.get('tab') as 'generate' | 'import' | 'manage' | null
      if (tab && ['generate', 'import', 'manage'].includes(tab)) {
        setActiveTab(tab)
      }
    }
  }, [])

  const fetchCampaign = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/login')
        return
      }

      const response = await fetch(`http://localhost:8000/api/v1/campaigns/${campaignId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!response.ok) {
        if (response.status === 401) {
          router.push('/login')
          return
        }
        throw new Error('Failed to fetch campaign')
      }

      const data = await response.json()
      setCampaign(data)
    } catch (error) {
      console.error('Error fetching campaign:', error)
      toast.error('Failed to load campaign')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateSuccess = () => {
    setActiveTab('manage')
    setLeadsRefreshKey(prev => prev + 1)
    toast.success('Leads generated successfully!')
  }

  const handleImportSuccess = () => {
    setActiveTab('manage')
    setLeadsRefreshKey(prev => prev + 1)
    toast.success('Leads imported successfully!')
  }


  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </DashboardLayout>
    )
  }

  if (!campaign) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">Campaign not found</p>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.push('/campaigns')}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back to Campaigns
              </button>
            </div>
            <h1 className="text-3xl font-bold mt-2 flex items-center gap-3">
              <Sparkles className="w-8 h-8 text-purple-600" />
              {campaign.name}
            </h1>
            <p className="text-gray-600 mt-1">
              {campaign.description || 'Manage and generate leads for this campaign'}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-gray-500">Status</p>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                campaign.status === 'active'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {campaign.status}
              </span>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Total Leads</p>
              <p className="text-2xl font-bold text-gray-900">{campaign.leads_count || 0}</p>
            </div>
          </div>
        </div>

        {/* Info Card */}
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="py-4">
            <div className="flex gap-3">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900">
                <p className="font-semibold mb-2">Unified Leads Hub</p>
                <p className="text-blue-800">
                  All lead operations in one place! Generate new leads from multiple sources, import existing leads from CSV,
                  or manage your current leads with AI-powered enrichment and bulk actions.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue={activeTab} onValueChange={(value) => setActiveTab(value as 'generate' | 'import' | 'manage')}>
          <TabsList>
            <TabsTrigger value="generate" icon={<Zap className="w-4 h-4" />}>
              <div className="flex items-center gap-2">
                <span>Generate New</span>
                <span className="ml-1 px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-700 rounded-full">
                  AI Powered
                </span>
              </div>
            </TabsTrigger>
            <TabsTrigger value="import" icon={<Upload className="w-4 h-4" />}>
              Import CSV
            </TabsTrigger>
            <TabsTrigger value="manage" icon={<Users className="w-4 h-4" />}>
              <div className="flex items-center gap-2">
                <span>Manage Leads</span>
                {campaign?.leads_count && campaign.leads_count > 0 && (
                  <span className="ml-1 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                    {campaign.leads_count}
                  </span>
                )}
              </div>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="generate">
            <ScrapingForm
              campaignId={campaignId}
              onSuccess={handleGenerateSuccess}
            />
          </TabsContent>

          <TabsContent value="import">
            <CSVImporter
              campaignId={campaignId}
              onSuccess={handleImportSuccess}
            />
          </TabsContent>

          <TabsContent value="manage">
            <LeadsTable
              campaignId={campaignId}
              refreshKey={leadsRefreshKey}
            />
          </TabsContent>
        </Tabs>

        {/* Quick Stats Footer */}
        <Card>
          <CardContent className="py-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-sm text-gray-500">Campaign Source</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {campaign.lead_source?.replace('_', ' ') || 'Mixed'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Created</p>
                <p className="text-lg font-semibold text-gray-900">
                  {new Date(campaign.created_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Campaign Status</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {campaign.status}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
