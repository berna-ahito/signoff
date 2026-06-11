import { createElement, createContext, useCallback, useContext, useEffect, useState } from 'react'
import { login as apiLogin, apiLogout, refreshToken as apiRefresh } from '../api/auth'
import { authStore } from '../lib/authStore'
import type { Role } from '../types'

interface JwtPayload {
  role: Role
  user_id: number
  exp: number
}

function parseJwt(token: string): JwtPayload | null {
  try {
    return JSON.parse(atob(token.split('.')[1])) as JwtPayload
  } catch {
    return null
  }
}

interface AuthContextValue {
  token: string | null
  role: Role | null
  userId: number | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<Role | null>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(null)
  const [role, setRole] = useState<Role | null>(null)
  const [userId, setUserId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  function applyToken(accessToken: string) {
    const payload = parseJwt(accessToken)
    authStore.setAccessToken(accessToken)
    setToken(accessToken)
    setRole(payload?.role ?? null)
    setUserId(payload?.user_id ?? null)
  }

  function clearAuth() {
    authStore.setAccessToken(null)
    setToken(null)
    setRole(null)
    setUserId(null)
  }

  useEffect(() => {
    authStore.onRefreshed(applyToken)
    authStore.onLogout(clearAuth)
    return () => {
      authStore.onRefreshed(null)
      authStore.onLogout(null)
    }
  })

  useEffect(() => {
    const stored = localStorage.getItem('refresh_token')
    if (!stored) {
      setIsLoading(false)
      return
    }
    apiRefresh(stored)
      .then((data) => {
        applyToken(data.access_token)
      })
      .catch(() => {
        localStorage.removeItem('refresh_token')
      })
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string): Promise<Role | null> => {
    const data = await apiLogin(email, password)
    localStorage.setItem('refresh_token', data.refresh_token)
    applyToken(data.access_token)
    return parseJwt(data.access_token)?.role ?? null
  }, [])

  const logout = useCallback(async (): Promise<void> => {
    const stored = localStorage.getItem('refresh_token')
    if (stored) {
      try {
        await apiLogout(stored)
      } catch {
        // best-effort
      }
    }
    localStorage.removeItem('refresh_token')
    clearAuth()
  }, [])

  return createElement(
    AuthContext.Provider,
    { value: { token, role, userId, isAuthenticated: !!token, isLoading, login, logout } },
    children,
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
