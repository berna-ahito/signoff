import { apiClient } from './client'
import type { AccessToken, Token } from '../types'

export async function login(email: string, password: string): Promise<Token> {
  const { data } = await apiClient.post<Token>('/auth/login', { email, password })
  return data
}

export async function refreshToken(refresh_token: string): Promise<AccessToken> {
  const { data } = await apiClient.post<AccessToken>('/auth/refresh', { refresh_token })
  return data
}

export async function apiLogout(refresh_token: string): Promise<void> {
  await apiClient.post('/auth/logout', { refresh_token })
}
