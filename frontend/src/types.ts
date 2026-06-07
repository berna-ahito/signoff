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

export interface AIReview {
  summary: string
  category: string
  urgency: 'low' | 'medium' | 'high'
  risk_level: 'low' | 'medium' | 'high'
  missing_info: string[]
  recommended_action: 'request_more_info' | 'manager_review' | 'finance_review' | 'ready_for_rfq'
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
