// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Keycloak from 'keycloak-js'

const kc = new Keycloak({
  url: 'http://localhost:8180',
  realm: 'opd-vertex',
  clientId: 'opd-vertex-frontend',
})

let _initPromise: Promise<boolean> | null = null

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const authenticated = ref(false)
  const roles = ref<string[]>([])
  const doctorId = ref<string | null>(null)
  const userProfile = ref<{
    username?: string
    email?: string
    firstName?: string
    lastName?: string
  } | null>(null)
  const isInitialized = ref(false)

  let refreshTimer: ReturnType<typeof setTimeout> | null = null

  const isDoctor = computed(() => roles.value.includes('doctor'))
  const isNurse = computed(() => roles.value.includes('nurse'))

  // ── Init ────────────────────────────────────────────────────
  async function init(): Promise<boolean> {
    if (_initPromise) return _initPromise

    _initPromise = kc
      .init({
        onLoad: 'check-sso',
        pkceMethod: 'S256',
        checkLoginIframe: false,
      })
      .then(async (isAuthenticated) => {
        if (isAuthenticated) {
          await syncFromKeycloak()
          scheduleRefresh()
        }
        kc.onTokenExpired = () => refreshToken()
        isInitialized.value = true
        return isAuthenticated
      })
      .catch((error) => {
        console.error('Keycloak init failed:', error)
        isInitialized.value = true
        return false
      })

    return _initPromise
  }

  // ── Login ───────────────────────────────────────────────────
  async function login() {
    await kc.login({
      redirectUri: window.location.origin + '/doctor',
    })
  }

  // ── Logout ──────────────────────────────────────────────────
  async function logout() {
    stopRefreshTimer()
    clearLocalState()
    await kc.logout({
      redirectUri: window.location.origin + '/',
    })
  }

  // ── Sync state din Keycloak ─────────────────────────────────
  async function syncFromKeycloak() {
    token.value = kc.token ?? null
    authenticated.value = kc.authenticated ?? false

    const realmRoles = kc.realmAccess?.roles ?? []
    roles.value = realmRoles.filter((r) =>
      ['doctor', 'nurse', 'patient'].includes(r),
    )

    try {
      const profile = await kc.loadUserProfile()
      userProfile.value = {
        username: profile.username,
        email: profile.email,
        firstName: profile.firstName,
        lastName: profile.lastName,
      }
    } catch {
      console.warn('Could not load user profile')
    }

    // Dacă e doctor, fetch doctor_id din user-service
    if (roles.value.includes('doctor') && kc.tokenParsed?.sub) {
      try {
        const { userApi } = await import('@/services/userApi')
        const doctor = await userApi.getDoctorByKeycloakId(kc.tokenParsed.sub)
        doctorId.value = doctor.doctor_id
      } catch {
        console.warn('Could not fetch doctor profile')
      }
    }
  }

  // ── Token refresh ───────────────────────────────────────────
  async function refreshToken() {
    try {
      const refreshed = await kc.updateToken(30)
      if (refreshed) {
        token.value = kc.token ?? null
      }
    } catch {
      console.warn('Token refresh failed, logging out')
      await logout()
    }
  }

  function scheduleRefresh() {
    stopRefreshTimer()
    const exp = kc.tokenParsed?.exp ?? 0
    const now = Math.ceil(Date.now() / 1000)
    const delay = Math.max((exp - now - 60) * 1000, 10_000)
    refreshTimer = setTimeout(refreshToken, delay)
  }

  function stopRefreshTimer() {
    if (refreshTimer) {
      clearTimeout(refreshTimer)
      refreshTimer = null
    }
  }

  function clearLocalState() {
    token.value = null
    authenticated.value = false
    roles.value = []
    doctorId.value = null
    userProfile.value = null
  }

  function getToken(): string | null {
    return kc.token ?? null
  }

  return {
    token,
    authenticated,
    roles,
    userProfile,
    doctorId,
    isInitialized,
    isDoctor,
    isNurse,
    init,
    login,
    logout,
    getToken,
    refreshToken,
  }
})