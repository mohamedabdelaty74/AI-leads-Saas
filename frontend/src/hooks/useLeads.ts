'use client'

import { useState } from 'react'
import { api } from '@/lib/api-client'
import { toast } from '@/components/ui/Toast'

interface Lead {
  id: string
  title: string
  email?: string
  phone?: string
  website?: string
  address?: string
  rating?: number
  reviews_count?: number
  category?: string
  generated_email?: string
  generated_whatsapp?: string
  email_sent: boolean
  whatsapp_sent: boolean
  created_at: string
}

export const useLeads = (campaignId?: string) => {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const parseErrorMessage = (err: any, defaultMessage: string): string => {
    const detail = err.response?.data?.detail
    if (!detail) return defaultMessage

    // Handle Pydantic validation errors (array of {type, loc, msg, input})
    if (Array.isArray(detail)) {
      return detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ')
    } else if (typeof detail === 'string') {
      return detail
    } else if (typeof detail === 'object') {
      return detail.msg || detail.message || JSON.stringify(detail)
    }
    return defaultMessage
  }

  const fetchLeads = async (cid: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.leads.list(cid)
      setLeads(response.data)
    } catch (err: any) {
      const errorMessage = parseErrorMessage(err, 'Failed to fetch leads')
      setError(errorMessage)
      console.error('Error fetching leads:', err)
    } finally {
      setLoading(false)
    }
  }

  const addLead = async (campaignId: string, data: Partial<Lead>) => {
    try {
      const response = await api.leads.create(campaignId, data)
      setLeads(prev => [...prev, response.data])
      toast.success('Lead added successfully!')
      return { success: true, data: response.data }
    } catch (err: any) {
      const errorMessage = parseErrorMessage(err, 'Failed to add lead')
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  const addLeadsBulk = async (campaignId: string, leadsData: Partial<Lead>[]) => {
    try {
      setLoading(true)
      const response = await api.leads.bulkCreate(campaignId, leadsData)
      await fetchLeads(campaignId) // Refresh the list
      toast.success(`${leadsData.length} leads added successfully!`)
      return { success: true, data: response.data }
    } catch (err: any) {
      const errorMessage = parseErrorMessage(err, 'Failed to add leads')
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    } finally {
      setLoading(false)
    }
  }

  return {
    leads,
    loading,
    error,
    fetchLeads,
    addLead,
    addLeadsBulk,
  }
}
