// src/services/httpClient.ts
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080'

// ── Client PUBLIC — fără token (pentru pacient) ────────────────
export const publicClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

// ── Client AUTENTIFICAT — cu Bearer token (pentru doctor) ──────
export const authClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

authClient.interceptors.request.use(
  async (config) => {
    const authStore = useAuthStore()
    if (authStore.authenticated) {
      await authStore.refreshToken()
      const token = authStore.getToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error),
)

authClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      await authStore.logout()
    }
    return Promise.reject(error)
  },
)

// Păstrat pentru compatibilitate cu cod vechi dacă există
export const apiClient = authClient