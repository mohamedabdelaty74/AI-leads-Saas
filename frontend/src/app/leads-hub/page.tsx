'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { toast } from 'react-hot-toast'
import {
  FolderKanban,
  ArrowRight,
  Plus,
  Loader2,
  Users,
  Sparkles
} from 'lucide-react'

interface Campaign {
  id: string
  name: string
  description?: string
  status: string
  lead_source: string
  leads_count: number
  created_at: string
}

export default function LeadsHubPage() {
  const router = useRouter()
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const fetchCampaigns = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/login')
        return
      }

      const response = await fetch('http://localhost:8000/api/v1/campaigns', {
        headers: { 'Authorization': `Bearer ${token}` }
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

      // If only one campaign, auto-navigate
      if (data.length === 1) {
        router.push(`/campaigns/${data[0].id}/leads`)
      }
    } catch (error) {
      console.error('Error fetching campaigns:', error)
      toast.error('Failed to load campaigns')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-purple-600" />
            Leads Hub
          </h1>
          <p className="text-gray-600 mt-1">
            Select a campaign to manage, generate, or import leads
          </p>
        </div>

        {campaigns.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FolderKanban className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p className="text-gray-500 mb-4">No campaigns found. Create one to get started.</p>
              <Button onClick={() => router.push('/campaigns')}>
                <Plus className="w-4 h-4 mr-2" /> Create Campaign
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {campaigns.map((campaign) => (
              <Card key={campaign.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="text-xl font-semibold text-gray-900">{campaign.name}</h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          campaign.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {campaign.status}
                        </span>
                      </div>
                      {campaign.description && (
                        <p className="text-gray-600 mt-1">{campaign.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {campaign.leads_count} leads
                        </span>
                        <span className="capitalize">
                          Source: {campaign.lead_source?.replace('_', ' ') || 'Mixed'}
                        </span>
                        <span>
                          Created: {new Date(campaign.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <Button
                      onClick={() => router.push(`/campaigns/${campaign.id}/leads`)}
                      variant="primary"
                    >
                      Manage Leads
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
