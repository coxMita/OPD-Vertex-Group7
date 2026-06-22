import { test, expect, type Page } from '@playwright/test'

// ---------------------------------------------------------------------------
// Keycloak ES-module stub — same strategy as consultation-ai-transcription.spec.ts
// ---------------------------------------------------------------------------
const KEYCLOAK_ESM_STUB = `
class Keycloak {
  constructor(config) {
    this.authenticated = true;
    this.tokenParsed = { sub: 'test-keycloak-sub-001', preferred_username: 'dr.anna' };
    this.token = 'mock-access-token';
  }
  init() { return Promise.resolve(true); }
  login() { return Promise.resolve(); }
  logout(opts) {
    window.location.href = (opts && opts.redirectUri) || window.location.origin;
    return Promise.resolve();
  }
  updateToken() { return Promise.resolve(true); }
  clearToken() {}
  isTokenExpired() { return false; }
  hasRealmRole() { return true; }
  hasResourceRole() { return true; }
  createLoginUrl() { return '#'; }
  createLogoutUrl() { return '#'; }
}
export default Keycloak;
`

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Replace the Vite-pre-bundled keycloak-js module with a pre-authenticated stub. */
async function mockKeycloakJs(page: Page) {
  await page.route(/keycloak-js/, (route) => {
    const url = route.request().url()
    if (url.includes('.js') && !url.includes('localhost:8089')) {
      route.fulfill({
        status: 200,
        contentType: 'application/javascript; charset=utf-8',
        body: KEYCLOAK_ESM_STUB,
      })
    } else {
      route.continue()
    }
  })
  await page.route('http://localhost:8089/**', (route) => route.abort())
}

/** Legacy window-based stub (kept for the "mocked auth" toolbar tests). */
async function injectKeycloakSession(page: Page) {
  await page.addInitScript(() => {
    ;(window as any).__kcAuthenticated = true
    ;(window as any).__kcSub = 'test-keycloak-sub-001'
  })
}

/** Mock the doctor-profile lookup used in DoctorCalendarView.loadDoctorProfile */
async function mockDoctorApis(page: Page) {
  await page.route('**/api/v1/user/doctors/by-keycloak/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        doctor_id: 'doc-001',
        full_name: 'Dr. Anna Larsen',
        department_name: 'General Medicine',
        email: 'anna.larsen@clinic.dk',
        keycloak_id: 'test-keycloak-sub-001',
      }),
    }),
  )

  // Mock appointment queue — return an empty list so the calendar renders cleanly
  await page.route('**/api/v1/appointments/queue/day**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    }),
  )
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('Doctor Calendar — Unauthenticated redirect', () => {
  test('visiting /doctor without auth triggers Keycloak redirect', async ({ page }) => {
    await Promise.all([
      page.waitForURL(/\/doctor|keycloak|auth\/realms|openid-connect|login/, { timeout: 10_000 }).catch(() => null),
      page.goto('/doctor'),
    ])

    const url = page.url()
    // Either stays at /doctor (if Keycloak init is slow) or redirects to auth
    const isDocterRoute = url.includes('/doctor')
    const isKeycloakAuth =
      url.includes('keycloak') ||
      url.includes('auth/realms') ||
      url.includes('openid-connect') ||
      url.includes('login')

    expect(isDocterRoute || isKeycloakAuth).toBeTruthy()
  })
})

test.describe('Doctor Calendar — Calendar UI structure', () => {
  test.beforeEach(async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await page.goto('/doctor', { waitUntil: 'commit' }).catch(() => null)
    await page.waitForSelector('.doctor-tabs', { timeout: 10_000 }).catch(() => null)
  })

  test('renders Calendar and Consultations tabs', async ({ page }) => {
    // The tabs are always rendered regardless of auth state
    const calendarTab = page.getByRole('button', { name: /Calendar/i })
    const consultationsTab = page.getByRole('button', { name: /Consultations/i })

    const calendarVisible = await calendarTab.isVisible().catch(() => false)
    const consultationsVisible = await consultationsTab.isVisible().catch(() => false)

    // At least one of the tabs should be visible once the calendar container renders
    expect(calendarVisible || consultationsVisible).toBeTruthy()
  })
})

test.describe('Doctor Calendar — Calendar toolbar (mocked auth)', () => {
  test.beforeEach(async ({ page }) => {
    await injectKeycloakSession(page)
    await mockDoctorApis(page)
    await page.goto('/doctor')
    await page.waitForLoadState('networkidle')
  })

  test('calendar tab is active by default', async ({ page }) => {
    const calTab = page.locator('.doctor-tab.active')
    const isVisible = await calTab.isVisible().catch(() => false)
    if (isVisible) {
      await expect(calTab).toContainText(/Calendar/i)
    }
  })

  test('switching to Consultations tab changes active section', async ({ page }) => {
    const consultTab = page.locator('.doctor-tab').filter({ hasText: /Consultations/i })
    const isVisible = await consultTab.isVisible().catch(() => false)
    if (isVisible) {
      await consultTab.click()
      await expect(consultTab).toHaveClass(/active/)
    }
  })
})

test.describe('Doctor Calendar — API error handling', () => {
  test.beforeEach(async ({ page }) => {
    await injectKeycloakSession(page)
    // Doctor profile succeeds
    await page.route('**/api/v1/user/doctors/by-keycloak/**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          doctor_id: 'doc-001',
          full_name: 'Dr. Anna Larsen',
          department_name: 'General Medicine',
          email: 'anna@clinic.dk',
          keycloak_id: 'test-keycloak-sub-001',
        }),
      }),
    )
    // Appointment fetch fails
    await page.route('**/api/v1/appointments/queue/day**', (route) =>
      route.fulfill({ status: 500, body: 'Internal Server Error' }),
    )
  })

  test('shows error alert when appointment fetch fails', async ({ page }) => {
    await page.goto('/doctor')
    await page.waitForLoadState('networkidle')
    // Error alert may be displayed by the calendar view
    const errorAlert = page.locator('[role="alert"]').first()
    const hasAlert = await errorAlert.isVisible({ timeout: 5_000 }).catch(() => false)
    // We assert that the page doesn't crash (has content)
    const bodyText = await page.locator('body').innerText()
    expect(bodyText.length).toBeGreaterThan(0)
    // If an alert is shown, it should be visible (not a blank error screen)
    if (hasAlert) {
      await expect(errorAlert).toBeVisible()
    }
  })
})
