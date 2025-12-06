'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import Table from '@/components/ui/Table'
import { SkeletonTable } from '@/components/ui/Skeleton'
import { toast } from '@/components/ui/Toast'
import FileUpload from '@/components/ui/FileUpload'
import { useCampaigns } from '@/hooks/useCampaigns'
import { useLeads } from '@/hooks/useLeads'
import {
  Search,
  MapPin,
  Linkedin,
  Instagram,
  Download,
  Sparkles,
  Filter,
  Plus,
  RefreshCw,
  AlertCircle,
  Upload,
  FileUp,
  Loader2,
  Edit2,
  Trash2,
  Globe,
  X,
  Clock,
  CheckCircle2,
  Mail,
  MessageCircle,
  Send
} from 'lucide-react'

// Type for pending tasks
interface PendingTask {
  leadId: string
  leadName: string
  type: 'description' | 'deep_research' | 'email' | 'whatsapp'
  startTime: number
}

// LocalStorage key for pending tasks
const PENDING_TASKS_KEY = 'elite_creatif_pending_tasks'

export default function LeadsPage() {
  const [activeTab, setActiveTab] = useState('google-maps')
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('')

  // Hooks
  const { campaigns, loading: campaignsLoading } = useCampaigns()
  const { leads, loading: leadsLoading, fetchLeads, addLeadsBulk } = useLeads()

  // Google Maps State
  const [googleQuery, setGoogleQuery] = useState('')
  const [googleMaxResults, setGoogleMaxResults] = useState(50)
  const [googleLocation, setGoogleLocation] = useState('')

  // LinkedIn State
  const [linkedinQuery, setLinkedinQuery] = useState('')
  const [linkedinMaxResults, setLinkedinMaxResults] = useState(20)

  // Instagram State
  const [instagramQuery, setInstagramQuery] = useState('')
  const [instagramMaxResults, setInstagramMaxResults] = useState(30)

  // Upload State
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [generateDescriptions, setGenerateDescriptions] = useState(true)
  const [generateEmails, setGenerateEmails] = useState(true)
  const [companyInfo, setCompanyInfo] = useState('')
  const [uploading, setUploading] = useState(false)

  // Edit/Delete State
  const [editingLead, setEditingLead] = useState<any>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [deletingLeadId, setDeletingLeadId] = useState<string | null>(null)

  // Generate AI State
  const [generatingDescriptionId, setGeneratingDescriptionId] = useState<string | null>(null)
  const [generatingDeepResearchId, setGeneratingDeepResearchId] = useState<string | null>(null)
  const [generatingEmailId, setGeneratingEmailId] = useState<string | null>(null)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailCompanyInfo, setEmailCompanyInfo] = useState('')
  const [currentLeadForEmail, setCurrentLeadForEmail] = useState<any>(null)

  // WhatsApp Generation State
  const [generatingWhatsappId, setGeneratingWhatsappId] = useState<string | null>(null)
  const [showWhatsappModal, setShowWhatsappModal] = useState(false)
  const [whatsappCompanyInfo, setWhatsappCompanyInfo] = useState('')
  const [currentLeadForWhatsapp, setCurrentLeadForWhatsapp] = useState<any>(null)

  // Enrich Leads State
  const [enrichingLeads, setEnrichingLeads] = useState(false)
  const enrichAbortRef = useRef<AbortController | null>(null)

  // Lead Generation Loading States
  const [generatingGoogleLeads, setGeneratingGoogleLeads] = useState(false)
  const [generatingLinkedinLeads, setGeneratingLinkedinLeads] = useState(false)
  const [generatingInstagramLeads, setGeneratingInstagramLeads] = useState(false)
  const [generationStatus, setGenerationStatus] = useState('')

  // Pending tasks and auto-refresh
  const [pendingTasks, setPendingTasks] = useState<PendingTask[]>([])
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false)
  const autoRefreshIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastRefreshTimeRef = useRef<number>(0)

  // AbortController refs for cancellation (only for active UI operations)
  const descriptionAbortRef = useRef<AbortController | null>(null)
  const deepResearchAbortRef = useRef<AbortController | null>(null)
  const emailAbortRef = useRef<AbortController | null>(null)

  // Bulk Automation State
  const [selectedLeads, setSelectedLeads] = useState<string[]>([])
  const [selectAll, setSelectAll] = useState(false)
  const [bulkGeneratingDescriptions, setBulkGeneratingDescriptions] = useState(false)
  const [bulkGeneratingEmails, setBulkGeneratingEmails] = useState(false)
  const [bulkGeneratingWhatsApp, setBulkGeneratingWhatsApp] = useState(false)
  const [sendingEmails, setSendingEmails] = useState(false)
  const [sendingWhatsApp, setSendingWhatsApp] = useState(false)

  // AbortControllers for cancelling operations
  const abortControllerDescriptions = useRef<AbortController | null>(null)
  const abortControllerEmails = useRef<AbortController | null>(null)
  const abortControllerWhatsApp = useRef<AbortController | null>(null)

  // Send Email Dialog State
  const [showSendEmailDialog, setShowSendEmailDialog] = useState(false)
  const [senderEmail, setSenderEmail] = useState('')
  const [senderPassword, setSenderPassword] = useState('')
  const [bulkEmailCompanyInfo, setBulkEmailCompanyInfo] = useState('')

  // Send WhatsApp Dialog State
  const [showSendWhatsAppDialog, setShowSendWhatsAppDialog] = useState(false)
  const [whatsappPhoneNumberId, setWhatsappPhoneNumberId] = useState('')
  const [whatsappAccessToken, setWhatsappAccessToken] = useState('')
  const [bulkWhatsAppCompanyInfo, setBulkWhatsAppCompanyInfo] = useState('')

  // Load pending tasks from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(PENDING_TASKS_KEY)
    if (stored) {
      try {
        const tasks = JSON.parse(stored) as PendingTask[]
        // Filter out tasks older than 30 minutes
        const validTasks = tasks.filter(t => Date.now() - t.startTime < 30 * 60 * 1000)
        setPendingTasks(validTasks)
        // Auto-refresh disabled - user can manually refresh
        // Update localStorage with filtered tasks
        localStorage.setItem(PENDING_TASKS_KEY, JSON.stringify(validTasks))
      } catch (e) {
        localStorage.removeItem(PENDING_TASKS_KEY)
      }
    }
  }, [])

  // Save pending tasks to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(PENDING_TASKS_KEY, JSON.stringify(pendingTasks))
  }, [pendingTasks])

  // Auto-refresh logic with debouncing
  useEffect(() => {
    if (autoRefreshEnabled && selectedCampaignId && pendingTasks.length > 0) {
      // Clear any existing interval
      if (autoRefreshIntervalRef.current) {
        clearInterval(autoRefreshIntervalRef.current)
      }

      // Start auto-refresh every 30 seconds (increased from 15)
      // with a 5 second initial delay to prevent instant refresh on page load
      const initialDelay = setTimeout(() => {
        autoRefreshIntervalRef.current = setInterval(() => {
          const now = Date.now()
          // Only refresh if at least 10 seconds have passed since last refresh
          if (now - lastRefreshTimeRef.current >= 10000) {
            lastRefreshTimeRef.current = now
            fetchLeads(selectedCampaignId)
          }
        }, 30000)
      }, 5000)

      return () => {
        clearTimeout(initialDelay)
        if (autoRefreshIntervalRef.current) {
          clearInterval(autoRefreshIntervalRef.current)
        }
      }
    } else if (autoRefreshIntervalRef.current) {
      clearInterval(autoRefreshIntervalRef.current)
      autoRefreshIntervalRef.current = null
    }
  }, [autoRefreshEnabled, selectedCampaignId, pendingTasks.length])

  // Check if pending tasks are completed when leads are refreshed
  useEffect(() => {
    if (leads.length > 0 && pendingTasks.length > 0) {
      const completedTasks: string[] = []

      pendingTasks.forEach(task => {
        const lead = leads.find(l => l.id === task.leadId)
        if (lead) {
          if (task.type === 'description' && lead.description) {
            completedTasks.push(task.leadId)
            toast.success(`AI description completed for ${task.leadName}!`)
          } else if (task.type === 'email' && lead.generated_email) {
            completedTasks.push(task.leadId)
            toast.success(`AI email completed for ${task.leadName}!`)
          }
        }
      })

      if (completedTasks.length > 0) {
        setPendingTasks(prev => prev.filter(t => !completedTasks.includes(t.leadId)))
      }
    }
  }, [leads])

  // Cleanup on unmount - only clear intervals, don't abort requests
  // Backend will continue processing even if user navigates away
  useEffect(() => {
    return () => {
      if (autoRefreshIntervalRef.current) {
        clearInterval(autoRefreshIntervalRef.current)
      }
      // Note: We don't abort requests here because the backend will continue processing
      // The pending tasks are saved in localStorage and will be restored when user returns
    }
  }, [])

  // Helper to add pending task
  const addPendingTask = (leadId: string, leadName: string, type: 'description' | 'email') => {
    setPendingTasks(prev => [...prev, { leadId, leadName, type, startTime: Date.now() }])
    // Auto-refresh disabled - user can manually refresh
  }

  // Helper to remove pending task
  const removePendingTask = (leadId: string) => {
    setPendingTasks(prev => prev.filter(t => t.leadId !== leadId))
  }

  // Cancel generation handler
  const handleCancelGeneration = async (leadId: string, type: 'description' | 'email') => {
    console.log('🛑 CANCEL CLICKED - Lead ID:', leadId, 'Type:', type)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in')
        return
      }

      console.log('🌐 Sending cancel request to backend...')

      // Call backend cancel endpoint
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/leads/${leadId}/cancel-generation`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      console.log('📡 Cancel response status:', response.status)

      if (!response.ok) {
        throw new Error('Failed to cancel generation')
      }

      const data = await response.json()

      // Also abort the HTTP request on frontend side
      if (type === 'description' && descriptionAbortRef.current) {
        descriptionAbortRef.current.abort()
        setGeneratingDescriptionId(null)
      } else if (type === 'deep_research' && deepResearchAbortRef.current) {
        deepResearchAbortRef.current.abort()
        setGeneratingDeepResearchId(null)
      } else if (type === 'email' && emailAbortRef.current) {
        emailAbortRef.current.abort()
        setGeneratingEmailId(null)
        setShowEmailModal(false)
      }

      removePendingTask(leadId)

      if (data.status === 'cancelled') {
        toast.success(`Cancelled ${data.cancelled_tasks.join(', ')} generation`)
      } else {
        toast.info('No active generation tasks found')
      }

    } catch (error) {
      console.error('Error cancelling generation:', error)
      toast.error('Failed to cancel generation')

      // Fallback: still abort the frontend request
      if (type === 'description' && descriptionAbortRef.current) {
        descriptionAbortRef.current.abort()
        setGeneratingDescriptionId(null)
      } else if (type === 'deep_research' && deepResearchAbortRef.current) {
        deepResearchAbortRef.current.abort()
        setGeneratingDeepResearchId(null)
      } else if (type === 'email' && emailAbortRef.current) {
        emailAbortRef.current.abort()
        setGeneratingEmailId(null)
        setShowEmailModal(false)
      }
      removePendingTask(leadId)
    }
  }

  // Set first campaign as default when campaigns load
  useEffect(() => {
    if (campaigns.length > 0 && !selectedCampaignId) {
      setSelectedCampaignId(campaigns[0].id)
    }
  }, [campaigns, selectedCampaignId])

  // Fetch leads when campaign is selected
  useEffect(() => {
    if (selectedCampaignId) {
      lastRefreshTimeRef.current = Date.now()
      fetchLeads(selectedCampaignId)
    }
  }, [selectedCampaignId])

  const handleGoogleSearch = async () => {
    if (!googleQuery.trim()) {
      toast.error('Please enter a search query')
      return
    }

    if (!selectedCampaignId) {
      toast.error('Please select a campaign first')
      return
    }

    try {
      setGeneratingGoogleLeads(true)
      setGenerationStatus('Initializing Google Maps search...')

      // Call the REAL backend API to generate leads from Google Maps
      const token = localStorage.getItem('access_token')

      if (!token) {
        toast.error('You must be logged in to generate leads')
        return
      }

      setGenerationStatus('Searching Google Maps for businesses...')

      const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/generate-leads?` +
                  `query=${encodeURIComponent(googleQuery)}&` +
                  `location=${encodeURIComponent(googleLocation || '')}&` +
                  `max_results=${googleMaxResults}`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to generate leads')
      }

      setGenerationStatus('Processing results...')
      const data = await response.json()
      toast.success(`Generated ${data.leads_generated} REAL leads from Google Maps!`)

      // Refresh the leads list to show the new leads
      setGenerationStatus('Loading leads...')
      await fetchLeads(selectedCampaignId)
    } catch (error) {
      console.error('Error generating leads:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to generate leads')
    } finally {
      setGeneratingGoogleLeads(false)
      setGenerationStatus('')
    }
  }

  const handleLinkedinSearch = async () => {
    if (!linkedinQuery.trim()) {
      toast.error('Please enter a search query')
      return
    }

    if (!selectedCampaignId) {
      toast.error('Please select a campaign first')
      return
    }

    try {
      setGeneratingLinkedinLeads(true)
      setGenerationStatus('Initializing LinkedIn search...')

      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in to generate leads')
        return
      }

      setGenerationStatus('Searching LinkedIn for companies...')

      const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/generate-linkedin-leads?` +
                  `query=${encodeURIComponent(linkedinQuery)}&` +
                  `max_results=${linkedinMaxResults}`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to generate LinkedIn leads')
      }

      setGenerationStatus('Processing results...')
      const data = await response.json()
      toast.success(`Generated ${data.leads_generated} leads from LinkedIn!`)

      setGenerationStatus('Loading leads...')
      await fetchLeads(selectedCampaignId)
    } catch (error) {
      console.error('Error generating LinkedIn leads:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to generate LinkedIn leads')
    } finally {
      setGeneratingLinkedinLeads(false)
      setGenerationStatus('')
    }
  }

  const handleInstagramSearch = async () => {
    if (!instagramQuery.trim()) {
      toast.error('Please enter a search query')
      return
    }

    if (!selectedCampaignId) {
      toast.error('Please select a campaign first')
      return
    }

    try {
      setGeneratingInstagramLeads(true)
      setGenerationStatus('Initializing Instagram search...')

      // Call the REAL backend API to generate leads from Instagram
      const token = localStorage.getItem('access_token')

      if (!token) {
        toast.error('You must be logged in to generate leads')
        return
      }

      setGenerationStatus('Searching Instagram for accounts...')

      const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/generate-instagram-leads?` +
                  `query=${encodeURIComponent(instagramQuery)}&` +
                  `max_results=${instagramMaxResults}`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to generate Instagram leads')
      }

      setGenerationStatus('Processing results...')
      const data = await response.json()
      toast.success(`Generated ${data.leads_generated} leads from Instagram!`)

      // Refresh the leads list to show the new leads
      setGenerationStatus('Loading leads...')
      await fetchLeads(selectedCampaignId)
    } catch (error) {
      console.error('Error generating Instagram leads:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to generate Instagram leads')
    } finally {
      setGeneratingInstagramLeads(false)
      setGenerationStatus('')
    }
  }

  const handleCancelLeadGeneration = async () => {
    if (!selectedCampaignId) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in')
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/cancel-generation`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (!response.ok) {
        throw new Error('Failed to cancel lead generation')
      }

      const data = await response.json()

      // Reset all generation states
      setGeneratingGoogleLeads(false)
      setGeneratingLinkedinLeads(false)
      setGeneratingInstagramLeads(false)
      setGenerationStatus('')

      if (data.cancelled) {
        toast.success(`Lead generation cancelled from ${data.source}`)
        // Refresh leads to show any partially generated leads
        await fetchLeads(selectedCampaignId)
      } else {
        toast.info(data.message)
      }
    } catch (error) {
      console.error('Error cancelling lead generation:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to cancel lead generation')
    }
  }

  const handleExport = () => {
    if (leads.length === 0) {
      toast.error('No leads to export')
      return
    }

    try {
      // Prepare CSV data with enhanced fields for Instagram and LinkedIn leads
      const headers = [
        'Name',
        'Username/Location',
        'Email',
        'Phone',
        'WhatsApp',
        'Website',
        'External Website',
        'Job Title',
        'Company',
        'Industry/Category',
        'Followers',
        'Connections',
        'Posts/Experience',
        'Seniority/Engagement',
        'Lead Score',
        'Bio',
        'Source',
        'Has Contact',
        'AI Email'
      ]
      const csvData = leads.map(lead => [
        lead.title || '',
        lead.address || lead.scraped_data?.username || '',
        lead.email || '',
        lead.phone || '',
        lead.scraped_data?.whatsapp || '',
        lead.website || '',
        lead.scraped_data?.external_website || '',
        lead.scraped_data?.job_title || '',
        lead.scraped_data?.company || '',
        lead.scraped_data?.industry || lead.scraped_data?.category || '',
        lead.scraped_data?.followers_display || lead.scraped_data?.followers || '',
        lead.scraped_data?.connections_display || lead.scraped_data?.connections || lead.scraped_data?.following || '',
        lead.scraped_data?.experience_years ? `${lead.scraped_data.experience_years} years` : lead.scraped_data?.posts || '',
        lead.scraped_data?.seniority || lead.scraped_data?.engagement_category || '',
        lead.lead_score || '',
        lead.scraped_data?.bio || lead.description || '',
        lead.contact_source || '',
        lead.scraped_data?.has_contact ? 'Yes' : 'No',
        lead.generated_email || ''
      ])

      // Convert to CSV string
      const csvContent = [
        headers.join(','),
        ...csvData.map(row =>
          row.map(cell => {
            // Escape quotes and wrap in quotes if contains comma
            const cellStr = String(cell).replace(/"/g, '""')
            return cellStr.includes(',') || cellStr.includes('\n') ? `"${cellStr}"` : cellStr
          }).join(',')
        )
      ].join('\n')

      // Create blob and download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)

      link.setAttribute('href', url)
      link.setAttribute('download', `leads_export_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      URL.revokeObjectURL(url)

      toast.success(`Exported ${leads.length} leads to CSV`)
    } catch (error) {
      console.error('Export error:', error)
      toast.error('Failed to export leads')
    }
  }

  const handleFileUpload = async () => {
    if (!uploadedFile) {
      toast.error('Please select a file first')
      return
    }

    if (!selectedCampaignId) {
      toast.error('Please select a campaign first')
      return
    }

    if (generateEmails && !companyInfo.trim()) {
      toast.error('Please enter your company information for AI email generation')
      return
    }

    try {
      setUploading(true)

      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in')
        return
      }

      // Create form data
      const formData = new FormData()
      formData.append('file', uploadedFile)

      // Build URL with query parameters
      const url = new URL(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/upload-leads`)
      url.searchParams.append('generate_descriptions', generateDescriptions.toString())
      url.searchParams.append('generate_emails', generateEmails.toString())
      if (generateEmails && companyInfo) {
        url.searchParams.append('company_info', companyInfo)
      }

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to upload leads')
      }

      const data = await response.json()

      // Show detailed results
      if (data.stats.leads_created > 0) {
        toast.success(
          `Successfully uploaded ${data.stats.leads_created} leads! ` +
          (data.stats.descriptions_generated > 0 ? `${data.stats.descriptions_generated} descriptions generated. ` : '') +
          (data.stats.emails_generated > 0 ? `${data.stats.emails_generated} emails generated.` : '')
        )
      }

      // Show warnings for failed rows
      if (data.stats.leads_failed > 0) {
        const failureReasons = data.failed_rows?.map((f: any) => `Row ${f.row}: ${f.reason}`).join('\n') || ''
        console.warn('Failed rows:', data.failed_rows)
        toast.error(
          `${data.stats.leads_failed} rows failed to import.\n` +
          `Check the console (F12) for details.\n\n` +
          `Common issues:\n- Missing company name\n- Invalid data format`
        )
      }

      // If no leads were created at all
      if (data.stats.leads_created === 0) {
        toast.error(
          `No leads were imported! All ${data.stats.total_rows} rows failed.\n\n` +
          `Check your CSV format:\n` +
          `- Must have a "Name" or "Company" column\n` +
          `- Rows must not be empty\n\n` +
          `Check browser console (F12) for detailed errors.`
        )
      }

      // Reset form
      setUploadedFile(null)
      setCompanyInfo('')

      // Refresh leads
      fetchLeads(selectedCampaignId)

    } catch (error: any) {
      console.error('Upload error:', error)
      toast.error(error.message || 'Failed to upload leads')
    } finally {
      setUploading(false)
    }
  }

  const handleEditLead = (lead: any) => {
    setEditingLead({...lead})
    setShowEditModal(true)
  }

  const handleSaveLead = async () => {
    if (!editingLead) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/leads/${editingLead.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editingLead)
      })

      if (!response.ok) throw new Error('Failed to update lead')

      toast.success('Lead updated successfully!')
      setShowEditModal(false)
      setEditingLead(null)

      // Refresh leads
      if (selectedCampaignId) {
        fetchLeads(selectedCampaignId)
      }
    } catch (error: any) {
      console.error('Update error:', error)
      toast.error(error.message || 'Failed to update lead')
    }
  }

  const handleDeleteLead = async (leadId: string) => {
    if (!confirm('Are you sure you want to delete this lead? This action cannot be undone.')) {
      return
    }

    try {
      setDeletingLeadId(leadId)
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/leads/${leadId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) throw new Error('Failed to delete lead')

      toast.success('Lead deleted successfully!')

      // Refresh leads
      if (selectedCampaignId) {
        fetchLeads(selectedCampaignId)
      }
    } catch (error: any) {
      console.error('Delete error:', error)
      toast.error(error.message || 'Failed to delete lead')
    } finally {
      setDeletingLeadId(null)
    }
  }

  const handleDeleteAllLeads = async () => {
    if (!selectedCampaignId) {
      toast.error('Please select a campaign first')
      return
    }

    if (!confirm(`Are you sure you want to delete ALL ${leads.length} leads in this campaign? This action cannot be undone.`)) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/leads`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) throw new Error('Failed to delete all leads')

      toast.success(`Successfully deleted all ${leads.length} leads!`)

      // Refresh leads
      fetchLeads(selectedCampaignId)
    } catch (error: any) {
      console.error('Delete all error:', error)
      toast.error(error.message || 'Failed to delete all leads')
    }
  }

  const handleEnrichLeads = async () => {
    if (!selectedCampaignId) {
      toast.error('Please select a campaign first')
      return
    }

    if (leads.length === 0) {
      toast.error('No leads to enrich')
      return
    }

    try {
      setEnrichingLeads(true)

      // Create AbortController for cancellation
      enrichAbortRef.current = new AbortController()

      const token = localStorage.getItem('access_token')

      if (!token) {
        toast.error('You must be logged in')
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/leads/enrich`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          signal: enrichAbortRef.current.signal
        }
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to enrich leads')
      }

      const data = await response.json()

      // Show detailed results
      const message = `Enriched ${data.enriched} of ${data.total_leads} leads!\n` +
        `Emails found: ${data.emails_found}\n` +
        `Phones found: ${data.phones_found}\n` +
        (data.skipped > 0 ? `Skipped: ${data.skipped} (no website)` : '')

      toast.success(message, { duration: 6000 })

      // Refresh leads to show updated data
      await fetchLeads(selectedCampaignId)

    } catch (error: any) {
      if (error.name === 'AbortError') {
        toast.info('Enrichment cancelled')
        return
      }
      console.error('Enrich leads error:', error)
      toast.error(error.message || 'Failed to enrich leads')
    } finally {
      setEnrichingLeads(false)
      enrichAbortRef.current = null
    }
  }

  const handleCancelEnrichment = () => {
    if (enrichAbortRef.current) {
      enrichAbortRef.current.abort()
      setEnrichingLeads(false)
    }
  }

  const handleGenerateDescription = async (leadId: string) => {
    // Find lead name for better UX
    const lead = leads.find(l => l.id === leadId)
    const leadName = lead?.title || 'Lead'

    try {
      setGeneratingDescriptionId(leadId)

      // Create AbortController for cancellation
      descriptionAbortRef.current = new AbortController()

      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/leads/${leadId}/generate-description`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        signal: descriptionAbortRef.current.signal
      })

      if (!response.ok) throw new Error('Failed to queue description generation')

      const result = await response.json()

      // Add to pending tasks for tracking
      addPendingTask(leadId, leadName, 'description')

      // Show success message that task is queued
      toast.success(
        `AI description queued for ${leadName}! Auto-refresh is enabled - you'll be notified when it's ready.`,
        { duration: 5000 }
      )

    } catch (error: any) {
      if (error.name === 'AbortError') {
        // Request was cancelled - don't show error
        return
      }
      console.error('Generate description error:', error)
      toast.error(error.message || 'Failed to queue description generation')
    } finally {
      setGeneratingDescriptionId(null)
      descriptionAbortRef.current = null
    }
  }

  const handleGenerateDeepResearch = async (leadId: string) => {
    // Find lead name for better UX
    const lead = leads.find(l => l.id === leadId)
    const leadName = lead?.title || 'Lead'

    try {
      setGeneratingDeepResearchId(leadId)

      // Create AbortController for cancellation
      deepResearchAbortRef.current = new AbortController()

      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/leads/${leadId}/generate-deep-research`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        signal: deepResearchAbortRef.current.signal
      })

      if (!response.ok) throw new Error('Failed to queue deep research generation')

      const result = await response.json()

      // Add to pending tasks for tracking
      addPendingTask(leadId, leadName, 'deep_research')

      // Show success message that task is queued
      toast.success(
        `Deep research queued for ${leadName}! This will take 15-30 minutes. Auto-refresh is enabled - you'll be notified when it's ready.`,
        { duration: 7000 }
      )

    } catch (error: any) {
      if (error.name === 'AbortError') {
        // Request was cancelled - don't show error
        return
      }
      console.error('Generate deep research error:', error)
      toast.error(error.message || 'Failed to queue deep research generation')
    } finally {
      setGeneratingDeepResearchId(null)
      deepResearchAbortRef.current = null
    }
  }

  const handleGenerateEmailClick = (lead: any) => {
    setCurrentLeadForEmail(lead)
    setShowEmailModal(true)
  }

  const handleGenerateEmail = async () => {
    if (!currentLeadForEmail) return

    if (!emailCompanyInfo.trim()) {
      toast.error('Please enter your company information')
      return
    }

    const leadId = currentLeadForEmail.id
    const leadName = currentLeadForEmail.title

    try {
      setGeneratingEmailId(leadId)

      // Create AbortController for cancellation
      emailAbortRef.current = new AbortController()

      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/leads/${leadId}/generate-email`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ company_info: emailCompanyInfo }),
        signal: emailAbortRef.current.signal
      })

      if (!response.ok) throw new Error('Failed to queue email generation')

      const result = await response.json()

      // Add to pending tasks for tracking
      addPendingTask(leadId, leadName, 'email')

      // Show success message that task is queued
      toast.success(
        `AI email queued for ${leadName}! Auto-refresh is enabled - you'll be notified when it's ready.`,
        { duration: 5000 }
      )

      // Close modal and reset
      setShowEmailModal(false)
      setEmailCompanyInfo('')
      setCurrentLeadForEmail(null)

    } catch (error: any) {
      if (error.name === 'AbortError') {
        // Request was cancelled - don't show error
        return
      }
      console.error('Generate email error:', error)
      toast.error(error.message || 'Failed to queue email generation')
    } finally {
      setGeneratingEmailId(null)
      emailAbortRef.current = null
    }
  }

  const handleGenerateWhatsappClick = (lead: any) => {
    setCurrentLeadForWhatsapp(lead)
    setShowWhatsappModal(true)
  }

  const handleGenerateWhatsapp = async () => {
    if (!currentLeadForWhatsapp) return

    if (!whatsappCompanyInfo.trim()) {
      toast.error('Please enter your company information')
      return
    }

    const leadId = currentLeadForWhatsapp.id
    const leadName = currentLeadForWhatsapp.title

    try {
      setGeneratingWhatsappId(leadId)

      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/leads/${leadId}/generate-whatsapp`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ company_info: whatsappCompanyInfo })
      })

      if (!response.ok) throw new Error('Failed to queue WhatsApp generation')

      const result = await response.json()

      // Add to pending tasks for tracking
      addPendingTask(leadId, leadName, 'whatsapp')

      // Show success message that task is queued
      toast.success(
        `AI WhatsApp message queued for ${leadName}! Auto-refresh is enabled - you'll be notified when it's ready.`,
        { duration: 5000 }
      )

      // Close modal and reset
      setShowWhatsappModal(false)
      setWhatsappCompanyInfo('')
      setCurrentLeadForWhatsapp(null)

    } catch (error: any) {
      console.error('Generate WhatsApp error:', error)
      toast.error(error.message || 'Failed to queue WhatsApp generation')
    } finally {
      setGeneratingWhatsappId(null)
    }
  }

  // ============================================================================
  // Bulk Automation Handlers
  // ============================================================================

  const handleSelectLead = (leadId: string) => {
    setSelectedLeads(prev =>
      prev.includes(leadId)
        ? prev.filter(id => id !== leadId)
        : [...prev, leadId]
    )
  }

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedLeads([])
    } else {
      setSelectedLeads(leads.map((lead: any) => lead.id))
    }
    setSelectAll(!selectAll)
  }

  const handleBulkGenerateDescriptions = async () => {
    if (selectedLeads.length === 0) {
      toast.error('Please select leads first')
      return
    }

    setBulkGeneratingDescriptions(true)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in')
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/bulk-generate-descriptions`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(selectedLeads)
        }
      )

      if (!response.ok) {
        throw new Error('Failed to generate descriptions')
      }

      const data = await response.json()
      toast.success(`Generated ${data.generated} descriptions!`, { duration: 5000 })

      // Refresh leads
      await fetchLeads(selectedCampaignId)

      // Clear selection
      setSelectedLeads([])
      setSelectAll(false)
    } catch (error) {
      console.error('Bulk generate descriptions error:', error)
      toast.error('Failed to generate descriptions')
    } finally {
      setBulkGeneratingDescriptions(false)
    }
  }

  const handleBulkGenerateEmails = async () => {
    if (selectedLeads.length === 0) {
      toast.error('Please select leads first')
      return
    }

    if (!bulkEmailCompanyInfo.trim()) {
      toast.error('Please enter your company information for email generation')
      return
    }

    // Create new AbortController
    abortControllerEmails.current = new AbortController()
    setBulkGeneratingEmails(true)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in')
        setBulkGeneratingEmails(false)
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/bulk-generate-emails`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lead_ids: selectedLeads,
            company_info: bulkEmailCompanyInfo
          }),
          signal: abortControllerEmails.current.signal
        }
      )

      if (!response.ok) {
        throw new Error('Failed to generate emails')
      }

      const data = await response.json()
      toast.success(`Generated ${data.generated} emails!`, { duration: 5000 })

      // Refresh leads
      await fetchLeads(selectedCampaignId)

      // Clear selection
      setSelectedLeads([])
      setSelectAll(false)
    } catch (error: any) {
      if (error.name === 'AbortError') {
        toast.error('Email generation cancelled')
      } else {
        console.error('Bulk generate emails error:', error)
        toast.error('Failed to generate emails')
      }
    } finally {
      setBulkGeneratingEmails(false)
      abortControllerEmails.current = null
    }
  }

  const cancelBulkGenerateEmails = () => {
    if (abortControllerEmails.current) {
      abortControllerEmails.current.abort()
      toast.info('Cancelling email generation...')
    }
  }

  const handleBulkGenerateWhatsApp = async () => {
    if (selectedLeads.length === 0) {
      toast.error('Please select leads first')
      return
    }

    if (!bulkWhatsAppCompanyInfo.trim()) {
      toast.error('Please enter your company information for WhatsApp generation')
      return
    }

    // Create new AbortController
    abortControllerWhatsApp.current = new AbortController()
    setBulkGeneratingWhatsApp(true)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in')
        setBulkGeneratingWhatsApp(false)
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/bulk-generate-whatsapp`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lead_ids: selectedLeads,
            company_info: bulkWhatsAppCompanyInfo
          }),
          signal: abortControllerWhatsApp.current.signal
        }
      )

      if (!response.ok) {
        throw new Error('Failed to generate WhatsApp messages')
      }

      const data = await response.json()
      toast.success(`Generated ${data.generated} WhatsApp messages!`, { duration: 5000 })

      // Refresh leads
      await fetchLeads(selectedCampaignId)

      // Clear selection
      setSelectedLeads([])
      setSelectAll(false)
    } catch (error: any) {
      if (error.name === 'AbortError') {
        toast.error('WhatsApp generation cancelled')
      } else {
        console.error('Bulk generate WhatsApp error:', error)
        toast.error('Failed to generate WhatsApp messages')
      }
    } finally {
      setBulkGeneratingWhatsApp(false)
      abortControllerWhatsApp.current = null
    }
  }

  const cancelBulkGenerateWhatsApp = () => {
    if (abortControllerWhatsApp.current) {
      abortControllerWhatsApp.current.abort()
      toast.info('Cancelling WhatsApp generation...')
    }
  }

  const handleSendEmails = async () => {
    if (selectedLeads.length === 0) {
      toast.error('Please select leads first')
      return
    }

    if (!senderEmail || !senderPassword) {
      toast.error('Please enter Gmail credentials')
      return
    }

    setSendingEmails(true)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in')
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/send-emails-to-leads`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lead_ids: selectedLeads,
            sender_email: senderEmail,
            sender_password: senderPassword,
            min_delay: 5,
            max_delay: 15
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to send emails')
      }

      const data = await response.json()
      toast.success(`Sent ${data.sent} emails successfully!`, { duration: 6000 })

      // Close dialog
      setShowSendEmailDialog(false)
      setSenderEmail('')
      setSenderPassword('')

      // Refresh leads
      await fetchLeads(selectedCampaignId)

      // Clear selection
      setSelectedLeads([])
      setSelectAll(false)
    } catch (error: any) {
      console.error('Send emails error:', error)
      toast.error(error.message || 'Failed to send emails')
    } finally {
      setSendingEmails(false)
    }
  }

  const handleSendWhatsApp = async () => {
    if (selectedLeads.length === 0) {
      toast.error('Please select leads first')
      return
    }

    if (!whatsappPhoneNumberId || !whatsappAccessToken) {
      toast.error('Please enter WhatsApp Business API credentials')
      return
    }

    setSendingWhatsApp(true)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('You must be logged in')
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/campaigns/${selectedCampaignId}/send-whatsapp`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lead_ids: selectedLeads,
            phone_number_id: whatsappPhoneNumberId,
            access_token: whatsappAccessToken,
            min_delay: 5,
            max_delay: 15
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to send WhatsApp messages')
      }

      const data = await response.json()
      toast.success(`Sent ${data.sent} WhatsApp messages successfully!`, { duration: 6000 })

      // Close dialog
      setShowSendWhatsAppDialog(false)
      setWhatsappPhoneNumberId('')
      setWhatsappAccessToken('')

      // Refresh leads
      await fetchLeads(selectedCampaignId)

      // Clear selection
      setSelectedLeads([])
      setSelectAll(false)
    } catch (error: any) {
      console.error('Send WhatsApp error:', error)
      toast.error(error.message || 'Failed to send WhatsApp messages')
    } finally {
      setSendingWhatsApp(false)
    }
  }

  const tableColumns = [
    {
      key: 'select',
      label: (
        <input
          type="checkbox"
          checked={selectAll}
          onChange={handleSelectAll}
          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
        />
      ),
      width: '3%',
      align: 'center' as const,
      render: (_val: any, lead: any) => (
        <input
          type="checkbox"
          checked={selectedLeads.includes(lead.id)}
          onChange={() => handleSelectLead(lead.id)}
          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
        />
      )
    },
    { key: 'title', label: 'Name', width: '22%' },
    { key: 'address', label: 'Address', width: '22%' },
    { key: 'phone', label: 'Phone', width: '13%' },
    { key: 'category', label: 'Category', width: '13%' },
    {
      key: 'website',
      label: 'Website',
      width: '10%',
      render: (val: string) => val ? (
        <a href={val} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
          Visit
        </a>
      ) : '-'
    },
    {
      key: 'description',
      label: 'AI Description',
      width: '30%',
      render: (val: string, lead: any) => {
        const isPending = pendingTasks.some(t => t.leadId === lead.id && t.type === 'description')
        const isGenerating = generatingDescriptionId === lead.id

        if (val) {
          return (
            <div className="text-sm text-gray-700 max-w-xs truncate" title={val}>
              {val}
            </div>
          )
        }

        if (isPending) {
          return (
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 rounded-md flex items-center gap-1.5">
                <Clock className="w-3 h-3 animate-pulse" />
                Processing...
              </span>
              <button
                onClick={() => handleCancelGeneration(lead.id, 'description')}
                className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                title="Cancel Generation"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )
        }

        return (
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleGenerateDescription(lead.id)}
              disabled={isGenerating}
              className="px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Queuing...
                </>
              ) : (
                <>
                  <Sparkles className="w-3 h-3" />
                  Generate
                </>
              )}
            </button>
            {isGenerating && (
              <button
                onClick={() => handleCancelGeneration(lead.id, 'description')}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="Cancel"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        )
      }
    },
    {
      key: 'deep_research',
      label: 'Deep Research',
      width: '30%',
      render: (val: string, lead: any) => {
        const isPending = pendingTasks.some(t => t.leadId === lead.id && t.type === 'deep_research')
        const isGenerating = generatingDeepResearchId === lead.id

        if (val) {
          return (
            <div className="text-sm text-gray-700 max-w-xs truncate" title={val}>
              {val}
            </div>
          )
        }

        if (isPending) {
          return (
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 rounded-md flex items-center gap-1.5">
                <Clock className="w-3 h-3 animate-pulse" />
                Processing (15-30 min)...
              </span>
              <button
                onClick={() => handleCancelGeneration(lead.id, 'deep_research')}
                className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                title="Cancel Generation"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )
        }

        return (
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleGenerateDeepResearch(lead.id)}
              disabled={isGenerating}
              className="px-3 py-1.5 text-xs font-medium text-orange-700 bg-orange-50 hover:bg-orange-100 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Queuing...
                </>
              ) : (
                <>
                  <Sparkles className="w-3 h-3" />
                  Research
                </>
              )}
            </button>
            {isGenerating && (
              <button
                onClick={() => handleCancelGeneration(lead.id, 'deep_research')}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="Cancel"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        )
      }
    },
    {
      key: 'generated_email',
      label: 'AI Email',
      width: '30%',
      render: (val: string, lead: any) => {
        const isPending = pendingTasks.some(t => t.leadId === lead.id && t.type === 'email')
        const isGenerating = generatingEmailId === lead.id

        if (val) {
          return (
            <div className="text-sm text-gray-700 max-w-xs truncate" title={val}>
              {val}
            </div>
          )
        }

        if (isPending) {
          return (
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 rounded-md flex items-center gap-1.5">
                <Clock className="w-3 h-3 animate-pulse" />
                Processing...
              </span>
              <button
                onClick={() => handleCancelGeneration(lead.id, 'email')}
                className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                title="Cancel Generation"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )
        }

        return (
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleGenerateEmailClick(lead)}
              disabled={isGenerating}
              className="px-3 py-1.5 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Queuing...
                </>
              ) : (
                <>
                  <Sparkles className="w-3 h-3" />
                  Generate
                </>
              )}
            </button>
            {isGenerating && (
              <button
                onClick={() => handleCancelGeneration(lead.id, 'email')}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="Cancel"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        )
      }
    },
    {
      key: 'generated_whatsapp',
      label: 'AI WhatsApp',
      width: '30%',
      render: (val: string, lead: any) => {
        const isPending = pendingTasks.some(t => t.leadId === lead.id && t.type === 'whatsapp')
        const isGenerating = generatingWhatsappId === lead.id

        if (val) {
          return (
            <div className="text-sm text-gray-700 max-w-xs truncate" title={val}>
              {val}
            </div>
          )
        }

        if (isPending) {
          return (
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 rounded-md flex items-center gap-1.5">
                <Clock className="w-3 h-3 animate-pulse" />
                Processing...
              </span>
              <button
                onClick={() => handleCancelGeneration(lead.id, 'whatsapp')}
                className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                title="Cancel Generation"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )
        }

        return (
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleGenerateWhatsappClick(lead)}
              disabled={isGenerating}
              className="px-3 py-1.5 text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Queuing...
                </>
              ) : (
                <>
                  <Sparkles className="w-3 h-3" />
                  Generate
                </>
              )}
            </button>
            {isGenerating && (
              <button
                onClick={() => handleCancelGeneration(lead.id, 'whatsapp')}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="Cancel"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        )
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      width: '10%',
      align: 'center' as const,
      render: (_val: any, lead: any) => (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => handleEditLead(lead)}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
            title="Edit lead"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleDeleteLead(lead.id)}
            className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
            title="Delete lead"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      )
    },
  ]

  return (
    <DashboardLayout>
      {/* Pending Tasks Banner */}
      {pendingTasks.length > 0 && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex gap-3">
              <Clock className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5 animate-pulse" />
              <div>
                <h3 className="text-sm font-semibold text-amber-900">
                  {pendingTasks.length} AI {pendingTasks.length === 1 ? 'task' : 'tasks'} processing
                </h3>
                <div className="mt-1 text-sm text-amber-800 space-y-1">
                  {pendingTasks.map(task => (
                    <div key={`${task.leadId}-${task.type}`} className="flex items-center gap-2">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>
                        {task.type === 'description' ? 'Description' : 'Email'} for <strong>{task.leadName}</strong>
                      </span>
                      <span className="text-amber-600 text-xs">
                        ({Math.floor((Date.now() - task.startTime) / 60000)}m ago)
                      </span>
                      <button
                        onClick={() => removePendingTask(task.leadId)}
                        className="text-amber-600 hover:text-red-600 transition-colors"
                        title="Dismiss"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
                <p className="mt-2 text-xs text-amber-700">
                  Auto-refresh is active. Results will appear automatically when ready.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => selectedCampaignId && fetchLeads(selectedCampaignId)}
                className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-md transition-colors flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                Refresh Now
              </button>
              <button
                onClick={() => {
                  setPendingTasks([])
                  setAutoRefreshEnabled(false)
                }}
                className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-white border border-amber-300 hover:bg-amber-50 rounded-md transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Page Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Lead Generation</h1>
            <p className="mt-2 text-gray-600">
              Generate leads from multiple sources using AI-powered scraping
            </p>
          </div>
          <div className="sm:w-64">
            {campaignsLoading ? (
              <div className="h-10 bg-gray-200 animate-pulse rounded-lg"></div>
            ) : campaigns.length === 0 ? (
              <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                <span className="text-sm text-yellow-800">No campaigns found</span>
              </div>
            ) : (
              <Select
                label="Campaign"
                value={selectedCampaignId}
                onChange={(e) => setSelectedCampaignId(e.target.value)}
                fullWidth
              >
                {campaigns.map((campaign) => (
                  <option key={campaign.id} value={campaign.id}>
                    {campaign.name}
                  </option>
                ))}
              </Select>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Card>
        <CardContent>
          <Tabs defaultValue="google-maps" onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger
                value="google-maps"
                icon={<MapPin className="h-4 w-4" />}
              >
                Google Maps
              </TabsTrigger>
              <TabsTrigger
                value="linkedin"
                icon={<Linkedin className="h-4 w-4" />}
              >
                LinkedIn
              </TabsTrigger>
              <TabsTrigger
                value="instagram"
                icon={<Instagram className="h-4 w-4" />}
              >
                Instagram
              </TabsTrigger>
              <TabsTrigger
                value="upload"
                icon={<FileUp className="h-4 w-4" />}
              >
                Upload File
              </TabsTrigger>
            </TabsList>

            {/* Google Maps Tab */}
            <TabsContent value="google-maps">
              <div className="space-y-6">
                {/* Search Form */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Input
                    label="Search Query"
                    placeholder="e.g., restaurants in San Francisco"
                    value={googleQuery}
                    onChange={(e) => setGoogleQuery(e.target.value)}
                    leftIcon={<Search className="h-4 w-4" />}
                    fullWidth
                  />
                  <Input
                    label="Location (Optional)"
                    placeholder="e.g., San Francisco, CA"
                    value={googleLocation}
                    onChange={(e) => setGoogleLocation(e.target.value)}
                    leftIcon={<MapPin className="h-4 w-4" />}
                    fullWidth
                  />
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Max Results
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="500"
                      value={googleMaxResults}
                      onChange={(e) => {
                        const value = Number(e.target.value)
                        if (value > 500) {
                          setGoogleMaxResults(500)
                          toast.error('Maximum 500 results allowed for Google Maps')
                        } else if (value < 1) {
                          setGoogleMaxResults(1)
                          toast.error('Minimum 1 result required')
                        } else {
                          setGoogleMaxResults(value)
                        }
                      }}
                      onBlur={(e) => {
                        const value = Number(e.target.value)
                        if (!value || value < 1) setGoogleMaxResults(50)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <div className="mt-1 space-y-1">
                      <p className="text-xs text-gray-500">Maximum: 500 results for Google Maps</p>
                      {googleMaxResults >= 100 && (
                        <div className="flex items-start gap-1 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                          <span>⚠</span>
                          <span>Scraping {googleMaxResults} results may take {Math.ceil(googleMaxResults / 10)}-{Math.ceil(googleMaxResults / 5)} minutes</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-3">
                  <Button
                    variant="primary"
                    leftIcon={generatingGoogleLeads ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                    onClick={handleGoogleSearch}
                    disabled={!selectedCampaignId || generatingGoogleLeads}
                  >
                    {generatingGoogleLeads ? 'Generating...' : 'Generate Leads'}
                  </Button>
                  <Button
                    variant="outline"
                    leftIcon={<Filter className="h-4 w-4" />}
                    disabled={!selectedCampaignId || generatingGoogleLeads}
                  >
                    Advanced Filters
                  </Button>
                </div>

                {/* Processing Overlay */}
                {generatingGoogleLeads && (
                  <div className="mt-6 p-6 bg-primary-50 border border-primary-200 rounded-lg">
                    <div className="flex flex-col items-center justify-center space-y-4">
                      <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
                      <div className="text-center">
                        <p className="text-lg font-semibold text-primary-900">{generationStatus}</p>
                        <p className="text-sm text-primary-700 mt-1">
                          Searching for up to {googleMaxResults} businesses. This may take a moment...
                        </p>
                      </div>
                      <div className="w-full max-w-md bg-primary-200 rounded-full h-2 overflow-hidden">
                        <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        leftIcon={<X className="h-4 w-4" />}
                        onClick={handleCancelLeadGeneration}
                        className="text-red-600 hover:bg-red-50 border-red-300"
                      >
                        Stop Generation
                      </Button>
                    </div>
                  </div>
                )}

                {/* Results */}
                {leadsLoading ? (
                  <SkeletonTable rows={5} />
                ) : leads.length > 0 && activeTab === 'google-maps' ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="primary">{leads.length} leads</Badge>
                        <span className="text-sm text-gray-600">in this campaign</span>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<RefreshCw className="h-4 w-4" />}
                          onClick={() => selectedCampaignId && fetchLeads(selectedCampaignId)}
                          disabled={leadsLoading}
                        >
                          Refresh
                        </Button>
                        {enrichingLeads ? (
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              leftIcon={<Loader2 className="h-4 w-4 animate-spin" />}
                              disabled={true}
                              className="text-green-600 border-green-300"
                            >
                              Enriching...
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              leftIcon={<X className="h-4 w-4" />}
                              onClick={handleCancelEnrichment}
                              className="text-red-600 hover:bg-red-50 border-red-300"
                            >
                              Stop
                            </Button>
                          </div>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            leftIcon={<Globe className="h-4 w-4" />}
                            onClick={handleEnrichLeads}
                            disabled={leads.length === 0}
                            className="text-green-600 hover:bg-green-50 border-green-300"
                          >
                            Enrich from Websites
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Download className="h-4 w-4" />}
                          onClick={handleExport}
                        >
                          Export
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Trash2 className="h-4 w-4" />}
                          onClick={handleDeleteAllLeads}
                          disabled={leads.length === 0}
                          className="text-red-600 hover:bg-red-50 border-red-300"
                        >
                          Delete All
                        </Button>
                      </div>
                    </div>

                    {/* Bulk Actions Toolbar */}
                    {selectedLeads.length > 0 && (
                      <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center justify-between flex-wrap gap-3">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-blue-900">
                              {selectedLeads.length} lead{selectedLeads.length > 1 ? 's' : ''} selected
                            </span>
                            <button
                              onClick={() => {
                                setSelectedLeads([])
                                setSelectAll(false)
                              }}
                              className="text-xs text-blue-700 hover:text-blue-900 underline"
                            >
                              Clear selection
                            </button>
                          </div>

                          <div className="flex items-center gap-2 flex-wrap">
                            <Button
                              size="sm"
                              variant="outline"
                              leftIcon={<Sparkles className="h-4 w-4" />}
                              onClick={handleBulkGenerateDescriptions}
                              disabled={bulkGeneratingDescriptions}
                              className="bg-white hover:bg-blue-50 border-blue-300"
                            >
                              {bulkGeneratingDescriptions ? 'Generating...' : 'Generate Descriptions'}
                            </Button>

                            {bulkGeneratingEmails ? (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<X className="h-4 w-4" />}
                                onClick={cancelBulkGenerateEmails}
                                className="bg-red-50 hover:bg-red-100 border-red-300 text-red-700"
                              >
                                Cancel Email Generation
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<Mail className="h-4 w-4" />}
                                onClick={handleBulkGenerateEmails}
                                disabled={!bulkEmailCompanyInfo.trim()}
                                className="bg-white hover:bg-purple-50 border-purple-300"
                                title={!bulkEmailCompanyInfo.trim() ? 'Enter company info first' : ''}
                              >
                                Generate Emails
                              </Button>
                            )}

                            {bulkGeneratingWhatsApp ? (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<X className="h-4 w-4" />}
                                onClick={cancelBulkGenerateWhatsApp}
                                className="bg-red-50 hover:bg-red-100 border-red-300 text-red-700"
                              >
                                Cancel WhatsApp Generation
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<MessageCircle className="h-4 w-4" />}
                                onClick={handleBulkGenerateWhatsApp}
                                disabled={!bulkWhatsAppCompanyInfo.trim()}
                                className="bg-white hover:bg-green-50 border-green-300"
                                title={!bulkWhatsAppCompanyInfo.trim() ? 'Enter company info first' : ''}
                              >
                                Generate WhatsApp
                              </Button>
                            )}

                            <Button
                              size="sm"
                              leftIcon={<Send className="h-4 w-4" />}
                              onClick={() => setShowSendEmailDialog(true)}
                              className="bg-green-600 hover:bg-green-700 text-white"
                            >
                              Send Emails
                            </Button>

                            <Button
                              size="sm"
                              leftIcon={<Send className="h-4 w-4" />}
                              onClick={() => setShowSendWhatsAppDialog(true)}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white"
                            >
                              Send WhatsApp
                            </Button>
                          </div>
                        </div>

                        {/* Company Info Input for Email Generation */}
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <label className="block text-sm font-medium text-blue-900 mb-2">
                            Company Information (for email generation)
                          </label>
                          <textarea
                            value={bulkEmailCompanyInfo}
                            onChange={(e) => setBulkEmailCompanyInfo(e.target.value)}
                            placeholder="Enter information about your company to help AI generate personalized cold emails..."
                            className="w-full px-3 py-2 text-sm border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            rows={2}
                          />
                        </div>

                        {/* Company Info Input for WhatsApp Generation */}
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <label className="block text-sm font-medium text-blue-900 mb-2">
                            Company Information (for WhatsApp generation)
                          </label>
                          <textarea
                            value={bulkWhatsAppCompanyInfo}
                            onChange={(e) => setBulkWhatsAppCompanyInfo(e.target.value)}
                            placeholder="Enter information about your company to help AI generate personalized WhatsApp messages..."
                            className="w-full px-3 py-2 text-sm border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            rows={2}
                          />
                        </div>
                      </div>
                    )}

                    <Table columns={tableColumns} data={leads} />
                  </div>
                ) : (
                  <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                    <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      No leads generated yet
                    </h3>
                    <p className="text-gray-600">
                      Enter a search query and click "Generate Leads" to start
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* LinkedIn Tab */}
            <TabsContent value="linkedin">
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Company Search"
                    placeholder="e.g., SaaS companies in San Francisco"
                    value={linkedinQuery}
                    onChange={(e) => setLinkedinQuery(e.target.value)}
                    leftIcon={<Search className="h-4 w-4" />}
                    fullWidth
                  />
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Max Results
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="200"
                      value={linkedinMaxResults}
                      onChange={(e) => {
                        const value = Number(e.target.value)
                        if (value > 200) {
                          setLinkedinMaxResults(200)
                          toast.error('Maximum 200 results allowed for LinkedIn')
                        } else if (value < 1) {
                          setLinkedinMaxResults(1)
                          toast.error('Minimum 1 result required')
                        } else {
                          setLinkedinMaxResults(value)
                        }
                      }}
                      onBlur={(e) => {
                        const value = Number(e.target.value)
                        if (!value || value < 1) setLinkedinMaxResults(25)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <div className="mt-1 space-y-1">
                      <p className="text-xs text-gray-500">Maximum: 200 results for LinkedIn</p>
                      {linkedinMaxResults >= 100 && (
                        <div className="flex items-start gap-1 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                          <span>⚠</span>
                          <span>Scraping {linkedinMaxResults} results may take {Math.ceil(linkedinMaxResults / 8)}-{Math.ceil(linkedinMaxResults / 4)} minutes</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    variant="primary"
                    leftIcon={generatingLinkedinLeads ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                    onClick={handleLinkedinSearch}
                    disabled={!selectedCampaignId || generatingLinkedinLeads}
                  >
                    {generatingLinkedinLeads ? 'Generating...' : 'Generate Leads'}
                  </Button>
                </div>

                {/* Processing Overlay */}
                {generatingLinkedinLeads && (
                  <div className="mt-6 p-6 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex flex-col items-center justify-center space-y-4">
                      <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
                      <div className="text-center">
                        <p className="text-lg font-semibold text-blue-900">{generationStatus}</p>
                        <p className="text-sm text-blue-700 mt-1">
                          Searching for up to {linkedinMaxResults} companies. This may take a moment...
                        </p>
                      </div>
                      <div className="w-full max-w-md bg-blue-200 rounded-full h-2 overflow-hidden">
                        <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        leftIcon={<X className="h-4 w-4" />}
                        onClick={handleCancelLeadGeneration}
                        className="text-red-600 hover:bg-red-50 border-red-300"
                      >
                        Stop Generation
                      </Button>
                    </div>
                  </div>
                )}

                {leadsLoading ? (
                  <SkeletonTable rows={5} />
                ) : leads.length > 0 && activeTab === 'linkedin' ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="primary">{leads.length} leads</Badge>
                        <span className="text-sm text-gray-600">in this campaign</span>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<RefreshCw className="h-4 w-4" />}
                          onClick={() => selectedCampaignId && fetchLeads(selectedCampaignId)}
                          disabled={leadsLoading}
                        >
                          Refresh
                        </Button>
                        {enrichingLeads ? (
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              leftIcon={<Loader2 className="h-4 w-4 animate-spin" />}
                              disabled={true}
                              className="text-green-600 border-green-300"
                            >
                              Enriching...
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              leftIcon={<X className="h-4 w-4" />}
                              onClick={handleCancelEnrichment}
                              className="text-red-600 hover:bg-red-50 border-red-300"
                            >
                              Stop
                            </Button>
                          </div>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            leftIcon={<Globe className="h-4 w-4" />}
                            onClick={handleEnrichLeads}
                            disabled={leads.length === 0}
                            className="text-green-600 hover:bg-green-50 border-green-300"
                          >
                            Enrich from Websites
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Download className="h-4 w-4" />}
                          onClick={handleExport}
                        >
                          Export
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Trash2 className="h-4 w-4" />}
                          onClick={handleDeleteAllLeads}
                          disabled={leads.length === 0}
                          className="text-red-600 hover:bg-red-50 border-red-300"
                        >
                          Delete All
                        </Button>
                      </div>
                    </div>

                    {/* Bulk Actions Toolbar */}
                    {selectedLeads.length > 0 && (
                      <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center justify-between flex-wrap gap-3">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-blue-900">
                              {selectedLeads.length} lead{selectedLeads.length > 1 ? 's' : ''} selected
                            </span>
                            <button
                              onClick={() => {
                                setSelectedLeads([])
                                setSelectAll(false)
                              }}
                              className="text-xs text-blue-700 hover:text-blue-900 underline"
                            >
                              Clear selection
                            </button>
                          </div>

                          <div className="flex items-center gap-2 flex-wrap">
                            <Button
                              size="sm"
                              variant="outline"
                              leftIcon={<Sparkles className="h-4 w-4" />}
                              onClick={handleBulkGenerateDescriptions}
                              disabled={bulkGeneratingDescriptions}
                              className="bg-white hover:bg-blue-50 border-blue-300"
                            >
                              {bulkGeneratingDescriptions ? 'Generating...' : 'Generate Descriptions'}
                            </Button>

                            {bulkGeneratingEmails ? (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<X className="h-4 w-4" />}
                                onClick={cancelBulkGenerateEmails}
                                className="bg-red-50 hover:bg-red-100 border-red-300 text-red-700"
                              >
                                Cancel Email Generation
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<Mail className="h-4 w-4" />}
                                onClick={handleBulkGenerateEmails}
                                disabled={!bulkEmailCompanyInfo.trim()}
                                className="bg-white hover:bg-purple-50 border-purple-300"
                                title={!bulkEmailCompanyInfo.trim() ? 'Enter company info first' : ''}
                              >
                                Generate Emails
                              </Button>
                            )}

                            {bulkGeneratingWhatsApp ? (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<X className="h-4 w-4" />}
                                onClick={cancelBulkGenerateWhatsApp}
                                className="bg-red-50 hover:bg-red-100 border-red-300 text-red-700"
                              >
                                Cancel WhatsApp Generation
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<MessageCircle className="h-4 w-4" />}
                                onClick={handleBulkGenerateWhatsApp}
                                disabled={!bulkWhatsAppCompanyInfo.trim()}
                                className="bg-white hover:bg-green-50 border-green-300"
                                title={!bulkWhatsAppCompanyInfo.trim() ? 'Enter company info first' : ''}
                              >
                                Generate WhatsApp
                              </Button>
                            )}

                            <Button
                              size="sm"
                              leftIcon={<Send className="h-4 w-4" />}
                              onClick={() => setShowSendEmailDialog(true)}
                              className="bg-green-600 hover:bg-green-700 text-white"
                            >
                              Send Emails
                            </Button>

                            <Button
                              size="sm"
                              leftIcon={<Send className="h-4 w-4" />}
                              onClick={() => setShowSendWhatsAppDialog(true)}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white"
                            >
                              Send WhatsApp
                            </Button>
                          </div>
                        </div>

                        {/* Company Info Input for Email Generation */}
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <label className="block text-sm font-medium text-blue-900 mb-2">
                            Company Information (for email generation)
                          </label>
                          <textarea
                            value={bulkEmailCompanyInfo}
                            onChange={(e) => setBulkEmailCompanyInfo(e.target.value)}
                            placeholder="Enter information about your company to help AI generate personalized cold emails..."
                            className="w-full px-3 py-2 text-sm border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            rows={2}
                          />
                        </div>

                        {/* Company Info Input for WhatsApp Generation */}
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <label className="block text-sm font-medium text-blue-900 mb-2">
                            Company Information (for WhatsApp generation)
                          </label>
                          <textarea
                            value={bulkWhatsAppCompanyInfo}
                            onChange={(e) => setBulkWhatsAppCompanyInfo(e.target.value)}
                            placeholder="Enter information about your company to help AI generate personalized WhatsApp messages..."
                            className="w-full px-3 py-2 text-sm border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            rows={2}
                          />
                        </div>
                      </div>
                    )}

                    <Table columns={tableColumns} data={leads} />
                  </div>
                ) : (
                  <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                    <Linkedin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      No companies found yet
                    </h3>
                    <p className="text-gray-600">
                      Enter a search query to find companies on LinkedIn
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Instagram Tab */}
            <TabsContent value="instagram">
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Search Accounts"
                    placeholder="e.g., #fashion influencers"
                    value={instagramQuery}
                    onChange={(e) => setInstagramQuery(e.target.value)}
                    leftIcon={<Search className="h-4 w-4" />}
                    fullWidth
                  />
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Max Results
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="300"
                      value={instagramMaxResults}
                      onChange={(e) => {
                        const value = Number(e.target.value)
                        if (value > 300) {
                          setInstagramMaxResults(300)
                          toast.error('Maximum 300 results allowed for Instagram')
                        } else if (value < 1) {
                          setInstagramMaxResults(1)
                          toast.error('Minimum 1 result required')
                        } else {
                          setInstagramMaxResults(value)
                        }
                      }}
                      onBlur={(e) => {
                        const value = Number(e.target.value)
                        if (!value || value < 1) setInstagramMaxResults(30)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <div className="mt-1 space-y-1">
                      <p className="text-xs text-gray-500">Maximum: 300 results for Instagram</p>
                      {instagramMaxResults >= 100 && (
                        <div className="flex items-start gap-1 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                          <span>⚠</span>
                          <span>Scraping {instagramMaxResults} results may take {Math.ceil(instagramMaxResults / 10)}-{Math.ceil(instagramMaxResults / 6)} minutes</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    variant="primary"
                    leftIcon={generatingInstagramLeads ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                    onClick={handleInstagramSearch}
                    disabled={!selectedCampaignId || generatingInstagramLeads}
                  >
                    {generatingInstagramLeads ? 'Generating...' : 'Generate Leads'}
                  </Button>
                </div>

                {/* Processing Overlay */}
                {generatingInstagramLeads && (
                  <div className="mt-6 p-6 bg-pink-50 border border-pink-200 rounded-lg">
                    <div className="flex flex-col items-center justify-center space-y-4">
                      <Loader2 className="w-12 h-12 text-pink-600 animate-spin" />
                      <div className="text-center">
                        <p className="text-lg font-semibold text-pink-900">{generationStatus}</p>
                        <p className="text-sm text-pink-700 mt-1">
                          Searching for up to {instagramMaxResults} accounts. This may take a moment...
                        </p>
                      </div>
                      <div className="w-full max-w-md bg-pink-200 rounded-full h-2 overflow-hidden">
                        <div className="bg-pink-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        leftIcon={<X className="h-4 w-4" />}
                        onClick={handleCancelLeadGeneration}
                        className="text-red-600 hover:bg-red-50 border-red-300"
                      >
                        Stop Generation
                      </Button>
                    </div>
                  </div>
                )}

                {leadsLoading ? (
                  <SkeletonTable rows={5} />
                ) : leads.length > 0 && activeTab === 'instagram' ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="primary">{leads.length} leads</Badge>
                        <span className="text-sm text-gray-600">in this campaign</span>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<RefreshCw className="h-4 w-4" />}
                          onClick={() => selectedCampaignId && fetchLeads(selectedCampaignId)}
                          disabled={leadsLoading}
                        >
                          Refresh
                        </Button>
                        {enrichingLeads ? (
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              leftIcon={<Loader2 className="h-4 w-4 animate-spin" />}
                              disabled={true}
                              className="text-green-600 border-green-300"
                            >
                              Enriching...
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              leftIcon={<X className="h-4 w-4" />}
                              onClick={handleCancelEnrichment}
                              className="text-red-600 hover:bg-red-50 border-red-300"
                            >
                              Stop
                            </Button>
                          </div>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            leftIcon={<Globe className="h-4 w-4" />}
                            onClick={handleEnrichLeads}
                            disabled={leads.length === 0}
                            className="text-green-600 hover:bg-green-50 border-green-300"
                          >
                            Enrich from Websites
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Download className="h-4 w-4" />}
                          onClick={handleExport}
                        >
                          Export
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Trash2 className="h-4 w-4" />}
                          onClick={handleDeleteAllLeads}
                          disabled={leads.length === 0}
                          className="text-red-600 hover:bg-red-50 border-red-300"
                        >
                          Delete All
                        </Button>
                      </div>
                    </div>

                    {/* Bulk Actions Toolbar */}
                    {selectedLeads.length > 0 && (
                      <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center justify-between flex-wrap gap-3">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-blue-900">
                              {selectedLeads.length} lead{selectedLeads.length > 1 ? 's' : ''} selected
                            </span>
                            <button
                              onClick={() => {
                                setSelectedLeads([])
                                setSelectAll(false)
                              }}
                              className="text-xs text-blue-700 hover:text-blue-900 underline"
                            >
                              Clear selection
                            </button>
                          </div>

                          <div className="flex items-center gap-2 flex-wrap">
                            <Button
                              size="sm"
                              variant="outline"
                              leftIcon={<Sparkles className="h-4 w-4" />}
                              onClick={handleBulkGenerateDescriptions}
                              disabled={bulkGeneratingDescriptions}
                              className="bg-white hover:bg-blue-50 border-blue-300"
                            >
                              {bulkGeneratingDescriptions ? 'Generating...' : 'Generate Descriptions'}
                            </Button>

                            {bulkGeneratingEmails ? (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<X className="h-4 w-4" />}
                                onClick={cancelBulkGenerateEmails}
                                className="bg-red-50 hover:bg-red-100 border-red-300 text-red-700"
                              >
                                Cancel Email Generation
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<Mail className="h-4 w-4" />}
                                onClick={handleBulkGenerateEmails}
                                disabled={!bulkEmailCompanyInfo.trim()}
                                className="bg-white hover:bg-purple-50 border-purple-300"
                                title={!bulkEmailCompanyInfo.trim() ? 'Enter company info first' : ''}
                              >
                                Generate Emails
                              </Button>
                            )}

                            {bulkGeneratingWhatsApp ? (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<X className="h-4 w-4" />}
                                onClick={cancelBulkGenerateWhatsApp}
                                className="bg-red-50 hover:bg-red-100 border-red-300 text-red-700"
                              >
                                Cancel WhatsApp Generation
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                leftIcon={<MessageCircle className="h-4 w-4" />}
                                onClick={handleBulkGenerateWhatsApp}
                                disabled={!bulkWhatsAppCompanyInfo.trim()}
                                className="bg-white hover:bg-green-50 border-green-300"
                                title={!bulkWhatsAppCompanyInfo.trim() ? 'Enter company info first' : ''}
                              >
                                Generate WhatsApp
                              </Button>
                            )}

                            <Button
                              size="sm"
                              leftIcon={<Send className="h-4 w-4" />}
                              onClick={() => setShowSendEmailDialog(true)}
                              className="bg-green-600 hover:bg-green-700 text-white"
                            >
                              Send Emails
                            </Button>

                            <Button
                              size="sm"
                              leftIcon={<Send className="h-4 w-4" />}
                              onClick={() => setShowSendWhatsAppDialog(true)}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white"
                            >
                              Send WhatsApp
                            </Button>
                          </div>
                        </div>

                        {/* Company Info Input for Email Generation */}
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <label className="block text-sm font-medium text-blue-900 mb-2">
                            Company Information (for email generation)
                          </label>
                          <textarea
                            value={bulkEmailCompanyInfo}
                            onChange={(e) => setBulkEmailCompanyInfo(e.target.value)}
                            placeholder="Enter information about your company to help AI generate personalized cold emails..."
                            className="w-full px-3 py-2 text-sm border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            rows={2}
                          />
                        </div>

                        {/* Company Info Input for WhatsApp Generation */}
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <label className="block text-sm font-medium text-blue-900 mb-2">
                            Company Information (for WhatsApp generation)
                          </label>
                          <textarea
                            value={bulkWhatsAppCompanyInfo}
                            onChange={(e) => setBulkWhatsAppCompanyInfo(e.target.value)}
                            placeholder="Enter information about your company to help AI generate personalized WhatsApp messages..."
                            className="w-full px-3 py-2 text-sm border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            rows={2}
                          />
                        </div>
                      </div>
                    )}

                    <Table columns={tableColumns} data={leads} />
                  </div>
                ) : (
                  <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                    <Instagram className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      No accounts found yet
                    </h3>
                    <p className="text-gray-600">
                      Enter hashtags or usernames to find Instagram accounts
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Upload File Tab */}
            <TabsContent value="upload">
              <div className="space-y-6">
                {/* Info Card */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex gap-3">
                    <Sparkles className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-900">
                      <p className="font-semibold mb-1">Upload Your Own Lead List</p>
                      <p className="text-blue-800">
                        Import leads from CSV or Excel files, then optionally enrich them with AI-generated descriptions
                        and personalized emails. Perfect for existing lead lists or CRM exports!
                      </p>
                    </div>
                  </div>
                </div>

                {/* File Upload */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Select File</h3>
                    <FileUpload
                      onFileSelect={(file) => setUploadedFile(file)}
                      accept=".csv,.xlsx,.xls"
                      maxSizeMB={10}
                    />
                  </div>

                  {/* File Format Info */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Required Column Format</h4>
                    <div className="text-sm text-gray-700 space-y-1">
                      <p><span className="font-medium">Required:</span> Name/Title/Company (business name)</p>
                      <p><span className="font-medium">Optional:</span> Email, Phone, Address/Location, Website/URL</p>
                      <p className="text-xs text-gray-600 mt-2">
                        Column names are flexible - we automatically detect variations like "company_name", "business", etc.
                      </p>
                    </div>
                  </div>
                </div>

                {/* AI Enrichment Options */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">AI Enrichment Options</h3>

                  {/* Generate Descriptions */}
                  <div className="flex items-start gap-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                    <input
                      type="checkbox"
                      id="upload-generate-descriptions"
                      className="mt-1"
                      checked={generateDescriptions}
                      onChange={(e) => setGenerateDescriptions(e.target.checked)}
                    />
                    <div className="flex-1">
                      <label htmlFor="upload-generate-descriptions" className="font-medium text-gray-900 cursor-pointer">
                        Generate AI Business Descriptions
                      </label>
                      <p className="text-sm text-gray-600">
                        Create professional descriptions for each business using AI
                      </p>
                    </div>
                  </div>

                  {/* Generate Emails */}
                  <div className="flex items-start gap-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                    <input
                      type="checkbox"
                      id="upload-generate-emails"
                      className="mt-1"
                      checked={generateEmails}
                      onChange={(e) => setGenerateEmails(e.target.checked)}
                    />
                    <div className="flex-1">
                      <label htmlFor="upload-generate-emails" className="font-medium text-gray-900 cursor-pointer">
                        Generate Personalized AI Emails
                      </label>
                      <p className="text-sm text-gray-600">
                        AI creates completely unique outreach emails for each lead
                      </p>
                    </div>
                  </div>

                  {/* Company Info for Email Generation */}
                  {generateEmails && (
                    <div className="ml-8 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Your Company Information * (Required for AI Emails)
                      </label>
                      <textarea
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        rows={5}
                        placeholder="Example: We are Elite Creatif, a digital marketing agency based in Dubai. We specialize in SEO, social media management, and targeted advertising for restaurants and retail businesses. Our services help businesses increase online visibility, attract more customers, and boost revenue through strategic digital campaigns."
                        value={companyInfo}
                        onChange={(e) => setCompanyInfo(e.target.value)}
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        AI uses this to introduce your company and explain your services to each lead
                      </p>
                    </div>
                  )}
                </div>

                {/* Upload Button */}
                <div className="flex justify-end pt-4 border-t">
                  <Button
                    onClick={handleFileUpload}
                    disabled={uploading || !uploadedFile || !selectedCampaignId}
                    size="lg"
                    leftIcon={uploading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Upload className="h-5 w-5" />}
                  >
                    {uploading ? 'Uploading & Processing...' : 'Upload & Process Leads'}
                  </Button>
                </div>

                {/* Sample CSV Download */}
                <div className="bg-gray-50 rounded-lg p-4 border-t">
                  <p className="text-sm text-gray-700">
                    <span className="font-medium">Need a sample file?</span> Download our{' '}
                    <button
                      onClick={() => {
                        const sampleCSV = 'Name,Email,Phone,Address,Website\nAcme Corp,contact@acme.com,+1234567890,"123 Main St, New York",https://acme.com\nTech Solutions,info@techsolutions.com,+0987654321,"456 Tech Ave, San Francisco",https://techsolutions.com'
                        const blob = new Blob([sampleCSV], { type: 'text/csv' })
                        const url = URL.createObjectURL(blob)
                        const link = document.createElement('a')
                        link.href = url
                        link.download = 'sample_leads_template.csv'
                        link.click()
                        URL.revokeObjectURL(url)
                      }}
                      className="text-blue-600 hover:text-blue-700 underline"
                    >
                      sample CSV template
                    </button>
                  </p>
                </div>

                {/* Uploaded Leads Display */}
                {leads.length > 0 && (
                  <div className="space-y-4 pt-6 border-t">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold text-gray-900">Campaign Leads</h3>
                        <Badge variant="primary">{leads.length} leads</Badge>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<RefreshCw className="h-4 w-4" />}
                          onClick={() => selectedCampaignId && fetchLeads(selectedCampaignId)}
                          disabled={leadsLoading}
                        >
                          Refresh
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Download className="h-4 w-4" />}
                          onClick={handleExport}
                        >
                          Export
                        </Button>
                      </div>
                    </div>

                    {leadsLoading ? (
                      <SkeletonTable rows={5} columns={5} />
                    ) : (
                      <Table
                        columns={tableColumns}
                        data={leads.map(lead => ({
                          ...lead,
                          category: lead.scraped_data?.category || 'N/A',
                          source: (
                            <Badge variant={lead.contact_source === 'google_maps' ? 'success' : 'secondary'}>
                              {lead.contact_source?.replace('_', ' ') || 'file_upload'}
                            </Badge>
                          )
                        }))}
                      />
                    )}
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Edit Lead Modal */}
      {showEditModal && editingLead && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Edit Lead</h2>
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setEditingLead(null)
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="px-6 py-4 space-y-4">
              {/* Company Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Company Name *
                </label>
                <input
                  type="text"
                  value={editingLead.title || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Enter company name"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  value={editingLead.email || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="contact@company.com"
                />
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Phone
                </label>
                <input
                  type="tel"
                  value={editingLead.phone || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              {/* Address */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Address
                </label>
                <input
                  type="text"
                  value={editingLead.address || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, address: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="123 Main St, City, Country"
                />
              </div>

              {/* Website */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Website
                </label>
                <input
                  type="url"
                  value={editingLead.website || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, website: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="https://www.company.com"
                />
              </div>

              {/* AI Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  AI Description
                </label>
                <textarea
                  value={editingLead.description || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, description: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                  placeholder="AI-generated business description..."
                />
              </div>

              {/* Deep Research */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Deep Research
                </label>
                <textarea
                  value={editingLead.deep_research || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, deep_research: e.target.value })}
                  rows={8}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
                  placeholder="AI-generated deep business research..."
                />
              </div>

              {/* Generated Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Generated Email
                </label>
                <textarea
                  value={editingLead.generated_email || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, generated_email: e.target.value })}
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                  placeholder="AI-generated email content..."
                />
              </div>

              {/* Generated WhatsApp */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  AI WhatsApp Message
                </label>
                <textarea
                  value={editingLead.generated_whatsapp || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, generated_whatsapp: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                  placeholder="AI-generated WhatsApp message..."
                />
              </div>
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setEditingLead(null)
                }}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveLead}
                className="px-4 py-2 text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors font-medium"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Email Modal */}
      {showEmailModal && currentLeadForEmail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-lg">
              <h2 className="text-xl font-semibold text-gray-900">Generate AI Email for {currentLeadForEmail.title}</h2>
              <button
                onClick={() => {
                  setShowEmailModal(false)
                  setEmailCompanyInfo('')
                  setCurrentLeadForEmail(null)
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="px-6 py-4 space-y-4">
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex gap-3">
                  <Sparkles className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-purple-900">
                    <p className="font-semibold mb-1">AI Email Generation</p>
                    <p className="text-purple-800">
                      Our AI will create a personalized outreach email for <strong>{currentLeadForEmail.title}</strong> based on your company information.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Company Information *
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                  rows={6}
                  placeholder="Example: We are Elite Creatif, a digital marketing agency based in Dubai. We specialize in SEO, social media management, and targeted advertising for restaurants and retail businesses. Our services help businesses increase online visibility, attract more customers, and boost revenue through strategic digital campaigns."
                  value={emailCompanyInfo}
                  onChange={(e) => setEmailCompanyInfo(e.target.value)}
                  autoFocus
                />
                <p className="text-xs text-gray-600 mt-1">
                  AI uses this to introduce your company and explain your services to the lead
                </p>
              </div>
            </div>

            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex items-center justify-end gap-3 rounded-b-lg">
              <button
                onClick={() => {
                  setShowEmailModal(false)
                  setEmailCompanyInfo('')
                  setCurrentLeadForEmail(null)
                }}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                disabled={generatingEmailId !== null}
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateEmail}
                disabled={generatingEmailId !== null || !emailCompanyInfo.trim()}
                className="px-4 py-2 text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {generatingEmailId !== null ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Generate Email
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* WhatsApp Generation Modal */}
      {showWhatsappModal && currentLeadForWhatsapp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-lg">
              <h2 className="text-xl font-semibold text-gray-900">Generate AI WhatsApp for {currentLeadForWhatsapp.title}</h2>
              <button
                onClick={() => {
                  setShowWhatsappModal(false)
                  setWhatsappCompanyInfo('')
                  setCurrentLeadForWhatsapp(null)
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="px-6 py-4 space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex gap-3">
                  <Sparkles className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-green-900">
                    <p className="font-semibold mb-1">AI WhatsApp Generation</p>
                    <p className="text-green-800">
                      Our AI will create a personalized WhatsApp message for <strong>{currentLeadForWhatsapp.title}</strong> based on your company information.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Company Information *
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                  rows={6}
                  placeholder="Example: We are Elite Creatif, a digital marketing agency based in Dubai. We specialize in SEO, social media management, and targeted advertising for restaurants and retail businesses."
                  value={whatsappCompanyInfo}
                  onChange={(e) => setWhatsappCompanyInfo(e.target.value)}
                  autoFocus
                />
                <p className="text-xs text-gray-600 mt-1">
                  AI uses this to create a friendly WhatsApp message introducing your company
                </p>
              </div>
            </div>

            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex items-center justify-end gap-3 rounded-b-lg">
              <button
                onClick={() => {
                  setShowWhatsappModal(false)
                  setWhatsappCompanyInfo('')
                  setCurrentLeadForWhatsapp(null)
                }}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                disabled={generatingWhatsappId !== null}
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateWhatsapp}
                disabled={generatingWhatsappId !== null || !whatsappCompanyInfo.trim()}
                className="px-4 py-2 text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {generatingWhatsappId !== null ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Generate WhatsApp
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Send Email Dialog */}
      {showSendEmailDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Send className="h-5 w-5 text-green-600" />
                Send Emails to {selectedLeads.length} Lead{selectedLeads.length > 1 ? 's' : ''}
              </h3>
              <button
                onClick={() => setShowSendEmailDialog(false)}
                disabled={sendingEmails}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gmail Address
                </label>
                <input
                  type="email"
                  value={senderEmail}
                  onChange={(e) => setSenderEmail(e.target.value)}
                  placeholder="your@gmail.com"
                  disabled={sendingEmails}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gmail App Password
                </label>
                <input
                  type="password"
                  value={senderPassword}
                  onChange={(e) => setSenderPassword(e.target.value)}
                  placeholder="App password (not regular password)"
                  disabled={sendingEmails}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:bg-gray-100"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Generate an app password at{' '}
                  <a
                    href="https://myaccount.google.com/apppasswords"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 hover:underline"
                  >
                    myaccount.google.com/apppasswords
                  </a>
                </p>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
                <p className="text-xs text-amber-800">
                  <strong>Note:</strong> Emails will be sent with a 5-15 second delay between each to avoid spam filters.
                </p>
              </div>
            </div>

            <div className="flex gap-3 justify-end mt-6">
              <Button
                variant="outline"
                onClick={() => setShowSendEmailDialog(false)}
                disabled={sendingEmails}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSendEmails}
                disabled={sendingEmails || !senderEmail || !senderPassword}
                className="bg-green-600 hover:bg-green-700 text-white"
                leftIcon={sendingEmails ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              >
                {sendingEmails ? 'Sending...' : `Send ${selectedLeads.length} Email${selectedLeads.length > 1 ? 's' : ''}`}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Send WhatsApp Dialog */}
      {showSendWhatsAppDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Send className="h-5 w-5 text-emerald-600" />
                Send WhatsApp to {selectedLeads.length} Lead{selectedLeads.length > 1 ? 's' : ''}
              </h3>
              <button
                onClick={() => setShowSendWhatsAppDialog(false)}
                disabled={sendingWhatsApp}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  WhatsApp Business Phone Number ID
                </label>
                <input
                  type="text"
                  value={whatsappPhoneNumberId}
                  onChange={(e) => setWhatsappPhoneNumberId(e.target.value)}
                  placeholder="123456789012345"
                  disabled={sendingWhatsApp}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:bg-gray-100"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Find this in your{' '}
                  <a
                    href="https://business.facebook.com/settings/whatsapp-business-accounts"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-600 hover:underline"
                  >
                    WhatsApp Business Account settings
                  </a>
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  WhatsApp Business API Access Token
                </label>
                <input
                  type="password"
                  value={whatsappAccessToken}
                  onChange={(e) => setWhatsappAccessToken(e.target.value)}
                  placeholder="Your access token"
                  disabled={sendingWhatsApp}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:bg-gray-100"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Generate a token in{' '}
                  <a
                    href="https://developers.facebook.com/apps"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-600 hover:underline"
                  >
                    Meta for Developers
                  </a>
                </p>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
                <p className="text-xs text-amber-800">
                  <strong>Note:</strong> WhatsApp messages will be sent with a 5-15 second delay between each to comply with rate limits.
                </p>
              </div>
            </div>

            <div className="flex gap-3 justify-end mt-6">
              <Button
                variant="outline"
                onClick={() => setShowSendWhatsAppDialog(false)}
                disabled={sendingWhatsApp}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSendWhatsApp}
                disabled={sendingWhatsApp || !whatsappPhoneNumberId || !whatsappAccessToken}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
                leftIcon={sendingWhatsApp ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              >
                {sendingWhatsApp ? 'Sending...' : `Send ${selectedLeads.length} WhatsApp${selectedLeads.length > 1 ? ' Messages' : ''}`}
              </Button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
