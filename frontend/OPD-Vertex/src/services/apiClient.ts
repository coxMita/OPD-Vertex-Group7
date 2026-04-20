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
      // Refresh the token if it expires in the next 30 seconds
      await keycloak.updateToken(30)
      config.headers.set('Authorization', `Bearer ${keycloak.token}`)
    } catch (error) {
      console.error('Failed to update Keycloak token', error)
      // Optionally handle forced logout here
      // keycloak.login()
    }
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

export default apiClient
