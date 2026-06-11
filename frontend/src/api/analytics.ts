import { apiClient } from './client'
import type { SpendGroup, CategorySummary } from '../types'

export async function getSpendByCategory(): Promise<SpendGroup[]> {
  const res = await apiClient.get<SpendGroup[]>('/analytics/spend')
  return res.data
}

export async function getCategorySummaries(): Promise<CategorySummary[]> {
  const res = await apiClient.get<CategorySummary[]>('/analytics/categories')
  return res.data
}
