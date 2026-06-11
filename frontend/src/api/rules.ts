import { apiClient } from './client'
import type { ApprovalRule, ApprovalRuleCreate } from '../types'

export async function listRules(): Promise<ApprovalRule[]> {
  const { data } = await apiClient.get<ApprovalRule[]>('/approvals/rules')
  return data
}

export async function createRule(body: ApprovalRuleCreate): Promise<ApprovalRule> {
  const { data } = await apiClient.post<ApprovalRule>('/approvals/rules', body)
  return data
}
