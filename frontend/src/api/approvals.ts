import { apiClient } from './client'
import type { ApprovalDecision } from '../types'

export async function decide(requestId: number, body: ApprovalDecision) {
  const { data } = await apiClient.post(`/approvals/${requestId}/decide`, body)
  return data
}
