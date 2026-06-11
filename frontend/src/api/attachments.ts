import { apiClient } from './client'
import type { Attachment } from '../types'

export async function listAttachments(requestId: number): Promise<Attachment[]> {
  const { data } = await apiClient.get<Attachment[]>(`/requests/${requestId}/attachments`)
  return data
}

export async function uploadAttachment(requestId: number, file: File): Promise<Attachment> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<Attachment>(`/requests/${requestId}/attachments`, form)
  return data
}

export async function downloadAttachmentBlob(requestId: number, attachmentId: number): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(
    `/requests/${requestId}/attachments/${attachmentId}/download`,
    { responseType: 'blob' },
  )
  return data
}
