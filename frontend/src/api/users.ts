import { apiClient } from './client'
import type { User, UserCreate } from '../types'

export async function listUsers(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/users/')
  return data
}

export async function createUser(body: UserCreate): Promise<User> {
  const { data } = await apiClient.post<User>('/users/', body)
  return data
}

export async function updateUser(
  id: number,
  body: Partial<{ is_active: boolean; role: string; full_name: string; department_id: number | null }>,
): Promise<User> {
  const { data } = await apiClient.patch<User>(`/users/${id}`, body)
  return data
}
