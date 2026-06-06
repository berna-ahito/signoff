import { renderHook, act } from '@testing-library/react'
import { useAuth } from '../hooks/useAuth'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('starts unauthenticated when no token in localStorage', () => {
    const { result } = renderHook(() => useAuth())
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.role).toBeNull()
  })

  it('sets authenticated state after successful login', async () => {
    const payload = btoa(JSON.stringify({ role: 'requester', user_id: 1, exp: 9999999999 }))
    const fakeToken = `header.${payload}.sig`
    vi.mocked(authApi.login).mockResolvedValue({ access_token: fakeToken, token_type: 'bearer' })

    const { result } = renderHook(() => useAuth())
    await act(async () => {
      await result.current.login('alice@test.com', 'alice123')
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.role).toBe('requester')
  })

  it('clears state on logout', async () => {
    const payload = btoa(JSON.stringify({ role: 'requester', user_id: 1, exp: 9999999999 }))
    const fakeToken = `header.${payload}.sig`
    localStorage.setItem('access_token', fakeToken)

    const { result } = renderHook(() => useAuth())
    act(() => {
      result.current.logout()
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
