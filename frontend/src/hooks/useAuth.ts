import { useCallback, useState } from 'react'
import { login as apiLogin } from '../api/auth'
import type { Role } from '../types'

function parseRole(token: string): Role | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.role ?? null
  } catch {
    return null
  }
}

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'))
  const [role, setRole] = useState<Role | null>(() => {
    const t = localStorage.getItem('access_token')
    return t ? parseRole(t) : null
  })

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password)
    const parsedRole = parseRole(data.access_token)
    localStorage.setItem('access_token', data.access_token)
    if (parsedRole) localStorage.setItem('user_role', parsedRole)
    setToken(data.access_token)
    setRole(parsedRole)
    return parsedRole
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_role')
    setToken(null)
    setRole(null)
  }, [])

  return { token, role, isAuthenticated: !!token, login, logout }
}
