'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api-client'

interface DashboardStats {
  total_leads: number
  total_campaigns: number
  active_campaigns: number
  emails_sent: number
  response_rate: number
  leads_this_month: number
  leads_last_month: number
}

export const useDashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.dashboard.getStats()
      setStats(response.data)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to fetch dashboard stats'
      setError(errorMessage)
      console.error('Error fetching dashboard stats:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  return {
    stats,
    loading,
    error,
    fetchStats,
  }
}
