import axios from 'axios'
import { authStore } from '../lib/authStore'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = authStore.getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const retriedConfigs = new WeakSet<object>()

apiClient.interceptors.response.use(
  (res) => res,
  async (err: unknown) => {
    if (!axios.isAxiosError(err)) return Promise.reject(err)

    const config = err.config
    if (err.response?.status === 401 && config && !retriedConfigs.has(config)) {
      retriedConfigs.add(config)
      const storedRefresh = localStorage.getItem('refresh_token')
      if (storedRefresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: storedRefresh,
          })
          authStore.setAccessToken(data.access_token)
          authStore.notifyRefreshed(data.access_token)
          config.headers = config.headers ?? {}
          config.headers['Authorization'] = `Bearer ${data.access_token}`
          return apiClient(config)
        } catch {
          authStore.setAccessToken(null)
          localStorage.removeItem('refresh_token')
          authStore.notifyLogout()
          window.location.href = '/login'
        }
      } else {
        authStore.notifyLogout()
        window.location.href = '/login'
      }
    }

    return Promise.reject(err)
  },
)
