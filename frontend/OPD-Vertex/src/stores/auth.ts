import { defineStore } from 'pinia'
import Keycloak from 'keycloak-js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    keycloakManager: null as Keycloak | null,
    isAuthenticated: false,
    userProfile: null as any | null,
  }),
  actions: {
    async init() {
      const keycloak = new Keycloak({
        url: 'http://localhost:8089',
        realm: 'opd-vertex',
        clientId: 'vue-app',
      })

      try {
        const authenticated = await keycloak.init({
          onLoad: 'check-sso',
          silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        })

        this.keycloakManager = keycloak
        this.isAuthenticated = authenticated

        if (authenticated) {
          const profile = await keycloak.loadUserProfile()
          this.userProfile = profile
        }
      } catch (error) {
        console.error('Keycloak authentication failed', error)
      }
    },
    async login() {
      if (this.keycloakManager) {
        await this.keycloakManager.login()
      }
    },
    async logout() {
      if (this.keycloakManager) {
        await this.keycloakManager.logout()
      }
    },
  },
})
