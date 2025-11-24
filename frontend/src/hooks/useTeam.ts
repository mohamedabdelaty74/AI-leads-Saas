'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api-client'
import { toast } from '@/components/ui/Toast'

interface TeamMember {
  id: string
  email: string
  first_name?: string
  last_name?: string
  role: 'owner' | 'admin' | 'member'
  is_active: boolean
  created_at: string
  last_login_at?: string
}

export const useTeam = () => {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTeamMembers = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.team.list()
      setTeamMembers(response.data)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to fetch team members'
      setError(errorMessage)
      console.error('Error fetching team members:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTeamMembers()
  }, [])

  const inviteTeamMember = async (data: {
    email: string
    role: string
    first_name?: string
    last_name?: string
  }) => {
    try {
      const response = await api.team.invite(data)
      setTeamMembers(prev => [response.data, ...prev])
      toast.success(`Invitation sent to ${data.email}`)
      return { success: true, data: response.data }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to invite team member'
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  const updateTeamMemberRole = async (userId: string, role: string) => {
    try {
      const response = await api.team.updateRole(userId, role)
      setTeamMembers(prev =>
        prev.map(member => (member.id === userId ? { ...member, role: response.data.role } : member))
      )
      toast.success('Role updated successfully!')
      return { success: true, data: response.data }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to update role'
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  const removeTeamMember = async (userId: string) => {
    try {
      await api.team.remove(userId)
      setTeamMembers(prev => prev.filter(member => member.id !== userId))
      toast.success('Team member removed successfully!')
      return { success: true }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to remove team member'
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  return {
    teamMembers,
    loading,
    error,
    fetchTeamMembers,
    inviteTeamMember,
    updateTeamMemberRole,
    removeTeamMember,
  }
}
