'use client'

import React, { useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import { toast } from '@/components/ui/Toast'
import { useCampaigns } from '@/hooks/useCampaigns'
import {
  Plus,
  Search,
  Filter,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  Play,
  Pause,
  Users,
  Mail,
  MessageSquare,
  Calendar,
  TrendingUp,
  Loader2
} from 'lucide-react'
import { formatNumber, formatDate, getStatusColor } from '@/lib/utils'

interface Campaign {
  id: string
  name: string
  description: string
  status: 'draft' | 'active' | 'paused' | 'completed'
  lead_source: 'google_maps' | 'linkedin' | 'instagram'
  leads_count: number
  emails_sent: number
  response_rate: number
  created_at: string
}

export default function CampaignsPage() {
  const { campaigns, loading, createCampaign, updateCampaign, deleteCampaign } = useCampaigns()

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isViewModalOpen, setIsViewModalOpen] = useState(false)
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null)
  const [selectedCampaignLeads, setSelectedCampaignLeads] = useState<any[]>([])
  const [selectedCampaignEmails, setSelectedCampaignEmails] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  // WhatsApp state
  const [isSendWhatsAppModalOpen, setIsSendWhatsAppModalOpen] = useState(false)
  const [sendingWhatsApp, setSendingWhatsApp] = useState(false)
  const [whatsappPhoneId, setWhatsappPhoneId] = useState('')
  const [whatsappToken, setWhatsappToken] = useState('')

  // Edit modal state
  const [isEditEmailModalOpen, setIsEditEmailModalOpen] = useState(false)
  const [editingEmail, setEditingEmail] = useState<any | null>(null)
  const [editEmailSubject, setEditEmailSubject] = useState('')
  const [editEmailBody, setEditEmailBody] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  // Edit description modal state
  const [isEditDescriptionModalOpen, setIsEditDescriptionModalOpen] = useState(false)
  const [editingLead, setEditingLead] = useState<any | null>(null)
  const [editDescription, setEditDescription] = useState('')

  // Create Campaign Form State
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'active',
    search_query: '',
    lead_source: 'google_maps',
    max_leads: 100
  })

  const sourceOptions = [
    { value: 'google_maps', label: 'Google Maps' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'instagram', label: 'Instagram' }
  ]

  const handleCreateCampaign = async () => {
    if (!formData.name.trim()) {
      toast.error('Campaign name is required')
      return
    }

    if (!formData.search_query.trim()) {
      toast.error('Search query is required')
      return
    }

    await createCampaign({
      name: formData.name,
      description: formData.description,
      status: formData.status,
      search_query: formData.search_query,
      lead_source: formData.lead_source
    })

    setIsCreateModalOpen(false)
    setFormData({ name: '', description: '', status: 'active', search_query: '', lead_source: 'google_maps', max_leads: 100 })
  }

  const handleDeleteCampaign = async (id: string) => {
    await deleteCampaign(id)
  }

  const handleStatusChange = async (id: string, newStatus: Campaign['status']) => {
    await updateCampaign(id, { status: newStatus })
  }

  const handleViewCampaign = async (campaign: Campaign) => {
    setSelectedCampaign(campaign)
    setIsViewModalOpen(true)

    // Fetch leads and emails for this campaign
    try {
      const token = localStorage.getItem('token')
      const [leadsRes, emailsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/v1/campaigns/${campaign.id}/leads`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`http://localhost:8000/api/v1/campaigns/${campaign.id}/emails`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ])

      if (leadsRes.ok && emailsRes.ok) {
        const leads = await leadsRes.json()
        const emails = await emailsRes.json()
        setSelectedCampaignLeads(leads)
        setSelectedCampaignEmails(emails)
      }
    } catch (error) {
      console.error('Error fetching campaign details:', error)
    }
  }

  const handleEditEmail = (email: any) => {
    setEditingEmail(email)
    setEditEmailSubject(email.subject)
    setEditEmailBody(email.body)
    setIsEditEmailModalOpen(true)
  }

  const handleSaveEmail = async () => {
    if (!editingEmail) return

    setIsSaving(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:8000/api/v1/emails/${editingEmail.id}?subject=${encodeURIComponent(editEmailSubject)}&body=${encodeURIComponent(editEmailBody)}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        // Update local state
        setSelectedCampaignEmails(prev =>
          prev.map(e => e.id === editingEmail.id
            ? { ...e, subject: editEmailSubject, body: editEmailBody }
            : e
          )
        )
        setIsEditEmailModalOpen(false)
        toast.success('Email updated successfully!')
      } else {
        toast.error('Failed to update email')
      }
    } catch (error) {
      console.error('Error saving email:', error)
      toast.error('Error saving email')
    } finally {
      setIsSaving(false)
    }
  }

  const handleEditDescription = (lead: any) => {
    setEditingLead(lead)
    setEditDescription(lead.description || '')
    setIsEditDescriptionModalOpen(true)
  }

  const handleSaveDescription = async () => {
    if (!editingLead) return

    setIsSaving(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:8000/api/v1/leads/${editingLead.id}?description=${encodeURIComponent(editDescription)}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        // Update local state
        setSelectedCampaignLeads(prev =>
          prev.map(l => l.id === editingLead.id
            ? { ...l, description: editDescription }
            : l
          )
        )
        setIsEditDescriptionModalOpen(false)
        toast.success('Description updated successfully!')
      } else {
        toast.error('Failed to update description')
      }
    } catch (error) {
      console.error('Error saving description:', error)
      toast.error('Error saving description')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSendWhatsApp = () => {
    // Load WhatsApp credentials from localStorage
    const savedPhoneId = localStorage.getItem('whatsapp_phone_id') || ''
    const savedToken = localStorage.getItem('whatsapp_token') || ''

    setWhatsappPhoneId(savedPhoneId)
    setWhatsappToken(savedToken)
    setIsSendWhatsAppModalOpen(true)
  }

  const handleConfirmSendWhatsApp = async () => {
    if (!selectedCampaign) return

    if (!whatsappPhoneId || !whatsappToken) {
      toast.error('Please enter WhatsApp credentials')
      return
    }

    setSendingWhatsApp(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:8000/api/v1/campaigns/${selectedCampaign.id}/send-whatsapp`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          phone_number_id: whatsappPhoneId,
          access_token: whatsappToken
        })
      })

      if (response.ok) {
        const result = await response.json()
        toast.success(`WhatsApp messages sent! Success: ${result.sent}, Failed: ${result.failed}`)
        setIsSendWhatsAppModalOpen(false)

        // Refresh campaign data
        handleViewCampaign(selectedCampaign)
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to send WhatsApp messages')
      }
    } catch (error) {
      console.error('Error sending WhatsApp:', error)
      toast.error('Error sending WhatsApp messages')
    } finally {
      setSendingWhatsApp(false)
    }
  }

  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          campaign.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = filterStatus === 'all' || campaign.status === filterStatus
    return matchesSearch && matchesFilter
  })

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'google_maps':
        return '🗺️'
      case 'linkedin':
        return '💼'
      case 'instagram':
        return '📸'
      default:
        return '📊'
    }
  }

  const getSourceLabel = (source: string) => {
    switch (source) {
      case 'google_maps':
        return 'Google Maps'
      case 'linkedin':
        return 'LinkedIn'
      case 'instagram':
        return 'Instagram'
      default:
        return 'Unknown'
    }
  }

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Campaigns</h1>
            <p className="mt-2 text-gray-600">
              Manage your lead generation campaigns
            </p>
          </div>
          <Button
            variant="primary"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setIsCreateModalOpen(true)}
          >
            New Campaign
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search campaigns..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={<Search className="h-4 w-4" />}
                fullWidth
              />
            </div>
            <Select
              options={[
                { value: 'all', label: 'All Status' },
                { value: 'draft', label: 'Draft' },
                { value: 'active', label: 'Active' },
                { value: 'paused', label: 'Paused' },
                { value: 'completed', label: 'Completed' }
              ]}
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {loading && (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      )}

      {/* Campaign Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Campaigns</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{campaigns.length}</p>
              </div>
              <div className="p-3 bg-primary-50 rounded-lg">
                <TrendingUp className="h-5 w-5 text-primary-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {campaigns.filter(c => c.status === 'active').length}
                </p>
              </div>
              <div className="p-3 bg-success-50 rounded-lg">
                <Play className="h-5 w-5 text-success-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Leads</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatNumber(campaigns.reduce((sum, c) => sum + c.leads_count, 0))}
                </p>
              </div>
              <div className="p-3 bg-info-50 rounded-lg">
                <Users className="h-5 w-5 text-info-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Response Rate</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {(campaigns.reduce((sum, c) => sum + c.response_rate, 0) / campaigns.length).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-warning-50 rounded-lg">
                <Mail className="h-5 w-5 text-warning-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Campaign Cards */}
      {filteredCampaigns.length === 0 ? (
        <Card>
          <CardContent>
            <div className="text-center py-12">
              <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No campaigns found
              </h3>
              <p className="text-gray-600 mb-4">
                {searchQuery || filterStatus !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Create your first campaign to get started'}
              </p>
              {!searchQuery && filterStatus === 'all' && (
                <Button
                  variant="primary"
                  leftIcon={<Plus className="h-4 w-4" />}
                  onClick={() => setIsCreateModalOpen(true)}
                >
                  Create Campaign
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCampaigns.map((campaign) => (
            <Card key={campaign.id} hover clickable>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{getSourceIcon(campaign.lead_source)}</span>
                      <Badge
                        variant={
                          campaign.status === 'active' ? 'success' :
                          campaign.status === 'completed' ? 'info' :
                          campaign.status === 'paused' ? 'warning' : 'default'
                        }
                        size="sm"
                        dot
                      >
                        {campaign.status}
                      </Badge>
                    </div>
                    <CardTitle className="truncate">{campaign.name}</CardTitle>
                    <CardDescription className="line-clamp-2">
                      {campaign.description || 'No description'}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      Leads
                    </span>
                    <span className="font-semibold text-gray-900">
                      {formatNumber(campaign.leads_count)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      Emails Sent
                    </span>
                    <span className="font-semibold text-gray-900">
                      {formatNumber(campaign.emails_sent)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      Response Rate
                    </span>
                    <span className="font-semibold text-success-600">
                      {campaign.response_rate}%
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200">
                    <span className="text-gray-500 flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      {formatDate(campaign.created_at)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {getSourceLabel(campaign.lead_source)}
                    </span>
                  </div>
                </div>
              </CardContent>

              <CardFooter>
                <div className="flex gap-2 w-full">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    leftIcon={<Eye className="h-4 w-4" />}
                    onClick={() => handleViewCampaign(campaign)}
                  >
                    View
                  </Button>

                  {campaign.status === 'active' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      leftIcon={<Pause className="h-4 w-4" />}
                      onClick={() => handleStatusChange(campaign.id, 'paused')}
                    >
                      Pause
                    </Button>
                  ) : campaign.status === 'paused' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      leftIcon={<Play className="h-4 w-4" />}
                      onClick={() => handleStatusChange(campaign.id, 'active')}
                    >
                      Resume
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      leftIcon={<Play className="h-4 w-4" />}
                      onClick={() => handleStatusChange(campaign.id, 'active')}
                    >
                      Start
                    </Button>
                  )}

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteCampaign(campaign.id)}
                  >
                    <Trash2 className="h-4 w-4 text-error-500" />
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Create Campaign Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Campaign"
        description="Set up a new lead generation campaign"
        size="md"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateCampaign}
            >
              Create Campaign
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Campaign Name"
            placeholder="e.g., Tech Startups SF"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            fullWidth
            required
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Description
            </label>
            <textarea
              placeholder="Describe your campaign..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows={3}
            />
          </div>

          <Input
            label="Search Query"
            placeholder="e.g., restaurants, coffee shops, dentists"
            value={formData.search_query}
            onChange={(e) => setFormData({ ...formData, search_query: e.target.value })}
            fullWidth
            required
            hint="What type of businesses do you want to find?"
          />

          <Select
            label="Campaign Status"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            fullWidth
          >
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
          </Select>

          <Select
            label="Lead Source"
            value={formData.lead_source}
            onChange={(e) => setFormData({ ...formData, lead_source: e.target.value })}
            fullWidth
          >
            <option value="google_maps">Google Maps</option>
            <option value="linkedin">LinkedIn</option>
            <option value="instagram">Instagram</option>
          </Select>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Max Leads: {formData.max_leads}
            </label>
            <input
              type="range"
              min="50"
              max="1000"
              step="50"
              value={formData.max_leads}
              onChange={(e) => setFormData({ ...formData, max_leads: Number(e.target.value) })}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>
      </Modal>

      {/* View Campaign Modal */}
      <Modal
        isOpen={isViewModalOpen}
        onClose={() => {
          setIsViewModalOpen(false)
          setSelectedCampaignLeads([])
          setSelectedCampaignEmails([])
        }}
        title={`${selectedCampaign?.name || ''} - Generated Content`}
        size="xl"
      >
        {selectedCampaign && (
          <div className="space-y-6">
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-primary-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Total Leads</p>
                <p className="text-2xl font-bold text-gray-900">{selectedCampaignLeads.length}</p>
              </div>
              <div className="bg-success-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Descriptions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {selectedCampaignLeads.filter(l => l.description).length}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Emails Generated</p>
                <p className="text-2xl font-bold text-gray-900">{selectedCampaignEmails.length}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">WhatsApp Generated</p>
                <p className="text-2xl font-bold text-gray-900">
                  {selectedCampaignLeads.filter(l => l.generated_whatsapp).length}
                </p>
              </div>
            </div>

            {selectedCampaignLeads.length > 0 ? (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900">Leads & Generated Content</h4>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleSendWhatsApp}
                    leftIcon={<MessageSquare className="h-4 w-4" />}
                    disabled={selectedCampaignLeads.filter(l => l.generated_whatsapp && l.phone).length === 0}
                  >
                    Send WhatsApp ({selectedCampaignLeads.filter(l => l.generated_whatsapp && l.phone).length})
                  </Button>
                </div>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {selectedCampaignLeads.map((lead, index) => {
                    const email = selectedCampaignEmails.find(e => e.lead_id === lead.id)
                    return (
                      <div key={lead.id} className="bg-gray-50 rounded-lg p-4 space-y-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <h5 className="font-semibold text-gray-900">{lead.title}</h5>
                            <p className="text-sm text-gray-600">{lead.address || 'No address'}</p>
                            <p className="text-sm text-gray-600">{lead.phone || 'No phone'}</p>
                            {lead.website && (
                              <a href={lead.website} target="_blank" className="text-sm text-primary-600 hover:underline">
                                {lead.website}
                              </a>
                            )}
                          </div>
                          <Badge variant="default">{lead.contact_source || 'google_maps'}</Badge>
                        </div>

                        {lead.description && (
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-xs font-semibold text-gray-700">AI Description:</p>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditDescription(lead)}
                                leftIcon={<Edit className="h-3 w-3" />}
                              >
                                Edit
                              </Button>
                            </div>
                            <p className="text-sm text-gray-700 bg-white p-2 rounded border border-gray-200">
                              {lead.description}
                            </p>
                          </div>
                        )}

                        {email && (
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-xs font-semibold text-gray-700">Generated Email:</p>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditEmail(email)}
                                leftIcon={<Edit className="h-3 w-3" />}
                              >
                                Edit
                              </Button>
                            </div>
                            <div className="bg-white p-3 rounded border border-gray-200 space-y-2">
                              <p className="text-sm">
                                <span className="font-semibold">Subject: </span>
                                {email.subject}
                              </p>
                              <p className="text-sm text-gray-700 whitespace-pre-wrap">{email.body}</p>
                              <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
                                <Badge variant={email.status === 'sent' ? 'success' : 'default'} size="sm">
                                  {email.status}
                                </Badge>
                                {email.sent_at && (
                                  <span className="text-xs text-gray-500">
                                    Sent: {formatDate(email.sent_at)}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        )}

                        {lead.generated_whatsapp && (
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-xs font-semibold text-gray-700 flex items-center gap-1">
                                <MessageSquare className="h-3 w-3 text-green-600" />
                                Generated WhatsApp:
                              </p>
                            </div>
                            <div className="bg-green-50 p-3 rounded border border-green-200 space-y-2">
                              <p className="text-sm text-gray-700 whitespace-pre-wrap">{lead.generated_whatsapp}</p>
                              <div className="flex items-center gap-2 pt-2 border-t border-green-200">
                                <Badge variant={lead.whatsapp_sent ? 'success' : 'default'} size="sm">
                                  {lead.whatsapp_sent ? 'sent' : 'pending'}
                                </Badge>
                                {lead.phone && (
                                  <span className="text-xs text-gray-500">
                                    To: {lead.phone}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No leads found for this campaign</p>
                <p className="text-sm">Run the automation to generate leads and emails</p>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Edit Email Modal */}
      <Modal
        isOpen={isEditEmailModalOpen}
        onClose={() => setIsEditEmailModalOpen(false)}
        title="Edit Email"
        description="Refine the AI-generated email before sending"
        size="lg"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setIsEditEmailModalOpen(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveEmail}
              disabled={isSaving}
              leftIcon={isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Subject Line
            </label>
            <Input
              value={editEmailSubject}
              onChange={(e) => setEditEmailSubject(e.target.value)}
              placeholder="Email subject..."
              fullWidth
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Email Body
            </label>
            <textarea
              value={editEmailBody}
              onChange={(e) => setEditEmailBody(e.target.value)}
              placeholder="Email content..."
              className="w-full px-4 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows={12}
            />
            <p className="text-xs text-gray-500 mt-1">
              {editEmailBody.length} characters
            </p>
          </div>
        </div>
      </Modal>

      {/* Edit Description Modal */}
      <Modal
        isOpen={isEditDescriptionModalOpen}
        onClose={() => setIsEditDescriptionModalOpen(false)}
        title="Edit Business Description"
        description="Refine the AI-generated business description"
        size="lg"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setIsEditDescriptionModalOpen(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveDescription}
              disabled={isSaving}
              leftIcon={isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Business Description
            </label>
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              placeholder="Enter business description..."
              className="w-full px-4 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows={6}
            />
            <p className="text-xs text-gray-500 mt-1">
              {editDescription.length} characters
            </p>
          </div>
        </div>
      </Modal>

      {/* Send WhatsApp Modal */}
      <Modal
        isOpen={isSendWhatsAppModalOpen}
        onClose={() => setIsSendWhatsAppModalOpen(false)}
        title="Send WhatsApp Messages"
        description="Send WhatsApp messages to all leads with generated content"
        size="md"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setIsSendWhatsAppModalOpen(false)}
              disabled={sendingWhatsApp}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirmSendWhatsApp}
              disabled={sendingWhatsApp || !whatsappPhoneId || !whatsappToken}
              leftIcon={sendingWhatsApp ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageSquare className="h-4 w-4" />}
            >
              {sendingWhatsApp ? 'Sending...' : 'Send Messages'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-3">
              <MessageSquare className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900">
                <p className="font-semibold mb-1">Bulk WhatsApp Sending</p>
                <p>
                  This will send WhatsApp messages to all leads that have:
                </p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Generated WhatsApp message</li>
                  <li>Valid phone number</li>
                  <li>Not already sent</li>
                </ul>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              WhatsApp Phone Number ID
            </label>
            <Input
              value={whatsappPhoneId}
              onChange={(e) => setWhatsappPhoneId(e.target.value)}
              placeholder="Enter your WhatsApp Business Phone Number ID"
              fullWidth
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Access Token
            </label>
            <Input
              type="password"
              value={whatsappToken}
              onChange={(e) => setWhatsappToken(e.target.value)}
              placeholder="Enter your WhatsApp Business API access token"
              fullWidth
            />
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-sm text-yellow-800">
              <span className="font-semibold">Note:</span> Make sure you have configured your WhatsApp credentials in Settings before sending.
            </p>
          </div>

          {selectedCampaignLeads && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-700">
                <span className="font-semibold">Ready to send:</span>{' '}
                {selectedCampaignLeads.filter(l => l.generated_whatsapp && l.phone && !l.whatsapp_sent).length} messages
              </p>
            </div>
          )}
        </div>
      </Modal>
    </DashboardLayout>
  )
}
