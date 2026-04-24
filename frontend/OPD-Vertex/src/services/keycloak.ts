import Keycloak from 'keycloak-js'

export const keycloak = new Keycloak({
  url: 'http://localhost:8089',
  realm: 'opd-vertex',
  clientId: 'vue-app',
})

export let keycloakReady = false

let initPromise: Promise<void> | null = null

export const initKeycloak = () => {
  if (initPromise) return initPromise
  initPromise = keycloak.init({ checkLoginIframe: false }).then(() => {
    keycloakReady = true
  })
  return initPromise
}
