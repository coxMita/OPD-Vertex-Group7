import Keycloak from 'keycloak-js'

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? 'http://localhost:8089/auth',
  realm: 'opd-vertex',
  clientId: 'vue-app',
})

export let keycloakReady = false

let initPromise: Promise<void> | null = null

export const initKeycloak = () => {
  if (initPromise) return initPromise
  initPromise = keycloak.init({
    onLoad: 'check-sso',
    checkLoginIframe: false,
  }).then(() => {
    keycloakReady = true
  })
  return initPromise
}
