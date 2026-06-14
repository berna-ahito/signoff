import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios, { type AxiosAdapter, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { apiClient } from '../api/client'
import { authStore } from '../lib/authStore'

function make401(config: InternalAxiosRequestConfig): AxiosResponse {
  return { status: 401, statusText: 'Unauthorized', data: {}, headers: {}, config }
}

describe('apiClient 401 interceptor', () => {
  let savedAdapter: typeof apiClient.defaults.adapter

  beforeEach(() => {
    savedAdapter = apiClient.defaults.adapter
    vi.stubGlobal('location', { href: '' })
    localStorage.setItem('refresh_token', 'stored-rt')
  })

  afterEach(() => {
    apiClient.defaults.adapter = savedAdapter
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    localStorage.clear()
    authStore.setAccessToken(null)
  })

  it('calls POST /auth/refresh on 401', async () => {
    let callCount = 0
    apiClient.defaults.adapter = ((config: InternalAxiosRequestConfig) => {
      if (callCount++ === 0) {
        return Promise.reject(
          new axios.AxiosError('Unauthorized', 'ERR_BAD_RESPONSE', config, null, make401(config)),
        )
      }
      return Promise.resolve({
        data: {},
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      } as AxiosResponse)
    }) as unknown as AxiosAdapter

    vi.spyOn(axios, 'post').mockResolvedValueOnce({ data: { access_token: 'new-at' } })

    await apiClient.get('/test')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/auth/refresh'),
      { refresh_token: 'stored-rt' },
    )
  })

  it('retries the original request with the new Bearer token', async () => {
    let callCount = 0
    let lastConfig: InternalAxiosRequestConfig | undefined
    apiClient.defaults.adapter = ((config: InternalAxiosRequestConfig) => {
      lastConfig = config
      if (callCount++ === 0) {
        return Promise.reject(
          new axios.AxiosError('Unauthorized', 'ERR_BAD_RESPONSE', config, null, make401(config)),
        )
      }
      return Promise.resolve({
        data: { ok: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      } as AxiosResponse)
    }) as unknown as AxiosAdapter

    vi.spyOn(axios, 'post').mockResolvedValueOnce({ data: { access_token: 'new-at' } })

    const resp = await apiClient.get('/test')

    expect(resp.data).toEqual({ ok: true })
    const headers = lastConfig?.headers as Record<string, string> | undefined
    expect(headers?.['Authorization']).toBe('Bearer new-at')
  })

  it('redirects to /login when the refresh call fails', async () => {
    apiClient.defaults.adapter = ((config: InternalAxiosRequestConfig) =>
      Promise.reject(
        new axios.AxiosError('Unauthorized', 'ERR_BAD_RESPONSE', config, null, make401(config)),
      )
    ) as unknown as AxiosAdapter

    vi.spyOn(axios, 'post').mockRejectedValueOnce(new Error('network error'))

    await expect(apiClient.get('/test')).rejects.toThrow()
    expect(window.location.href).toBe('/login')
  })

  it('redirects to /login immediately when no refresh token is stored', async () => {
    localStorage.removeItem('refresh_token')
    apiClient.defaults.adapter = ((config: InternalAxiosRequestConfig) =>
      Promise.reject(
        new axios.AxiosError('Unauthorized', 'ERR_BAD_RESPONSE', config, null, make401(config)),
      )
    ) as unknown as AxiosAdapter

    await expect(apiClient.get('/test')).rejects.toThrow()
    expect(window.location.href).toBe('/login')
  })
})

describe('apiClient base URL', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('uses VITE_API_BASE_URL when set', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://custom.api')
    const { apiClient } = await import('../api/client')
    expect(apiClient.defaults.baseURL).toBe('https://custom.api')
  })

  it('falls back to http://localhost:8000 in dev mode when VITE_API_BASE_URL is unset', async () => {
    vi.unstubAllEnvs()
    const { apiClient } = await import('../api/client')
    expect(apiClient.defaults.baseURL).toBe('http://localhost:8000')
  })
})
