import { apiClient } from './client'
import type { AuditLog } from '../types'

export async function listAuditLogs(): Promise<AuditLog[]> {
  const { data } = await apiClient.get<{ items: AuditLog[] }>('/audit/')
  return data.items ?? []
}

export async function getRequestAuditLogs(requestId: number): Promise<AuditLog[]> {
  const { data } = await apiClient.get<AuditLog[]>(`/audit/requests/${requestId}`)
  return data
}
