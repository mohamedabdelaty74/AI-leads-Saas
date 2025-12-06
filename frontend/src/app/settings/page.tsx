'use client'

import React, { useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { toast } from '@/components/ui/Toast'
import { useTeam } from '@/hooks/useTeam'
import {
  Building2,
  Key,
  Users,
  CreditCard,
  Mail,
  Globe,
  Phone,
  MapPin,
  Eye,
  EyeOff,
  Copy,
  RefreshCw,
  Trash2,
  UserPlus,
  Shield,
  Check,
  Loader2,
  MessageSquare
} from 'lucide-react'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('company')

  // Team management hook
  const { teamMembers, loading: teamLoading, inviteTeamMember, updateTeamMemberRole, removeTeamMember } = useTeam()

  // Company Profile State
  const [companyData, setCompanyData] = useState({
    name: 'Elite Creatif',
    email: 'contact@elitecreatif.com',
    website: 'https://elitecreatif.com',
    phone: '+1 (555) 123-4567',
    address: '123 Business St, San Francisco, CA 94105',
    industry: 'technology',
    company_size: '11-50'
  })

  // API Keys State
  const [apiKeys, setApiKeys] = useState([
    {
      id: '1',
      name: 'Google Maps API',
      key: 'AIzaSyD********************xyz',
      masked: true,
      status: 'active',
      last_used: '2 hours ago'
    },
    {
      id: '2',
      name: 'Hunter.io API',
      key: '3f7a9b********************123',
      masked: true,
      status: 'active',
      last_used: '1 day ago'
    },
    {
      id: '3',
      name: 'SMTP Credentials',
      key: 'smtp.gmail.com:587',
      masked: false,
      status: 'active',
      last_used: '5 hours ago'
    }
  ])

  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')

  // WhatsApp Settings State
  const [whatsappPhoneId, setWhatsappPhoneId] = useState('')
  const [whatsappToken, setWhatsappToken] = useState('')
  const [whatsappTokenVisible, setWhatsappTokenVisible] = useState(false)
  const [verifyingWhatsapp, setVerifyingWhatsapp] = useState(false)
  const [whatsappVerified, setWhatsappVerified] = useState(false)
  const [savingWhatsapp, setSavingWhatsapp] = useState(false)

  const industryOptions = [
    { value: 'technology', label: 'Technology' },
    { value: 'finance', label: 'Finance' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'education', label: 'Education' },
    { value: 'retail', label: 'Retail' },
    { value: 'other', label: 'Other' }
  ]

  const companySizeOptions = [
    { value: '1-10', label: '1-10 employees' },
    { value: '11-50', label: '11-50 employees' },
    { value: '51-200', label: '51-200 employees' },
    { value: '201-500', label: '201-500 employees' },
    { value: '500+', label: '500+ employees' }
  ]

  const roleOptions = [
    { value: 'member', label: 'Member - Can view and generate leads' },
    { value: 'admin', label: 'Admin - Full access except billing' },
    { value: 'owner', label: 'Owner - Full access including billing' }
  ]

  const handleSaveCompanyProfile = () => {
    toast.success('Company profile updated successfully!')
  }

  const handleToggleKeyVisibility = (id: string) => {
    setApiKeys(apiKeys.map(key =>
      key.id === id ? { ...key, masked: !key.masked } : key
    ))
  }

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    toast.success('API key copied to clipboard')
  }

  const handleRegenerateKey = (id: string) => {
    toast.promise(
      new Promise(resolve => setTimeout(resolve, 1000)),
      {
        loading: 'Regenerating API key...',
        success: 'API key regenerated successfully!',
        error: 'Failed to regenerate API key'
      }
    )
  }

  const handleDeleteKey = (id: string) => {
    setApiKeys(apiKeys.filter(key => key.id !== id))
    toast.success('API key deleted')
  }

  const handleInviteTeamMember = async () => {
    if (!inviteEmail.trim()) {
      toast.error('Please enter an email address')
      return
    }

    if (!/\S+@\S+\.\S+/.test(inviteEmail)) {
      toast.error('Please enter a valid email address')
      return
    }

    const result = await inviteTeamMember({
      email: inviteEmail,
      role: inviteRole
    })

    if (result.success) {
      setInviteEmail('')
      setInviteRole('member')
    }
  }

  const handleRemoveTeamMember = async (id: string) => {
    await removeTeamMember(id)
  }

  const handleChangeRole = async (id: string, newRole: string) => {
    await updateTeamMemberRole(id, newRole)
  }

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'owner':
        return 'primary'
      case 'admin':
        return 'info'
      default:
        return 'default'
    }
  }

  const handleVerifyWhatsapp = async () => {
    if (!whatsappPhoneId.trim() || !whatsappToken.trim()) {
      toast.error('Please enter both Phone Number ID and Access Token')
      return
    }

    try {
      setVerifyingWhatsapp(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/settings/whatsapp-credentials/verify`, {
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

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Verification failed')
      }

      const result = await response.json()
      setWhatsappVerified(true)
      toast.success(result.message || 'WhatsApp credentials verified successfully!')
    } catch (error: any) {
      toast.error(error.message || 'Failed to verify WhatsApp credentials')
      setWhatsappVerified(false)
    } finally {
      setVerifyingWhatsapp(false)
    }
  }

  const handleSaveWhatsapp = async () => {
    if (!whatsappVerified) {
      toast.error('Please verify credentials before saving')
      return
    }

    try {
      setSavingWhatsapp(true)
      // Store credentials in localStorage for now (can be moved to backend later)
      localStorage.setItem('whatsapp_phone_id', whatsappPhoneId)
      localStorage.setItem('whatsapp_token', whatsappToken)

      toast.success('WhatsApp credentials saved successfully!')
    } catch (error: any) {
      toast.error('Failed to save WhatsApp credentials')
    } finally {
      setSavingWhatsapp(false)
    }
  }

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          Manage your account settings and preferences
        </p>
      </div>

      {/* Settings Tabs */}
      <Tabs defaultValue="company" onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger
            value="company"
            icon={<Building2 className="h-4 w-4" />}
          >
            Company Profile
          </TabsTrigger>
          <TabsTrigger
            value="api-keys"
            icon={<Key className="h-4 w-4" />}
          >
            API Keys
          </TabsTrigger>
          <TabsTrigger
            value="team"
            icon={<Users className="h-4 w-4" />}
          >
            Team
          </TabsTrigger>
          <TabsTrigger
            value="whatsapp"
            icon={<MessageSquare className="h-4 w-4" />}
          >
            WhatsApp
          </TabsTrigger>
          <TabsTrigger
            value="billing"
            icon={<CreditCard className="h-4 w-4" />}
          >
            Billing
          </TabsTrigger>
        </TabsList>

        {/* Company Profile Tab */}
        <TabsContent value="company">
          <Card>
            <CardHeader>
              <CardTitle>Company Information</CardTitle>
              <CardDescription>
                Update your company profile and business details
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input
                    label="Company Name"
                    value={companyData.name}
                    onChange={(e) => setCompanyData({ ...companyData, name: e.target.value })}
                    leftIcon={<Building2 className="h-4 w-4" />}
                    fullWidth
                  />

                  <Input
                    label="Company Email"
                    type="email"
                    value={companyData.email}
                    onChange={(e) => setCompanyData({ ...companyData, email: e.target.value })}
                    leftIcon={<Mail className="h-4 w-4" />}
                    fullWidth
                  />

                  <Input
                    label="Website"
                    type="url"
                    value={companyData.website}
                    onChange={(e) => setCompanyData({ ...companyData, website: e.target.value })}
                    leftIcon={<Globe className="h-4 w-4" />}
                    fullWidth
                  />

                  <Input
                    label="Phone Number"
                    type="tel"
                    value={companyData.phone}
                    onChange={(e) => setCompanyData({ ...companyData, phone: e.target.value })}
                    leftIcon={<Phone className="h-4 w-4" />}
                    fullWidth
                  />
                </div>

                <Input
                  label="Business Address"
                  value={companyData.address}
                  onChange={(e) => setCompanyData({ ...companyData, address: e.target.value })}
                  leftIcon={<MapPin className="h-4 w-4" />}
                  fullWidth
                />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Select
                    label="Industry"
                    options={industryOptions}
                    value={companyData.industry}
                    onChange={(e) => setCompanyData({ ...companyData, industry: e.target.value })}
                    fullWidth
                  />

                  <Select
                    label="Company Size"
                    options={companySizeOptions}
                    value={companyData.company_size}
                    onChange={(e) => setCompanyData({ ...companyData, company_size: e.target.value })}
                    fullWidth
                  />
                </div>

                <div className="flex justify-end pt-4 border-t border-gray-200">
                  <Button
                    variant="primary"
                    onClick={handleSaveCompanyProfile}
                  >
                    Save Changes
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys">
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>
                Manage your API keys for external services
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {apiKeys.map((apiKey) => (
                  <div
                    key={apiKey.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-semibold text-gray-900">{apiKey.name}</h4>
                        <Badge
                          variant={apiKey.status === 'active' ? 'success' : 'default'}
                          size="sm"
                        >
                          {apiKey.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 mb-1">
                        <code className="text-sm text-gray-600 font-mono">
                          {apiKey.masked
                            ? apiKey.key
                            : 'AIzaSyDmJ8KLqRx9F3tNv2p5Y7zM4wQ6xC8bE1f'}
                        </code>
                        <button
                          onClick={() => handleToggleKeyVisibility(apiKey.id)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          {apiKey.masked ? (
                            <Eye className="h-4 w-4" />
                          ) : (
                            <EyeOff className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleCopyKey(apiKey.key)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                      </div>
                      <p className="text-xs text-gray-500">
                        Last used: {apiKey.last_used}
                      </p>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        leftIcon={<RefreshCw className="h-4 w-4" />}
                        onClick={() => handleRegenerateKey(apiKey.id)}
                      >
                        Regenerate
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteKey(apiKey.id)}
                      >
                        <Trash2 className="h-4 w-4 text-error-500" />
                      </Button>
                    </div>
                  </div>
                ))}

                <div className="pt-4 border-t border-gray-200">
                  <Button
                    variant="outline"
                    leftIcon={<Key className="h-4 w-4" />}
                  >
                    Add New API Key
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* API Configuration Guide */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Configuration Guide</CardTitle>
              <CardDescription>
                How to set up your API keys
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-semibold">
                    1
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Google Maps API</h4>
                    <p className="text-sm text-gray-600">
                      Get your API key from{' '}
                      <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                        Google Cloud Console
                      </a>
                      . Enable Places API and Geocoding API.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-semibold">
                    2
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Hunter.io API</h4>
                    <p className="text-sm text-gray-600">
                      Sign up at{' '}
                      <a href="https://hunter.io" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                        hunter.io
                      </a>
                      {' '}and get your API key from the dashboard.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-semibold">
                    3
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">SMTP Configuration</h4>
                    <p className="text-sm text-gray-600">
                      Use your email provider's SMTP settings. For Gmail, enable "Less secure app access" or use App Passwords.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Team Tab */}
        <TabsContent value="team">
          <Card>
            <CardHeader>
              <CardTitle>Team Members</CardTitle>
              <CardDescription>
                Manage your team and their permissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Invite Section */}
                <div className="p-4 bg-primary-50 rounded-lg border border-primary-200">
                  <h4 className="font-semibold text-gray-900 mb-3">Invite Team Member</h4>
                  <div className="flex gap-3">
                    <Input
                      placeholder="email@company.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      leftIcon={<Mail className="h-4 w-4" />}
                      fullWidth
                    />
                    <Select
                      options={roleOptions.slice(0, 2)}
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                    />
                    <Button
                      variant="primary"
                      leftIcon={<UserPlus className="h-4 w-4" />}
                      onClick={handleInviteTeamMember}
                    >
                      Invite
                    </Button>
                  </div>
                </div>

                {/* Loading State */}
                {teamLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
                  </div>
                ) : (
                  /* Team Members List */
                  <div className="space-y-3">
                    {teamMembers.map((member) => {
                      const fullName = member.first_name && member.last_name
                        ? `${member.first_name} ${member.last_name}`
                        : member.first_name || member.email.split('@')[0]
                      const initials = member.first_name && member.last_name
                        ? `${member.first_name[0]}${member.last_name[0]}`
                        : fullName.substring(0, 2).toUpperCase()

                      // Calculate relative time for last_login_at
                      const getLastActive = (lastLogin?: string) => {
                        if (!lastLogin) return 'Never'
                        const now = new Date()
                        const loginDate = new Date(lastLogin)
                        const diffMs = now.getTime() - loginDate.getTime()
                        const diffMins = Math.floor(diffMs / 60000)
                        if (diffMins < 1) return 'Active now'
                        if (diffMins < 60) return `${diffMins} minutes ago`
                        const diffHours = Math.floor(diffMins / 60)
                        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
                        const diffDays = Math.floor(diffHours / 24)
                        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
                      }

                      return (
                        <div
                          key={member.id}
                          className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                        >
                          <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold">
                              {initials}
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-900">{fullName}</h4>
                              <p className="text-sm text-gray-600">{member.email}</p>
                              <p className="text-xs text-gray-500 mt-0.5">{getLastActive(member.last_login_at)}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <Badge variant={getRoleBadgeVariant(member.role)}>
                              {member.role}
                            </Badge>

                            {member.role !== 'owner' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRemoveTeamMember(member.id)}
                              >
                                <Trash2 className="h-4 w-4 text-error-500" />
                              </Button>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Permissions Guide */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Role Permissions</CardTitle>
              <CardDescription>
                Understanding team member roles and their access levels
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Shield className="h-5 w-5 text-primary-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Owner</h4>
                    <p className="text-sm text-gray-600">
                      Full access to all features including billing, team management, and settings.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Shield className="h-5 w-5 text-info-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Admin</h4>
                    <p className="text-sm text-gray-600">
                      Can manage campaigns, generate leads, and invite team members. Cannot access billing.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Shield className="h-5 w-5 text-gray-400 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Member</h4>
                    <p className="text-sm text-gray-600">
                      Can view and generate leads, but cannot manage settings or invite others.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* WhatsApp Settings Tab */}
        <TabsContent value="whatsapp">
          <Card>
            <CardHeader>
              <CardTitle>WhatsApp Business API</CardTitle>
              <CardDescription>
                Configure WhatsApp Business API credentials to send messages to your leads
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Instructions */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex gap-3">
                    <MessageSquare className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-blue-900 mb-1">How to get WhatsApp Business API credentials</h4>
                      <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                        <li>Create a Meta Developer account at <a href="https://developers.facebook.com" target="_blank" rel="noopener noreferrer" className="underline">developers.facebook.com</a></li>
                        <li>Create a new app and add WhatsApp Business product</li>
                        <li>Get your Phone Number ID from the WhatsApp dashboard</li>
                        <li>Generate an access token with messaging permissions</li>
                      </ol>
                    </div>
                  </div>
                </div>

                {/* Phone Number ID */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number ID *
                  </label>
                  <Input
                    type="text"
                    value={whatsappPhoneId}
                    onChange={(e) => {
                      setWhatsappPhoneId(e.target.value)
                      setWhatsappVerified(false)
                    }}
                    placeholder="123456789012345"
                    icon={<Phone className="h-4 w-4" />}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Find this in your WhatsApp Business API dashboard
                  </p>
                </div>

                {/* Access Token */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Access Token *
                  </label>
                  <div className="relative">
                    <Input
                      type={whatsappTokenVisible ? 'text' : 'password'}
                      value={whatsappToken}
                      onChange={(e) => {
                        setWhatsappToken(e.target.value)
                        setWhatsappVerified(false)
                      }}
                      placeholder="EAAxxxxxxxxxxxxxxxxxxxxxxxxxx"
                      icon={<Key className="h-4 w-4" />}
                    />
                    <button
                      type="button"
                      onClick={() => setWhatsappTokenVisible(!whatsappTokenVisible)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {whatsappTokenVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Generate a permanent access token from your Meta app settings
                  </p>
                </div>

                {/* Verification Status */}
                {whatsappVerified && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-600" />
                    <div>
                      <p className="font-medium text-green-900">Credentials Verified</p>
                      <p className="text-sm text-green-700">Your WhatsApp Business API credentials are valid</p>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3 pt-4 border-t border-gray-200">
                  <Button
                    onClick={handleVerifyWhatsapp}
                    disabled={verifyingWhatsapp || !whatsappPhoneId || !whatsappToken}
                    variant="outline"
                    leftIcon={verifyingWhatsapp ? <Loader2 className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
                  >
                    {verifyingWhatsapp ? 'Verifying...' : 'Verify Credentials'}
                  </Button>
                  <Button
                    onClick={handleSaveWhatsapp}
                    disabled={!whatsappVerified || savingWhatsapp}
                    leftIcon={savingWhatsapp ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  >
                    {savingWhatsapp ? 'Saving...' : 'Save Credentials'}
                  </Button>
                </div>

                {/* Usage Info */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-6">
                  <h4 className="font-semibold text-gray-900 mb-2">Usage Information</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>• These credentials will be used to send WhatsApp messages to your leads</p>
                    <p>• Messages are sent via the WhatsApp Cloud API</p>
                    <p>• Standard WhatsApp Business API rates apply</p>
                    <p>• Ensure your WhatsApp Business account is approved for messaging</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Billing Tab */}
        <TabsContent value="billing">
          <Card>
            <CardHeader>
              <CardTitle>Billing & Subscription</CardTitle>
              <CardDescription>
                Manage your subscription plan and payment methods
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Current Plan */}
                <div className="p-6 bg-gradient-to-r from-primary-500 to-primary-700 rounded-lg text-white">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-2xl font-bold">Pro Plan</h3>
                      <p className="text-primary-100 mt-1">$99/month</p>
                    </div>
                    <Badge variant="success" className="bg-white text-success-700">
                      Active
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-primary-400">
                    <div>
                      <p className="text-primary-100 text-sm">Leads Quota</p>
                      <p className="text-xl font-semibold">10,000/mo</p>
                    </div>
                    <div>
                      <p className="text-primary-100 text-sm">Renewal Date</p>
                      <p className="text-xl font-semibold">Feb 15, 2024</p>
                    </div>
                  </div>
                </div>

                {/* Usage */}
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3">Usage This Month</h4>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-600">Leads Generated</span>
                        <span className="font-semibold text-gray-900">7,482 / 10,000</span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-600 rounded-full"
                          style={{ width: '74.82%' }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-600">Emails Sent</span>
                        <span className="font-semibold text-gray-900">5,247 / Unlimited</span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-success-600 rounded-full" style={{ width: '100%' }} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Plan Options */}
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3">Available Plans</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 border border-gray-200 rounded-lg">
                      <h5 className="font-semibold text-gray-900 mb-2">Starter</h5>
                      <p className="text-2xl font-bold text-gray-900 mb-3">$29<span className="text-sm text-gray-600">/mo</span></p>
                      <ul className="space-y-2 text-sm text-gray-600 mb-4">
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-success-600" />
                          1,000 leads/mo
                        </li>
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-success-600" />
                          Basic support
                        </li>
                      </ul>
                      <Button variant="outline" size="sm" className="w-full">
                        Downgrade
                      </Button>
                    </div>

                    <div className="p-4 border-2 border-primary-600 rounded-lg bg-primary-50">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-semibold text-gray-900">Pro</h5>
                        <Badge variant="primary" size="sm">Current</Badge>
                      </div>
                      <p className="text-2xl font-bold text-gray-900 mb-3">$99<span className="text-sm text-gray-600">/mo</span></p>
                      <ul className="space-y-2 text-sm text-gray-600 mb-4">
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-success-600" />
                          10,000 leads/mo
                        </li>
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-success-600" />
                          Priority support
                        </li>
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-success-600" />
                          AI personalization
                        </li>
                      </ul>
                      <Button variant="primary" size="sm" className="w-full" disabled>
                        Current Plan
                      </Button>
                    </div>

                    <div className="p-4 border border-gray-200 rounded-lg">
                      <h5 className="font-semibold text-gray-900 mb-2">Enterprise</h5>
                      <p className="text-2xl font-bold text-gray-900 mb-3">$299<span className="text-sm text-gray-600">/mo</span></p>
                      <ul className="space-y-2 text-sm text-gray-600 mb-4">
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-success-600" />
                          Unlimited leads
                        </li>
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-success-600" />
                          Dedicated support
                        </li>
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-success-600" />
                          Custom integrations
                        </li>
                      </ul>
                      <Button variant="primary" size="sm" className="w-full">
                        Upgrade
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Payment Method */}
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3">Payment Method</h4>
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-8 bg-gray-900 rounded flex items-center justify-center text-white text-xs font-bold">
                        VISA
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">•••• •••• •••• 4242</p>
                        <p className="text-sm text-gray-600">Expires 12/25</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      Update
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  )
}
