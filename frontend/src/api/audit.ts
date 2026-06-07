import { apiClient } from './client'
import type { AuditLog } from '../types'

export async function listAuditLogs(): Promise<AuditLog[]> {
  const { data } = await apiClient.get<AuditLog[]>('/audit/')
  return data
}
