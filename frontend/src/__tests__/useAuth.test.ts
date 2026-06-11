import { renderHook, act, waitFor } from '@testing-library/react'
import { createElement } from 'react'
import { AuthProvider, useAuth } from '../hooks/useAuth'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

const wrapper = ({ children }: { children: React.ReactNode }) =>
  createElement(AuthProvider, null, children)

function makeToken(role: string, user_id = 1): string {
  const payload = btoa(JSON.stringify({ role, user_id, exp: 9999999999 }))
  return `header.${payload}.sig`
}

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('starts unauthenticated and not loading when no refresh_token', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.role).toBeNull()
  })

  it('auto-attempts refresh on mount when refresh_token exists in localStorage', async () => {
    const accessToken = makeToken('manager')
    localStorage.setItem('refresh_token', 'stored-refresh-token')
    vi.mocked(authApi.refreshToken).mockResolvedValue({
      access_token: accessToken,
      token_type: 'bearer',
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.role).toBe('manager')
    expect(authApi.refreshToken).toHaveBeenCalledWith('stored-refresh-token')
  })

  it('stays unauthenticated and clears localStorage when refresh fails on mount', async () => {
    localStorage.setItem('refresh_token', 'expired-token')
    vi.mocked(authApi.refreshToken).mockRejectedValue(new Error('401'))

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.isAuthenticated).toBe(false)
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('sets authenticated state after successful login', async () => {
    const accessToken = makeToken('requester')
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: accessToken,
      token_type: 'bearer',
      refresh_token: 'new-refresh-token',
    })

    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => {
      await result.current.login('alice@test.com', 'alice123')
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.role).toBe('requester')
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token')
  })

  it('stores access token in memory, not localStorage', async () => {
    const accessToken = makeToken('admin')
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: accessToken,
      token_type: 'bearer',
      refresh_token: 'refresh-abc',
    })

    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => {
      await result.current.login('admin@test.com', 'pass')
    })

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(result.current.token).toBe(accessToken)
  })

  it('logout calls apiLogout and clears all state', async () => {
    const accessToken = makeToken('finance')
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: accessToken,
      token_type: 'bearer',
      refresh_token: 'refresh-xyz',
    })
    vi.mocked(authApi.apiLogout).mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => {
      await result.current.login('finance@test.com', 'pass')
    })
    expect(result.current.isAuthenticated).toBe(true)

    await act(async () => {
      await result.current.logout()
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.role).toBeNull()
    expect(result.current.token).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
    expect(authApi.apiLogout).toHaveBeenCalledWith('refresh-xyz')
  })

  it('logout still clears state if apiLogout call fails', async () => {
    const accessToken = makeToken('admin')
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: accessToken,
      token_type: 'bearer',
      refresh_token: 'refresh-fail',
    })
    vi.mocked(authApi.apiLogout).mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => {
      await result.current.login('admin@test.com', 'pass')
    })

    await act(async () => {
      await result.current.logout()
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })
})
