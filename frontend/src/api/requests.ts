import { apiClient } from './client'
import type { AIReview, RequestCreate, RequestDetail, RequestSummary } from '../types'

export async function listRequests(): Promise<RequestSummary[]> {
  const { data } = await apiClient.get<RequestSummary[]>('/requests/')
  return data
}

export async function getRequest(id: number): Promise<RequestDetail> {
  const { data } = await apiClient.get<RequestDetail>(`/requests/${id}`)
  return data
}

export async function createRequest(body: RequestCreate): Promise<RequestDetail> {
  const { data } = await apiClient.post<RequestDetail>('/requests/', body)
  return data
}

export async function submitRequest(id: number): Promise<RequestDetail> {
  const { data } = await apiClient.post<RequestDetail>(`/requests/${id}/submit`)
  return data
}

export async function getAIReview(id: number): Promise<AIReview> {
  const { data } = await apiClient.post<AIReview>(`/requests/${id}/ai-review`)
  return data
}
