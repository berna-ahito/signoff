export type Urgency = 'low' | 'medium' | 'high' | 'critical'
export type RequestStatus =
  | 'draft'
  | 'pending_review'
  | 'pending_approval'
  | 'needs_rule'
  | 'approved'
  | 'rejected'
  | 'needs_more_info'
export type Role = 'requester' | 'manager' | 'finance' | 'admin'
export type Decision = 'approved' | 'rejected' | 'needs_more_info'

export interface Token {
  access_token: string
  token_type: string
  refresh_token: string
}

export interface AccessToken {
  access_token: string
  token_type: string
}

export interface SpendGroup {
  group: string
  count: number
  total_estimated_cost: number
}

export interface CategorySummary {
  category: string
  approved_count: number
  approved_total: number
  pending_count: number
  pending_total: number
}

export interface Attachment {
  id: number
  request_id: number
  filename: string
  content_type: string
  file_size: number
  uploader_id: number
  created_at: string
}

export interface ApprovalRule {
  id: number
  name: string
  category: string | null
  min_amount: number
  max_amount: number | null
  required_role: string
  priority: number
  is_active: boolean
}

export interface ApprovalRuleCreate {
  name: string
  min_amount: number
  max_amount?: number
  category?: string
  required_role: 'manager' | 'finance' | 'admin'
  priority: number
}

export interface RequestSummary {
  id: number
  title: string
  category: string
  urgency: Urgency
  status: RequestStatus
  estimated_cost: number
  requester_id: number
  created_at: string
}

export interface RequestDetail {
  id: number
  title: string
  description: string
  category: string
  urgency: Urgency
  quantity: number
  estimated_cost: number
  vendor_id: number | null
  justification: string
  status: RequestStatus
  requester_id: number
  assigned_role: string | null
  created_at: string
  updated_at: string
}

export interface RequestCreate {
  title: string
  description: string
  category: string
  urgency: Urgency
  quantity: number
  estimated_cost: number
  vendor_id?: number
  justification: string
}

export interface RequestUpdate {
  title?: string
  description?: string
  category?: string
  urgency?: Urgency
  quantity?: number
  estimated_cost?: number
  justification?: string
}

export interface AIReview {
  summary: string
  category: string
  urgency: 'low' | 'medium' | 'high'
  risk_level: 'low' | 'medium' | 'high' | 'unknown'
  missing_info: string[]
  recommended_action: 'approve' | 'reject' | 'request_info' | 'escalate' | 'review'
  rfq_draft: string
  confidence: number
}

export interface ApprovalDecision {
  decision: Decision
  note?: string
}

export interface User {
  id: number
  email: string
  full_name: string
  role: Role
  department_id: number | null
  is_active: boolean
  created_at: string
}

export interface UserCreate {
  email: string
  password: string
  full_name: string
  role: Role
  department_id?: number
}

export interface AuditLog {
  id: number
  request_id: number
  actor_id: number | null
  action: string
  old_status: string | null
  new_status: string | null
  note: string | null
  created_at: string
}
