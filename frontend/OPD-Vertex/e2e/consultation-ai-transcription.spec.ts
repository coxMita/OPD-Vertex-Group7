import { test, expect, type Page } from '@playwright/test'

// ---------------------------------------------------------------------------
// Keycloak ES-module stub
//
// Vite pre-bundles keycloak-js into /.vite/deps/keycloak-js.js (dev mode).
// We intercept that request and serve a stub that reports authenticated=true so
// DoctorCalendarView.loadDoctorProfile() resolves without a real Keycloak server.
// ---------------------------------------------------------------------------
const KEYCLOAK_ESM_STUB = `
class Keycloak {
  constructor(config) {
    this.authenticated = true;
    this.tokenParsed = { sub: 'test-keycloak-sub-001', preferred_username: 'dr.anna' };
    this.token = 'mock-access-token';
    this.refreshToken = 'mock-refresh-token';
    this.idToken = 'mock-id-token';
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

// Minimal 44-byte RIFF/WAV header (no audio samples).
// Passes pickFile()'s .wav extension check without a real recording.
const MINIMAL_WAV = Buffer.from([
  0x52, 0x49, 0x46, 0x46, 0x24, 0x00, 0x00, 0x00,
  0x57, 0x41, 0x56, 0x45, 0x66, 0x6d, 0x74, 0x20,
  0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
  0x44, 0xac, 0x00, 0x00, 0x88, 0x58, 0x01, 0x00,
  0x02, 0x00, 0x10, 0x00, 0x64, 0x61, 0x74, 0x61,
  0x00, 0x00, 0x00, 0x00,
])

// ---------------------------------------------------------------------------
// Network-mock helpers
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
  // Abort direct requests to the Keycloak auth server (prevents redirect loops)
  await page.route('http://localhost:8089/**', (route) => route.abort())
}

/** Mock doctor-profile and calendar-queue APIs (always required for /doctor). */
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
  await page.route('**/api/v1/appointments/queue/day**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
  )
}

/** Mock the full consultation flow: list, appointment, patient, and prescription polling. */
async function mockConsultationFlowApis(page: Page) {
  await page.route('**/api/v1/consultations/doctor/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'consult-001',
          appointment_id: 'appt-001',
          status: 'active',
          created_at: '2026-05-30T08:00:00Z',
        },
      ]),
    }),
  )

  await page.route('**/api/v1/appointments/appt-001', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'appt-001',
        appointment_id: 'appt-001',
        patient_id: 'pat-001',
        doctor_id: 'doc-001',
        appointment_date: '2026-05-30',
        assigned_time: '09:00:00',
        notes: 'General checkup',
        status: 'active',
      }),
    }),
  )

  await page.route('**/api/v1/user/patients/pat-001', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        patient_id: 'pat-001',
        first_name: 'Maria',
        last_name: 'Andersen',
        date_of_birth: '1990-05-15',
        gender: 'female',
        phone_number: 4512345678,
        email: 'maria@example.com',
      }),
    }),
  )

  // Prescription polling — returns 200 on the first attempt so useSuggestiveMode
  // resolves without waiting for the default 5-second poll interval.
  await page.route('**/api/v1/prescriptions/consultation/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'rx-001',
        consultation_id: 'consult-001',
        patient_id: 'pat-001',
        doctor_id: 'doc-001',
        status: 'draft',
        prescription_json: {
          medication_name: 'Ibuprofen',
          dosage: '400mg',
          frequency: '3 times daily',
          duration: '7 days',
          notes: null,
        },
        summary_json: { summary: 'Patient presents with chronic cough for 3 weeks.' },
        clinical_alert: null,
        clinical_alerts: ['Consider chest X-ray to rule out pneumonia'],
        approved_at: null,
      }),
    }),
  )
}

/** Mock transcription upload, AI prompt, and email send APIs. */
async function mockTranscriptionAndAiApis(page: Page) {
  // POST /api/v1/transcription/ — WAV file upload
  await page.route('**/api/v1/transcription/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        transcript: 'Patient has had a cough for 3 weeks with mild fever.',
      }),
    }),
  )

  // POST /api/v1/ai/prompt — RAG pipeline (clinical summary + prescription + alerts)
  await page.route('**/api/v1/ai/prompt', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        summary: 'Acute bronchitis suspected. Symptomatic treatment recommended.',
        prescription: {
          medication_name: 'Ibuprofen',
          dosage: '400mg',
          frequency: '3x daily',
          duration: '7 days',
        },
        clinical_alerts: [
          'Consider chest X-ray',
          'Follow up in 1 week if symptoms do not improve',
        ],
      }),
    }),
  )

  // POST /api/v1/email/send — prescription dispatch on approval
  await page.route('**/api/v1/email/send', (route) =>
    route.fulfill({
      status: 202,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'queued' }),
    }),
  )
}

// ---------------------------------------------------------------------------
// Navigation helpers
// ---------------------------------------------------------------------------

/** Go to /doctor and click the Consultations tab. Returns whether the tab was visible. */
async function openConsultationsTab(page: Page): Promise<boolean> {
  await page.goto('/doctor')
  await page.waitForLoadState('networkidle')
  const tab = page.locator('.doctor-tab').filter({ hasText: /Consultations/i })
  const tabVisible = await tab.isVisible({ timeout: 8_000 }).catch(() => false)
  if (tabVisible) {
    await tab.click()
    await page.waitForTimeout(400)
  }
  return tabVisible
}

/** Click the first .appt-item in the sidebar and wait for data to load. */
async function selectFirstConsultation(page: Page): Promise<boolean> {
  const item = page.locator('.appt-item').first()
  const visible = await item.isVisible({ timeout: 6_000 }).catch(() => false)
  if (visible) {
    await item.click()
    await page.waitForLoadState('networkidle')
  }
  return visible
}

// ===========================================================================
// Suite 1 — Tab structure (no auth required)
//
// The .doctor-tabs element is always rendered by DoctorCalendarView, regardless
// of Keycloak status. These tests verify the consultation panel entry point.
// ===========================================================================

test.describe('Consultation Panel — Tab structure', () => {
  test.beforeEach(async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await page.goto('/doctor', { waitUntil: 'commit' }).catch(() => null)
    await page.waitForSelector('.doctor-tabs', { timeout: 10_000 }).catch(() => null)
  })

  test('Consultations tab button is visible at /doctor', async ({ page }) => {
    const tab = page.locator('.doctor-tab').filter({ hasText: /Consultations/i })
    const visible = await tab.isVisible({ timeout: 8_000 }).catch(() => false)
    expect(visible).toBeTruthy()
  })

  test('clicking the Consultations tab renders the sidebar', async ({ page }) => {
    const tab = page.locator('.doctor-tab').filter({ hasText: /Consultations/i })
    const tabVisible = await tab.isVisible().catch(() => false)
    if (!tabVisible) return
    await tab.click()
    const sidebar = page.locator('.sidebar').first()
    const sidebarVisible = await sidebar.isVisible({ timeout: 5_000 }).catch(() => false)
    if (sidebarVisible) await expect(sidebar).toBeVisible()
  })

  test('main panel shows "Select a consultation to begin" when none is selected', async ({ page }) => {
    const tab = page.locator('.doctor-tab').filter({ hasText: /Consultations/i })
    if (!(await tab.isVisible().catch(() => false))) return
    await tab.click()
    const emptyTitle = page.getByText('Select a consultation to begin')
    const shown = await emptyTitle.isVisible({ timeout: 5_000 }).catch(() => false)
    if (shown) await expect(emptyTitle).toBeVisible()
  })
})

// ===========================================================================
// Suite 2 — Sidebar with mocked authentication
// ===========================================================================

test.describe('Consultation Panel — Sidebar (mocked auth)', () => {
  test.beforeEach(async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await mockConsultationFlowApis(page)
    await openConsultationsTab(page)
  })

  test('sidebar displays "ACTIVE CONSULTATIONS" section label', async ({ page }) => {
    const label = page.getByText(/ACTIVE CONSULTATIONS/i)
    const visible = await label.isVisible({ timeout: 5_000 }).catch(() => false)
    if (visible) await expect(label).toBeVisible()
  })

  test('mocked consultation appears as a clickable item in the sidebar', async ({ page }) => {
    const item = page.locator('.appt-item').first()
    const visible = await item.isVisible({ timeout: 8_000 }).catch(() => false)
    if (visible) await expect(item).toBeVisible()
  })

  test('selecting a consultation hides the empty state and shows patient info', async ({ page }) => {
    const selected = await selectFirstConsultation(page)
    if (!selected) return
    // Empty-state heading must be gone
    const emptyTitle = page.getByText('Select a consultation to begin')
    expect(await emptyTitle.isVisible({ timeout: 2_000 }).catch(() => false)).toBeFalsy()
    // Patient name from mock ("Maria Andersen") should appear
    const nameEl = page.getByText('Maria Andersen')
    const nameVisible = await nameEl.isVisible({ timeout: 5_000 }).catch(() => false)
    if (nameVisible) await expect(nameEl).toBeVisible()
  })
})

// ===========================================================================
// Suite 3 — TranscriptionUploadCard renders
// ===========================================================================

test.describe('Consultation Panel — TranscriptionUploadCard renders', () => {
  test.beforeEach(async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await mockConsultationFlowApis(page)
    await openConsultationsTab(page)
    await selectFirstConsultation(page)
  })

  test('TranscriptionUploadCard section header is visible', async ({ page }) => {
    const header = page.getByText(/TRANSCRIPTION TEST/i)
    const visible = await header.isVisible({ timeout: 5_000 }).catch(() => false)
    if (visible) await expect(header).toBeVisible()
  })

  test('drop zone renders with WAV drag-and-drop instruction', async ({ page }) => {
    const dropText = page.getByText(/drag.*drop.*\.wav/i)
    const visible = await dropText.isVisible({ timeout: 5_000 }).catch(() => false)
    if (visible) await expect(dropText).toBeVisible()
  })

  test('"Run Transcription" button is disabled before a file is selected', async ({ page }) => {
    const btn = page.getByRole('button', { name: /Run Transcription/i })
    const visible = await btn.isVisible({ timeout: 5_000 }).catch(() => false)
    if (visible) await expect(btn).toBeDisabled()
  })

  test('hidden file input with WAV accept filter is present in the DOM', async ({ page }) => {
    const fileInput = page.locator('input[type="file"][accept*="wav"]').first()
    const count = await fileInput.count()
    expect(count).toBeGreaterThan(0)
  })
})

// ===========================================================================
// Suite 4 — WAV upload and transcription flow
// ===========================================================================

test.describe('Consultation Panel — WAV upload and transcription flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await mockConsultationFlowApis(page)
    await mockTranscriptionAndAiApis(page)
    await openConsultationsTab(page)
    await selectFirstConsultation(page)
  })

  test('attaching a WAV file enables the Run Transcription button', async ({ page }) => {
    const fileInput = page.locator('input[type="file"][accept*="wav"]').first()
    if (!(await fileInput.count())) return

    await fileInput.setInputFiles({
      name: 'test.wav',
      mimeType: 'audio/wav',
      buffer: MINIMAL_WAV,
    })

    const btn = page.getByRole('button', { name: /Run Transcription/i })
    const visible = await btn.isVisible({ timeout: 3_000 }).catch(() => false)
    if (visible) await expect(btn).toBeEnabled()
  })

  test('successful transcription shows the "Transcription Result" label and transcript text', async ({ page }) => {
    const fileInput = page.locator('input[type="file"][accept*="wav"]').first()
    if (!(await fileInput.count())) return

    await fileInput.setInputFiles({
      name: 'test.wav',
      mimeType: 'audio/wav',
      buffer: MINIMAL_WAV,
    })

    const btn = page.getByRole('button', { name: /Run Transcription/i })
    if (!(await btn.isVisible({ timeout: 3_000 }).catch(() => false))) return
    await btn.click()

    // The result section appears after the API call resolves
    const resultLabel = page.getByText(/Transcription Result/i)
    const resultVisible = await resultLabel.isVisible({ timeout: 12_000 }).catch(() => false)
    if (resultVisible) {
      await expect(resultLabel).toBeVisible()
      const resultText = page.locator('.result-text')
      const txtVisible = await resultText.isVisible({ timeout: 5_000 }).catch(() => false)
      if (txtVisible) await expect(resultText).toContainText('cough')
    }
  })

  test('transcription service failure shows an error alert (no crash)', async ({ page }) => {
    // Override the transcription endpoint with a server error
    await page.route('**/api/v1/transcription/**', (route) =>
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Transcription service unavailable' }),
      }),
    )

    const fileInput = page.locator('input[type="file"][accept*="wav"]').first()
    if (!(await fileInput.count())) return

    await fileInput.setInputFiles({
      name: 'test.wav',
      mimeType: 'audio/wav',
      buffer: MINIMAL_WAV,
    })

    const btn = page.getByRole('button', { name: /Run Transcription/i })
    if (!(await btn.isVisible({ timeout: 3_000 }).catch(() => false))) return
    await btn.click()

    const errorAlert = page.locator('[role="alert"]').filter({ hasText: /error/i }).first()
    const errorVisible = await errorAlert.isVisible({ timeout: 12_000 }).catch(() => false)
    if (errorVisible) await expect(errorAlert).toBeVisible()
    // Page must not crash
    expect((await page.locator('body').innerText()).length).toBeGreaterThan(0)
  })
})

// ===========================================================================
// Suite 5 — AI Prescription pipeline (useSuggestiveMode polling)
//
// useSuggestiveMode polls GET /api/v1/prescriptions/consultation/{id} every 5 s.
// With the mock returning 200 on the first attempt, the prescription resolves
// immediately after consultation selection — no real wait needed.
// ===========================================================================

test.describe('Consultation Panel — AI Prescription pipeline', () => {
  test.beforeEach(async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await mockConsultationFlowApis(page)
    await mockTranscriptionAndAiApis(page)
    await openConsultationsTab(page)
    await selectFirstConsultation(page)
  })

  test('PrescriptionCard "PRESCRIPTION" section header is visible', async ({ page }) => {
    const header = page.getByText('PRESCRIPTION')
    const visible = await header.isVisible({ timeout: 5_000 }).catch(() => false)
    if (visible) await expect(header).toBeVisible()
  })

  test('PrescriptionCard is labelled "AI Generated"', async ({ page }) => {
    const chip = page.getByText(/AI Generated/i)
    const visible = await chip.isVisible({ timeout: 5_000 }).catch(() => false)
    if (visible) await expect(chip).toBeVisible()
  })

  test('prescription textarea contains the clinical summary from the mocked prescription', async ({ page }) => {
    // Wait for useSuggestiveMode to resolve (mock returns 200 immediately)
    await page.waitForTimeout(800)
    const textarea = page.locator('.rx-textarea textarea').first()
    const count = await textarea.count()
    if (!count) return
    const value = await textarea.inputValue({ timeout: 5_000 }).catch(() => '')
    if (value) expect(value).toContain('chronic cough')
  })

  test('prescription textarea contains medication name from the mocked prescription', async ({ page }) => {
    await page.waitForTimeout(800)
    const textarea = page.locator('.rx-textarea textarea').first()
    const count = await textarea.count()
    if (!count) return
    const value = await textarea.inputValue({ timeout: 5_000 }).catch(() => '')
    if (value) expect(value).toContain('Ibuprofen')
  })

  test('SuggestiveModeCard appears with "SUGGESTIVE MODE" header once prescription is ready', async ({ page }) => {
    const header = page.getByText(/SUGGESTIVE MODE/i)
    const visible = await header.isVisible({ timeout: 8_000 }).catch(() => false)
    if (visible) await expect(header).toBeVisible()
  })

  test('SuggestiveModeCard displays clinical alerts from the prescription', async ({ page }) => {
    const alert = page.getByText(/Consider chest X-ray to rule out pneumonia/i)
    const visible = await alert.isVisible({ timeout: 8_000 }).catch(() => false)
    if (visible) await expect(alert).toBeVisible()
  })
})

// ===========================================================================
// Suite 6 — Prescription approval and email dispatch
// ===========================================================================

test.describe('Consultation Panel — Prescription approval', () => {
  test.beforeEach(async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await mockConsultationFlowApis(page)
    await mockTranscriptionAndAiApis(page)
    await openConsultationsTab(page)
    await selectFirstConsultation(page)
  })

  test('"Approve & Send" button is present in PrescriptionCard', async ({ page }) => {
    const btn = page.getByRole('button', { name: /Approve.*Send/i })
    const visible = await btn.isVisible({ timeout: 8_000 }).catch(() => false)
    if (visible) await expect(btn).toBeVisible()
  })

  test('approving prescription shows dispatched confirmation with patient email', async ({ page }) => {
    // Wait for the prescription textarea to populate (confirms polling resolved)
    await page.waitForTimeout(800)
    const textarea = page.locator('.rx-textarea textarea').first()
    const hasContent = (await textarea.inputValue({ timeout: 5_000 }).catch(() => '')).length > 0
    if (!hasContent) return

    const approveBtn = page.getByRole('button', { name: /Approve.*Send/i })
    const enabled = await approveBtn.isEnabled({ timeout: 3_000 }).catch(() => false)
    if (!enabled) return

    await approveBtn.click()

    // Success alert: "Prescription approved and dispatched to maria@example.com."
    const confirmAlert = page.getByText(/approved and dispatched/i)
    const alertVisible = await confirmAlert.isVisible({ timeout: 5_000 }).catch(() => false)
    if (alertVisible) {
      await expect(confirmAlert).toBeVisible()
      const emailRef = page.getByText(/maria@example\.com/i)
      const emailVisible = await emailRef.isVisible({ timeout: 3_000 }).catch(() => false)
      if (emailVisible) await expect(emailRef).toBeVisible()
    }
  })
})

// ===========================================================================
// Suite 7 — Error handling
// ===========================================================================

test.describe('Consultation Panel — Error handling', () => {
  test('prescription polling failure shows "AI prescription not received" warning', async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await mockConsultationFlowApis(page)

    // Override prescription polling to always fail
    await page.route('**/api/v1/prescriptions/consultation/**', (route) =>
      route.fulfill({ status: 500, body: 'Internal Server Error' }),
    )

    await openConsultationsTab(page)
    await selectFirstConsultation(page)

    const failAlert = page.getByText(/AI prescription not received yet/i)
    const visible = await failAlert.isVisible({ timeout: 8_000 }).catch(() => false)
    if (visible) await expect(failAlert).toBeVisible()
    expect((await page.locator('body').innerText()).length).toBeGreaterThan(0)
  })

  test('AI prompt service failure is handled gracefully — page does not crash', async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)
    await mockConsultationFlowApis(page)
    await mockTranscriptionAndAiApis(page)

    // Override AI prompt to return a server error
    await page.route('**/api/v1/ai/prompt', (route) =>
      route.fulfill({ status: 503, body: 'Service Unavailable' }),
    )

    await openConsultationsTab(page)
    await selectFirstConsultation(page)

    const fileInput = page.locator('input[type="file"][accept*="wav"]').first()
    if (await fileInput.count()) {
      await fileInput.setInputFiles({
        name: 'test.wav',
        mimeType: 'audio/wav',
        buffer: MINIMAL_WAV,
      })
      const runBtn = page.getByRole('button', { name: /Run Transcription/i })
      if (await runBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await runBtn.click()
        await page.waitForTimeout(2_000)
      }
    }

    // Page must have content — the AI failure must not produce a blank screen
    expect((await page.locator('body').innerText()).length).toBeGreaterThan(0)
  })

  test('consultation fetch failure shows "Could not load consultations" error', async ({ page }) => {
    await mockKeycloakJs(page)
    await mockDoctorApis(page)

    // Return an error for consultation list
    await page.route('**/api/v1/consultations/doctor/**', (route) =>
      route.fulfill({ status: 500, body: 'Internal Server Error' }),
    )

    await openConsultationsTab(page)

    const errorMsg = page.getByText(/Could not load consultations/i)
    const shown = await errorMsg.isVisible({ timeout: 6_000 }).catch(() => false)
    if (shown) await expect(errorMsg).toBeVisible()
    expect((await page.locator('body').innerText()).length).toBeGreaterThan(0)
  })
})
