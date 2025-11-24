// API Response Types

export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: number
}

export interface ApiError {
  message: string
  errors?: Record<string, string[]>
  status: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// Authentication
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  first_name?: string
  last_name?: string
  organization_name: string
  company_email?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface User {
  id: string
  email: string
  first_name?: string
  last_name?: string
  role: 'owner' | 'admin' | 'member'
  tenant_id: string
  is_active: boolean
  email_verified: boolean
  created_at: string
  last_login_at?: string
}

// Tenant/Organization
export interface Tenant {
  id: string
  name: string
  company_email?: string
  company_website?: string
  status: 'trial' | 'active' | 'suspended'
  plan: 'starter' | 'pro' | 'enterprise'
  leads_quota: number
  leads_used: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UpdateTenantRequest {
  name?: string
  company_email?: string
  company_website?: string
  company_phone?: string
  company_address?: string
}

// Campaign
export interface Campaign {
  id: string
  tenant_id: string
  name: string
  description?: string
  status: 'draft' | 'active' | 'paused' | 'completed'
  search_query?: string
  lead_source: 'google_maps' | 'linkedin' | 'instagram' | 'manual'
  max_leads: number
  description_style?: 'professional' | 'sales' | 'casual'
  enable_ai_personalization: boolean
  created_at: string
  started_at?: string
  completed_at?: string
  leads_count?: number
}

export interface CreateCampaignRequest {
  name: string
  description?: string
  search_query?: string
  lead_source: 'google_maps' | 'linkedin' | 'instagram' | 'manual'
  max_leads: number
  description_style?: 'professional' | 'sales' | 'casual'
  enable_ai_personalization?: boolean
}

export interface UpdateCampaignRequest {
  name?: string
  description?: string
  status?: 'draft' | 'active' | 'paused' | 'completed'
}

// Campaign Lead
export interface CampaignLead {
  id: string
  campaign_id: string
  title: string
  address?: string
  phone?: string
  website?: string
  email?: string
  description?: string
  lead_score?: number
  generated_email?: string
  generated_whatsapp?: string
  email_sent: boolean
  whatsapp_sent: boolean
  replied: boolean
  contact_source?: string
  scraped_data?: Record<string, any>
  created_at: string
}

export interface CreateLeadRequest {
  title: string
  address?: string
  phone?: string
  website?: string
  email?: string
  description?: string
  contact_source?: string
}

export interface BulkLeadsRequest {
  leads: CreateLeadRequest[]
}

// Analytics
export interface AnalyticsOverview {
  total_leads: number
  total_campaigns: number
  email_sent_count: number
  whatsapp_sent_count: number
  replied_count: number
  email_sent_rate: number
  response_rate: number
  leads_by_source: Record<string, number>
  leads_by_month: Array<{ month: string; count: number }>
}

// Scraper
export interface ScraperRequest {
  query: string
  max_results: number
  location?: string
  source: 'google_maps' | 'linkedin' | 'instagram'
  generate_description?: boolean
  description_style?: 'professional' | 'sales' | 'casual'
}

export interface ScraperResponse {
  leads: CampaignLead[]
  total: number
  source: string
}

// Email/WhatsApp Generation
export interface GenerateEmailRequest {
  leads: Array<{
    company_name: string
    description?: string
    website?: string
  }>
  user_company_info: {
    name: string
    description: string
    contact_email?: string
    signature?: string
  }
  custom_instructions?: string
}

export interface GenerateWhatsAppRequest {
  leads: Array<{
    company_name: string
    description?: string
  }>
  user_company_info: {
    name: string
    description: string
  }
  custom_instructions?: string
}

// Message Sending
export interface SendEmailRequest {
  leads: Array<{
    email: string
    subject: string
    body: string
  }>
  smtp_config: {
    host: string
    port: number
    username: string
    password: string
  }
}

export interface SendWhatsAppRequest {
  leads: Array<{
    phone: string
    message: string
  }>
  whatsapp_config: {
    phone_number_id: string
    access_token: string
  }
}
