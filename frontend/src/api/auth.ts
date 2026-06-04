import { apiClient } from './client'
import type { Token } from '../types'

export async function login(email: string, password: string): Promise<Token> {
  const { data } = await apiClient.post<Token>('/auth/login', { email, password })
  return data
}
