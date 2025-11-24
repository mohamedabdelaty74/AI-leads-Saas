'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { api, setTokens, clearTokens, getAccessToken } from '@/lib/api-client'
import { toast } from '@/components/ui/Toast'
import type { User } from '@/types/api'

export const useAuth = () => {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check if user is authenticated
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAccessToken()

      if (!token) {
        setLoading(false)
        return
      }

      try {
        const response = await api.auth.getCurrentUser()
        setUser(response.data)
      } catch (err) {
        console.error('Auth check failed:', err)
        clearTokens()
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await api.auth.login(email, password)
      const { access_token, refresh_token, user: userData } = response.data

      setTokens(access_token, refresh_token)
      setUser(userData)

      toast.success('Welcome back!')
      router.push('/dashboard')

      return { success: true }
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Login failed'
      setError(errorMessage)
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    } finally {
      setLoading(false)
    }
  }

  const register = async (data: {
    email: string
    password: string
    first_name?: string
    last_name?: string
    organization_name: string
  }) => {
    try {
      setLoading(true)
      setError(null)

      const response = await api.auth.register(data)
      const { access_token, refresh_token, user: userData } = response.data

      setTokens(access_token, refresh_token)
      setUser(userData)

      toast.success('Account created successfully!')
      router.push('/dashboard')

      return { success: true }
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Registration failed'
      setError(errorMessage)
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    clearTokens()
    setUser(null)
    toast.info('Logged out successfully')
    router.push('/login')
  }

  return {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  }
}
