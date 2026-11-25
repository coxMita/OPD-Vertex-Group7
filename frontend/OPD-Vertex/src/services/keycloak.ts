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
  // No onLoad: an existing Keycloak session is NOT picked up silently.
  // The app is only authenticated right after returning from the login page,
  // so every visit to /doctor or /admin asks for credentials again.
  initPromise = keycloak.init({
    checkLoginIframe: false,
  }).then(() => {
    keycloakReady = true
  })
  return initPromise
}

/**
 * Make sure the user logged in on this page load. If not, send them to the
 * Keycloak login form (always shown, even if Keycloak still has a session)
 * and come back to `path` afterwards.
 *
 * Returns true when the page can continue, false when a redirect started.
 */
export async function requireLogin(path: string): Promise<boolean> {
  await initKeycloak()
  if (keycloak.authenticated) return true
  await keycloak.login({
    redirectUri: `${window.location.origin}${path}`,
    prompt: 'login',
  })
  return false
}

/** Display name of the logged-in user from the Keycloak token. */
export function tokenDisplayName(): string {
  const t = keycloak.tokenParsed as
    | { name?: string; given_name?: string; family_name?: string; preferred_username?: string }
    | undefined
  if (!t) return ''
  return (
    t.name ||
    [t.given_name, t.family_name].filter(Boolean).join(' ') ||
    t.preferred_username ||
    ''
  )
}
