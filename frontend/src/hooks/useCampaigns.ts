'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api-client'
import { toast } from '@/components/ui/Toast'

interface Campaign {
  id: string
  name: string
  description?: string
  status: 'draft' | 'active' | 'paused' | 'completed'
  lead_source: 'google_maps' | 'linkedin' | 'instagram' | 'manual'
  leads_count?: number
  emails_sent?: number
  response_rate?: number
  created_at: string
}

export const useCampaigns = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCampaigns = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.campaigns.list()
      setCampaigns(response.data)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to fetch campaigns'
      setError(errorMessage)
      console.error('Error fetching campaigns:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const createCampaign = async (data: {
    name: string
    description?: string
    lead_source: string
  }) => {
    try {
      const response = await api.campaigns.create(data)
      setCampaigns(prev => [...prev, response.data])
      toast.success('Campaign created successfully!')
      return { success: true, data: response.data }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create campaign'
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  const updateCampaign = async (id: string, data: Partial<Campaign>) => {
    try {
      const response = await api.campaigns.update(id, data)
      setCampaigns(prev =>
        prev.map(c => (c.id === id ? { ...c, ...response.data } : c))
      )
      toast.success('Campaign updated successfully!')
      return { success: true, data: response.data }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to update campaign'
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  const deleteCampaign = async (id: string) => {
    try {
      await api.campaigns.delete(id)
      setCampaigns(prev => prev.filter(c => c.id !== id))
      toast.success('Campaign deleted successfully!')
      return { success: true }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to delete campaign'
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  return {
    campaigns,
    loading,
    error,
    fetchCampaigns,
    createCampaign,
    updateCampaign,
    deleteCampaign,
  }
}
