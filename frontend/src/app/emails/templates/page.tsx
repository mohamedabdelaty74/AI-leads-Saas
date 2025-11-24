'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import Input from '@/components/ui/Input'
import { toast } from '@/components/ui/Toast'
import {
  Plus,
  Edit,
  Trash2,
  Mail,
  FileText,
  Eye,
  Copy,
  Loader2,
  Sparkles
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface EmailTemplate {
  id: string
  name: string
  description: string
  subject: string
  body: string
  use_ai_personalization: boolean
  times_used: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export default function EmailTemplatesPage() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isViewModalOpen, setIsViewModalOpen] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    subject: '',
    body: '',
    use_ai_personalization: true
  })

  // Fetch templates
  const fetchTemplates = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/email-templates', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) throw new Error('Failed to fetch templates')

      const data = await response.json()
      setTemplates(data)
    } catch (error) {
      console.error('Error fetching templates:', error)
      toast.error('Failed to load email templates')
    } finally {
      setLoading(false)
    }
  }

  // Create template
  const handleCreateTemplate = async () => {
    if (!formData.name.trim()) {
      toast.error('Template name is required')
      return
    }

    if (!formData.subject.trim()) {
      toast.error('Email subject is required')
      return
    }

    if (!formData.body.trim()) {
      toast.error('Email body is required')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/email-templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      })

      if (!response.ok) throw new Error('Failed to create template')

      toast.success('Email template created successfully')
      setIsCreateModalOpen(false)
      setFormData({ name: '', description: '', subject: '', body: '', use_ai_personalization: true })
      fetchTemplates()
    } catch (error) {
      console.error('Error creating template:', error)
      toast.error('Failed to create email template')
    }
  }

  // Update template
  const handleUpdateTemplate = async () => {
    if (!selectedTemplate) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/api/v1/email-templates/${selectedTemplate.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      })

      if (!response.ok) throw new Error('Failed to update template')

      toast.success('Email template updated successfully')
      setIsEditModalOpen(false)
      setSelectedTemplate(null)
      setFormData({ name: '', description: '', subject: '', body: '', use_ai_personalization: true })
      fetchTemplates()
    } catch (error) {
      console.error('Error updating template:', error)
      toast.error('Failed to update email template')
    }
  }

  // Delete template
  const handleDeleteTemplate = async (id: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/api/v1/email-templates/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) throw new Error('Failed to delete template')

      toast.success('Email template deleted successfully')
      fetchTemplates()
    } catch (error) {
      console.error('Error deleting template:', error)
      toast.error('Failed to delete email template')
    }
  }

  // Duplicate template
  const handleDuplicateTemplate = (template: EmailTemplate) => {
    setFormData({
      name: `${template.name} (Copy)`,
      description: template.description,
      subject: template.subject,
      body: template.body,
      use_ai_personalization: template.use_ai_personalization
    })
    setIsCreateModalOpen(true)
  }

  // View template
  const handleViewTemplate = (template: EmailTemplate) => {
    setSelectedTemplate(template)
    setIsViewModalOpen(true)
  }

  // Edit template
  const handleEditTemplate = (template: EmailTemplate) => {
    setSelectedTemplate(template)
    setFormData({
      name: template.name,
      description: template.description,
      subject: template.subject,
      body: template.body,
      use_ai_personalization: template.use_ai_personalization
    })
    setIsEditModalOpen(true)
  }

  useEffect(() => {
    fetchTemplates()
  }, [])

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Email Templates</h1>
            <p className="text-gray-600 mt-1">
              Create and manage AI-powered email templates
            </p>
          </div>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Template
          </Button>
        </div>

        {/* Templates Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : templates.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Mail className="w-16 h-16 text-gray-400 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No email templates yet
              </h3>
              <p className="text-gray-600 mb-4">
                Create your first email template to get started with AI-powered personalization
              </p>
              <Button onClick={() => setIsCreateModalOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Template
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <Card key={template.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <CardDescription className="mt-1">
                        {template.description || 'No description'}
                      </CardDescription>
                    </div>
                    {template.use_ai_personalization && (
                      <Sparkles className="w-5 h-5 text-purple-600" />
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Subject preview */}
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Subject:</p>
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {template.subject}
                      </p>
                    </div>

                    {/* Body preview */}
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Body:</p>
                      <p className="text-sm text-gray-700 line-clamp-3">
                        {template.body}
                      </p>
                    </div>

                    {/* Stats */}
                    <div className="flex items-center justify-between text-xs text-gray-600 pt-2 border-t">
                      <span>Used {template.times_used} times</span>
                      <span>{formatDate(template.created_at)}</span>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleViewTemplate(template)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        View
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditTemplate(template)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDuplicateTemplate(template)}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteTemplate(template.id)}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Template Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="Create Email Template"
        >
          <div className="space-y-4">
            <Input
              label="Template Name"
              placeholder="e.g., Restaurant Outreach"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
                placeholder="Brief description of this template"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <Input
              label="Email Subject"
              placeholder={"e.g., Boost {{company_name}}'s Online Presence"}
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Body
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={8}
                placeholder={"Hi {{first_name}},\n\nI noticed {{company_name}} has great reviews..."}
                value={formData.body}
                onChange={(e) => setFormData({ ...formData, body: e.target.value })}
              />
              <p className="text-xs text-gray-500 mt-1">
                Use variables: {'{{company_name}}, {{first_name}}, {{your_company}}'}</p>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="use_ai"
                checked={formData.use_ai_personalization}
                onChange={(e) => setFormData({ ...formData, use_ai_personalization: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="use_ai" className="text-sm text-gray-700 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" />
                Enable AI Personalization
              </label>
            </div>

            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setIsCreateModalOpen(false)}
              >
                Cancel
              </Button>
              <Button className="flex-1" onClick={handleCreateTemplate}>
                Create Template
              </Button>
            </div>
          </div>
        </Modal>

        {/* Edit Template Modal */}
        <Modal
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false)
            setSelectedTemplate(null)
          }}
          title="Edit Email Template"
        >
          <div className="space-y-4">
            <Input
              label="Template Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <Input
              label="Email Subject"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Body
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={8}
                value={formData.body}
                onChange={(e) => setFormData({ ...formData, body: e.target.value })}
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="use_ai_edit"
                checked={formData.use_ai_personalization}
                onChange={(e) => setFormData({ ...formData, use_ai_personalization: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="use_ai_edit" className="text-sm text-gray-700 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" />
                Enable AI Personalization
              </label>
            </div>

            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setIsEditModalOpen(false)
                  setSelectedTemplate(null)
                }}
              >
                Cancel
              </Button>
              <Button className="flex-1" onClick={handleUpdateTemplate}>
                Update Template
              </Button>
            </div>
          </div>
        </Modal>

        {/* View Template Modal */}
        <Modal
          isOpen={isViewModalOpen}
          onClose={() => {
            setIsViewModalOpen(false)
            setSelectedTemplate(null)
          }}
          title="View Email Template"
        >
          {selectedTemplate && (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Template Name</p>
                <p className="text-gray-900">{selectedTemplate.name}</p>
              </div>

              {selectedTemplate.description && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Description</p>
                  <p className="text-gray-900">{selectedTemplate.description}</p>
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Subject</p>
                <p className="text-gray-900 bg-gray-50 p-3 rounded border">
                  {selectedTemplate.subject}
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Body</p>
                <pre className="text-sm text-gray-900 bg-gray-50 p-3 rounded border whitespace-pre-wrap font-sans">
                  {selectedTemplate.body}
                </pre>
              </div>

              <div className="flex items-center gap-2 pt-2">
                {selectedTemplate.use_ai_personalization && (
                  <span className="flex items-center gap-1 text-sm text-purple-600">
                    <Sparkles className="w-4 h-4" />
                    AI Personalization Enabled
                  </span>
                )}
              </div>

              <div className="text-xs text-gray-600 space-y-1 pt-2 border-t">
                <p>Used {selectedTemplate.times_used} times</p>
                <p>Created: {formatDate(selectedTemplate.created_at)}</p>
                <p>Updated: {formatDate(selectedTemplate.updated_at)}</p>
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setIsViewModalOpen(false)
                    handleEditTemplate(selectedTemplate)
                  }}
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </Button>
                <Button
                  className="flex-1"
                  onClick={() => {
                    setIsViewModalOpen(false)
                    setSelectedTemplate(null)
                  }}
                >
                  Close
                </Button>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </DashboardLayout>
  )
}
