import { test, expect, type Page } from '@playwright/test'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Mock all backend calls needed for a full happy-path booking. */
async function mockBookingApis(page: Page) {
  // GET doctors by department
  await page.route('**/api/v1/user/doctor/*/doctors', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          doctor_id: 'doc-001',
          full_name: 'Dr. Anna Larsen',
          department_name: 'General Medicine',
          email: 'anna.larsen@clinic.dk',
          keycloak_id: 'kc-001',
        },
      ]),
    }),
  )

  // POST find-or-create patient
  await page.route('**/api/v1/user/patients', (route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 201,
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
      })
    } else {
      route.continue()
    }
  })

  // POST create appointment
  await page.route('**/api/v1/appointments', (route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          appointment_id: 'appt-001',
          patient_id: 'pat-001',
          doctor_id: 'doc-001',
          appointment_date: '2026-06-15',
          time_preference: 'AM',
          status: 'scheduled',
          queue_number: 1,
        }),
      })
    } else {
      route.continue()
    }
  })
}

/** Navigate to the patient page with API mocks active. */
async function goToPatient(page: Page) {
  await mockBookingApis(page)
  await page.goto('/patient')
  await page.waitForLoadState('networkidle')
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('Patient Page — Mode Selector', () => {
  test.beforeEach(async ({ page }) => {
    await goToPatient(page)
  })

  test('renders all three mode cards', async ({ page }) => {
    await expect(page.getByText('Book Appointment')).toBeVisible()
    await expect(page.getByText('Check Appointment')).toBeVisible()
    await expect(page.getByText('Cancel Appointment')).toBeVisible()
  })

  test('Book Appointment card is selected by default', async ({ page }) => {
    // The booking form should be visible in default "book" mode
    await expect(page.getByText('New Appointment')).toBeVisible()
    await expect(page.getByText('Fill in your details below')).toBeVisible()
  })

  test('clicking Check Appointment switches to check mode', async ({ page }) => {
    await page.getByText('Check Appointment').click()
    await expect(page.getByText('Check Appointment').first()).toBeVisible()
    // LookupForm is shown instead of BookingForm
    await expect(page.getByText('New Appointment')).not.toBeVisible()
  })

  test('clicking Cancel Appointment switches to cancel mode', async ({ page }) => {
    await page.getByText('Cancel Appointment').click()
    await expect(page.getByText('New Appointment')).not.toBeVisible()
  })
})

test.describe('Patient Page — Booking Form', () => {
  test.beforeEach(async ({ page }) => {
    await goToPatient(page)
  })

  test('renders all personal information fields', async ({ page }) => {
    await expect(page.getByLabel('First Name')).toBeVisible()
    await expect(page.getByLabel('Last Name')).toBeVisible()
    await expect(page.getByLabel('Phone Number')).toBeVisible()
    await expect(page.getByLabel('Email')).toBeVisible()
    await expect(page.getByLabel('Date of Birth')).toBeVisible()
  })

  test('renders appointment detail fields', async ({ page }) => {
    await expect(page.getByLabel('Preferred Date')).toBeVisible()
    await expect(page.getByLabel('Reason for Visit')).toBeVisible()
    // AM / PM toggle buttons
    await expect(page.getByRole('button', { name: /AM/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /PM/i })).toBeVisible()
  })

  test('renders the Confirm Booking submit button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Confirm Booking/i })).toBeVisible()
  })

  test('AM/PM toggle works correctly', async ({ page }) => {
    const pmBtn = page.getByRole('button', { name: /PM/i })
    await pmBtn.click()
    // Vuetify 4 v-btn-toggle marks the active button with v-btn--active class, not aria-pressed
    await expect(pmBtn).toHaveClass(/v-btn--active/)
  })

  test('fills out and submits the full booking form successfully', async ({ page }) => {
    await page.getByLabel('First Name').fill('Maria')
    await page.getByLabel('Last Name').fill('Andersen')
    await page.getByLabel('Phone Number').fill('4512345678')
    await page.getByLabel('Email').fill('maria@example.com')
    await page.getByLabel('Date of Birth').fill('1990-05-15')
    await page.getByLabel('Preferred Date').fill('2026-06-15')
    await page.getByLabel('Reason for Visit').fill('General checkup')

    await page.getByRole('button', { name: /Confirm Booking/i }).click()

    // After successful submission the SuccessState component is shown
    await expect(page.getByText(/booking confirmed|appointment confirmed|success/i)).toBeVisible({
      timeout: 8000,
    })
  })

  test('shows error alert when API returns 409 (no slots available)', async ({ page }) => {
    // Override the appointment creation route to return 409
    await page.route('**/api/v1/appointments', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'No available slots' }),
        })
      } else {
        route.continue()
      }
    })

    await page.getByLabel('First Name').fill('Maria')
    await page.getByLabel('Last Name').fill('Andersen')
    await page.getByLabel('Phone Number').fill('4512345678')
    await page.getByLabel('Email').fill('maria@example.com')
    await page.getByLabel('Date of Birth').fill('1990-05-15')
    await page.getByLabel('Preferred Date').fill('2026-06-15')

    await page.getByRole('button', { name: /Confirm Booking/i }).click()

    await expect(
      page.getByText(/No available slots for this doctor on the selected date/i),
    ).toBeVisible({ timeout: 8000 })
  })

  test('shows generic error message on unexpected API failure', async ({ page }) => {
    await page.route('**/api/v1/user/patients', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({ status: 500, body: 'Internal Server Error' })
      } else {
        route.continue()
      }
    })

    await page.getByLabel('First Name').fill('Maria')
    await page.getByLabel('Last Name').fill('Andersen')
    await page.getByLabel('Phone Number').fill('4512345678')
    await page.getByLabel('Email').fill('maria@example.com')
    await page.getByLabel('Date of Birth').fill('1990-05-15')
    await page.getByLabel('Preferred Date').fill('2026-06-15')

    await page.getByRole('button', { name: /Confirm Booking/i }).click()

    await expect(
      page.getByText(/Booking failed. Please check your details and try again./i),
    ).toBeVisible({ timeout: 8000 })
  })
})

test.describe('Patient Page — Check Appointment Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock OTP send
    await page.route('**/api/v1/user/patients/by-email**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          patient_id: 'pat-001',
          first_name: 'Maria',
          last_name: 'Andersen',
          email: 'maria@example.com',
          date_of_birth: '1990-05-15',
          gender: 'female',
          phone_number: 4512345678,
        }),
      }),
    )
    await page.goto('/patient')
    await page.waitForLoadState('networkidle')
    await page.getByText('Check Appointment').click()
  })

  test('shows the lookup form when check mode is selected', async ({ page }) => {
    // LookupForm should render an email / contact input
    await expect(page.getByRole('textbox')).toBeVisible()
  })
})

test.describe('Patient Page — Navigation', () => {
  test('back-to-home button navigates back to /', async ({ page }) => {
    await page.goto('/patient')
    await page.getByRole('button', { name: /Back to Home/i }).click()
    await expect(page).toHaveURL('/')
  })
})
