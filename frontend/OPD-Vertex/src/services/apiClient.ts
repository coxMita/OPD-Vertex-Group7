import axios from 'axios'
import { keycloak } from './keycloak'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

// Add a request interceptor to attach the Keycloak token
apiClient.interceptors.request.use(async (config) => {
  if (keycloak && keycloak.token) {
    try {
      await keycloak.updateToken(30)
    } catch (error) {
      console.error('Failed to refresh Keycloak token, using existing token', error)
    }
    if (keycloak.token) {
      config.headers.set('Authorization', `Bearer ${keycloak.token}`)
    }
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

export default apiClient
