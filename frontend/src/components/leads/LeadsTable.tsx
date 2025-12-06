'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { toast } from 'react-hot-toast'
import {
  Users,
  Loader2,
  Download,
  Mail,
  Sparkles,
  Edit3,
  Save,
  X,
  Trash2,
  XCircle
} from 'lucide-react'

interface LeadsTableProps {
  campaignId: string
  refreshKey?: number
}

interface Lead {
  id: string
  title: string
  address: string
  phone: string
  website: string
  email: string
  description: string
  generated_email: string
  lead_score: number
  email_sent: boolean
  created_at: string
}

export default function LeadsTable({ campaignId, refreshKey = 0 }: LeadsTableProps) {
  const router = useRouter()
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set())
  const [editingLeadId, setEditingLeadId] = useState<string | null>(null)
  const [editedLead, setEditedLead] = useState<Partial<Lead>>({})
  const [bulkGeneratingDescriptions, setBulkGeneratingDescriptions] = useState(false)
  const [bulkGeneratingEmails, setBulkGeneratingEmails] = useState(false)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [companyInfo, setCompanyInfo] = useState('')
  const [cancellingGeneration, setCancellingGeneration] = useState(false)
  const [deletingLeadId, setDeletingLeadId] = useState<string | null>(null)
  const [generatingDescriptions, setGeneratingDescriptions] = useState<Set<string>>(new Set())
  const [deletingAllLeads, setDeletingAllLeads] = useState(false)
  const descriptionControllers = useRef<Record<string, AbortController>>({})
  const descriptionPollers = useRef<Record<string, NodeJS.Timeout>>({})

  useEffect(() => {
    fetchLeads()
  }, [campaignId, refreshKey])

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/login')
        return
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/leads`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      if (!response.ok) {
        if (response.status === 401) {
          router.push('/login')
          return
        }
        throw new Error('Failed to fetch leads')
      }

      const data = await response.json()
      setLeads(data)
    } catch (error) {
      console.error('Error fetching leads:', error)
      toast.error('Failed to load leads')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectAll = () => {
    if (selectedLeads.size === leads.length) {
      setSelectedLeads(new Set())
    } else {
      setSelectedLeads(new Set(leads.map(l => l.id)))
    }
  }

  const handleSelectLead = (leadId: string) => {
    const newSelected = new Set(selectedLeads)
    if (newSelected.has(leadId)) {
      newSelected.delete(leadId)
    } else {
      newSelected.add(leadId)
    }
    setSelectedLeads(newSelected)
  }

  const handleEditLead = (lead: Lead) => {
    setEditingLeadId(lead.id)
    setEditedLead({
      title: lead.title,
      description: lead.description,
      generated_email: lead.generated_email,
      email: lead.email
    })
  }

  const handleSaveLead = async (leadId: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/leads/${leadId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(editedLead)
        }
      )

      if (!response.ok) throw new Error('Failed to save changes')

      setLeads(prev => prev.map(lead =>
        lead.id === leadId ? { ...lead, ...editedLead } : lead
      ))

      setEditingLeadId(null)
      setEditedLead({})
      toast.success('Lead updated successfully!')
    } catch (error: any) {
      console.error('Error saving lead:', error)
      toast.error(error.message || 'Failed to save changes')
    }
  }

  const handleCancelEdit = () => {
    setEditingLeadId(null)
    setEditedLead({})
  }

  const handleDeleteLead = async (leadId: string) => {
    if (!confirm('Delete this lead? This cannot be undone.')) return

    try {
      setDeletingLeadId(leadId)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/leads/${leadId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) throw new Error('Failed to delete lead')

      setLeads(prev => prev.filter(lead => lead.id !== leadId))
      setSelectedLeads(prev => {
        const updated = new Set(prev)
        updated.delete(leadId)
        return updated
      })
      toast.success('Lead deleted')
    } catch (error: any) {
      console.error('Error deleting lead:', error)
      toast.error(error.message || 'Failed to delete lead')
    } finally {
      setDeletingLeadId(null)
    }
  }

  const handleDeleteAllLeads = async () => {
    if (leads.length === 0) {
      toast.error('No leads to delete')
      return
    }
    if (!confirm(`Delete all ${leads.length} leads in this campaign? This cannot be undone.`)) return

    try {
      setDeletingAllLeads(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/leads`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) throw new Error('Failed to delete all leads')

      setLeads([])
      setSelectedLeads(new Set())
      toast.success('All leads deleted')
    } catch (error: any) {
      console.error('Delete all leads error:', error)
      toast.error(error.message || 'Failed to delete all leads')
    } finally {
      setDeletingAllLeads(false)
    }
  }

  const handleCancelGeneration = async () => {
    if (!confirm('Are you sure you want to cancel the current operation?')) {
      return
    }

    try {
      setCancellingGeneration(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/cancel-generation`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('Failed to cancel')
      }

      const data = await response.json()
      toast.success(data.message || 'Operation cancelled')
      setBulkGeneratingDescriptions(false)
      setBulkGeneratingEmails(false)
      await fetchLeads()
    } catch (error: any) {
      console.error('Cancel error:', error)
      toast.error(error.message || 'Failed to cancel')
    } finally {
      setCancellingGeneration(false)
    }
  }

  const handleBulkGenerateDescriptions = async () => {
    if (selectedLeads.size === 0) {
      toast.error('Please select at least one lead')
      return
    }

    if (!confirm(`Generate AI descriptions for ${selectedLeads.size} leads?`)) {
      return
    }

    try {
      setBulkGeneratingDescriptions(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/bulk-generate-descriptions`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            lead_ids: Array.from(selectedLeads)
          })
        }
      )

      if (!response.ok) throw new Error('Failed to generate descriptions')

      const data = await response.json()
      toast.success(`Generated ${data.generated} descriptions!`, { duration: 5000 })
      await fetchLeads()
      setSelectedLeads(new Set())
    } catch (error: any) {
      console.error('Bulk generate descriptions error:', error)
      toast.error('Failed to generate descriptions')
    } finally {
      setBulkGeneratingDescriptions(false)
    }
  }

  const handleGenerateDescription = async (leadId: string) => {
    try {
      const controller = new AbortController()
      descriptionControllers.current[leadId] = controller

      setGeneratingDescriptions(prev => new Set(prev).add(leadId))
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/leads/${leadId}/generate-description`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          signal: controller.signal
        }
      )

      if (!response.ok) throw new Error('Failed to generate description')

      toast.success('AI description is being generated')

      // Poll for updated lead description for ~30s
      let attempts = 0
      const poll = async () => {
        attempts += 1
        await fetchLeads()
        const updated = leads.find(l => l.id === leadId)
        if (updated?.description) {
          clearInterval(descriptionPollers.current[leadId])
          delete descriptionPollers.current[leadId]
          setGeneratingDescriptions(prev => {
            const next = new Set(prev)
            next.delete(leadId)
            return next
          })
        } else if (attempts >= 15) {
          clearInterval(descriptionPollers.current[leadId])
          delete descriptionPollers.current[leadId]
          setGeneratingDescriptions(prev => {
            const next = new Set(prev)
            next.delete(leadId)
            return next
          })
          toast('AI description is still processing; please wait and refresh.')
        }
      }

      const intervalId = setInterval(poll, 2000)
      descriptionPollers.current[leadId] = intervalId
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        toast('Generation cancelled')
      } else {
        console.error('Generate description error:', error)
        toast.error(error.message || 'Failed to generate description')
      }
    } finally {
      delete descriptionControllers.current[leadId]
      setGeneratingDescriptions(prev => {
        const next = new Set(prev)
        next.delete(leadId)
        return next
      })
    }
  }

  const handleCancelGenerateDescription = (leadId: string) => {
    const controller = descriptionControllers.current[leadId]
    if (controller) {
      controller.abort()
    }
    const poller = descriptionPollers.current[leadId]
    if (poller) {
      clearInterval(poller)
      delete descriptionPollers.current[leadId]
    }
    setGeneratingDescriptions(prev => {
      const next = new Set(prev)
      next.delete(leadId)
      return next
    })
  }

  const handleBulkGenerateEmails = async () => {
    if (selectedLeads.size === 0) {
      toast.error('Please select at least one lead')
      return
    }

    if (!companyInfo.trim()) {
      toast.error('Please enter your company information')
      return
    }

    if (!confirm(`Generate AI emails for ${selectedLeads.size} leads?`)) {
      return
    }

    try {
      setBulkGeneratingEmails(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/v1/campaigns/${campaignId}/bulk-generate-emails`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            lead_ids: Array.from(selectedLeads),
            company_info: companyInfo.trim()
          })
        }
      )

      if (!response.ok) throw new Error('Failed to generate emails')

      const data = await response.json()
      toast.success(`Generated ${data.generated} emails!`, { duration: 5000 })
      await fetchLeads()
      setSelectedLeads(new Set())
      setShowEmailModal(false)
    } catch (error: any) {
      console.error('Bulk generate emails error:', error)
      toast.error('Failed to generate emails')
    } finally {
      setBulkGeneratingEmails(false)
    }
  }

  const exportToCSV = () => {
    if (leads.length === 0) {
      toast.error('No leads to export')
      return
    }

    const headers = ['Name', 'Email', 'Phone', 'Website', 'Address', 'Description', 'Generated Email', 'Lead Score', 'Email Sent']
    const rows = leads.map(lead => [
      lead.title,
      lead.email || '',
      lead.phone || '',
      lead.website || '',
      lead.address || '',
      (lead.description || '').replace(/"/g, '""'),
      (lead.generated_email || '').replace(/"/g, '""'),
      lead.lead_score || 0,
      lead.email_sent ? 'Yes' : 'No'
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `leads_${campaignId}_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    toast.success('Leads exported successfully!')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (leads.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Users className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p className="text-gray-500">No leads found. Generate or import leads to get started.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-600 font-medium">Total Leads</p>
          <p className="text-2xl font-bold text-blue-700">{leads.length}</p>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-sm text-green-600 font-medium">With Emails</p>
          <p className="text-2xl font-bold text-green-700">
            {leads.filter(l => l.email).length}
          </p>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <p className="text-sm text-purple-600 font-medium">AI Content</p>
          <p className="text-2xl font-bold text-purple-700">
            {leads.filter(l => l.generated_email).length}
          </p>
        </div>
        <div className="p-3 bg-amber-50 rounded-lg">
          <p className="text-sm text-amber-600 font-medium">Emails Sent</p>
          <p className="text-2xl font-bold text-amber-700">
            {leads.filter(l => l.email_sent).length}
          </p>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedLeads.size > 0 && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <p className="font-medium text-blue-900">
                {selectedLeads.size} lead{selectedLeads.size > 1 ? 's' : ''} selected
                {(bulkGeneratingDescriptions || bulkGeneratingEmails) && (
                  <span className="ml-2 text-sm text-blue-600">
                    (Processing...)
                  </span>
                )}
              </p>
              <div className="flex gap-2">
                {(bulkGeneratingDescriptions || bulkGeneratingEmails) ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCancelGeneration}
                    disabled={cancellingGeneration}
                    className="border-red-300 text-red-600 hover:bg-red-50"
                  >
                    {cancellingGeneration ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Cancelling...</>
                    ) : (
                      <><XCircle className="w-4 h-4 mr-2" /> Cancel Operation</>
                    )}
                  </Button>
                ) : (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleBulkGenerateDescriptions}
                      disabled={bulkGeneratingDescriptions}
                    >
                      {bulkGeneratingDescriptions ? (
                        <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
                      ) : (
                        <><Sparkles className="w-4 h-4 mr-2" /> Generate Descriptions</>
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowEmailModal(true)}
                      disabled={bulkGeneratingEmails}
                    >
                      <Mail className="w-4 h-4 mr-2" /> Generate Emails
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedLeads(new Set())}
                    >
                      Clear Selection
                    </Button>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Leads Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Leads ({leads.length})</CardTitle>
              <CardDescription>Manage, edit, and enrich your campaign leads</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={exportToCSV}
                variant="outline"
                size="sm"
              >
                <Download className="w-4 h-4 mr-2" /> Export CSV
              </Button>
              <Button
                onClick={handleDeleteAllLeads}
                variant="outline"
                size="sm"
                className="text-red-600 border-red-200 hover:bg-red-50"
                disabled={deletingAllLeads || leads.length === 0}
              >
                {deletingAllLeads ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Deleting...</>
                ) : (
                  <><Trash2 className="w-4 h-4 mr-2" /> Delete All</>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedLeads.size === leads.length}
                      onChange={handleSelectAll}
                      className="rounded"
                    />
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Name</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Email</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Phone</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">AI Description</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Generated Email</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Score</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr key={lead.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedLeads.has(lead.id)}
                        onChange={() => handleSelectLead(lead.id)}
                        className="rounded"
                      />
                    </td>
                    <td className="px-4 py-3">
                      {editingLeadId === lead.id ? (
                        <input
                          type="text"
                          className="w-full px-2 py-1 border rounded text-sm"
                          value={editedLead.title || ''}
                          onChange={(e) => setEditedLead({ ...editedLead, title: e.target.value })}
                        />
                      ) : (
                        <>
                          <div className="font-medium text-gray-900">{lead.title}</div>
                          <div className="text-xs text-gray-500">{lead.address}</div>
                        </>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {editingLeadId === lead.id ? (
                        <input
                          type="email"
                          className="w-full px-2 py-1 border rounded text-sm"
                          value={editedLead.email || ''}
                          onChange={(e) => setEditedLead({ ...editedLead, email: e.target.value })}
                        />
                      ) : (
                        <div className="text-gray-700">{lead.email || 'N/A'}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {lead.phone || 'N/A'}
                    </td>
                    <td className="px-4 py-3">
                      {editingLeadId === lead.id ? (
                        <textarea
                          className="w-full px-2 py-1 border rounded text-sm"
                          rows={3}
                          value={editedLead.description || ''}
                          onChange={(e) => setEditedLead({ ...editedLead, description: e.target.value })}
                        />
                      ) : (
                        <div className="text-gray-700 max-w-xs line-clamp-3">
                          {lead.description || 'Not generated'}
                          <div className="mt-2 flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleGenerateDescription(lead.id)}
                              disabled={generatingDescriptions.has(lead.id)}
                              className="text-primary-600 border-primary-200"
                            >
                              {generatingDescriptions.has(lead.id) ? (
                                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating</>
                              ) : (
                                <><Sparkles className="w-4 h-4 mr-2" /> Generate AI</>
                              )}
                            </Button>
                            {generatingDescriptions.has(lead.id) && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleCancelGenerateDescription(lead.id)}
                                className="text-red-600"
                              >
                                <X className="w-4 h-4 mr-1" /> Stop
                              </Button>
                            )}
                          </div>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {editingLeadId === lead.id ? (
                        <textarea
                          className="w-full px-2 py-1 border rounded text-sm"
                          rows={5}
                          value={editedLead.generated_email || ''}
                          onChange={(e) => setEditedLead({ ...editedLead, generated_email: e.target.value })}
                        />
                      ) : (
                        <div className="text-gray-700 max-w-md line-clamp-5">
                          {lead.generated_email || 'Not generated'}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full font-bold ${
                        lead.lead_score >= 80 ? 'bg-green-100 text-green-700' :
                        lead.lead_score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {lead.lead_score || 0}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        {editingLeadId === lead.id ? (
                          <>
                            <button
                              onClick={() => handleSaveLead(lead.id)}
                              className="p-2 text-green-600 hover:bg-green-50 rounded"
                              title="Save changes"
                            >
                              <Save className="w-4 h-4" />
                            </button>
                            <button
                              onClick={handleCancelEdit}
                              className="p-2 text-red-600 hover:bg-red-50 rounded"
                              title="Cancel"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => handleEditLead(lead)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                            title="Edit lead"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteLead(lead.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded disabled:opacity-60"
                          title="Delete lead"
                          disabled={deletingLeadId === lead.id}
                        >
                          {deletingLeadId === lead.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Company Info Modal for Bulk Email Generation */}
      <Modal
        isOpen={showEmailModal}
        onClose={() => setShowEmailModal(false)}
        title="Generate Bulk AI Emails"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Generate personalized AI emails for {selectedLeads.size} selected leads
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Your Company Information *
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              rows={5}
              placeholder="Example: We are Elite Creatif, a digital marketing agency based in Dubai..."
              value={companyInfo}
              onChange={(e) => setCompanyInfo(e.target.value)}
            />
          </div>
          <div className="flex gap-3">
            <Button
              onClick={handleBulkGenerateEmails}
              disabled={bulkGeneratingEmails}
              className="flex-1"
            >
              {bulkGeneratingEmails ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
              ) : (
                'Generate Emails'
              )}
            </Button>
            <Button
              onClick={() => setShowEmailModal(false)}
              variant="outline"
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
