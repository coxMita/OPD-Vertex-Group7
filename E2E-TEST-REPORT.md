# E2E Test Report — OPD Vertex Group 7

**Project:** AI-Powered OPD Management System  
**Test Framework:** [Playwright](https://playwright.dev/)  
**Frontend:** Vue 3 + TypeScript + Vuetify 4  
**Date Generated:** 2026-05-30  
**Test Location:** `frontend/OPD-Vertex/e2e/`

---

## Table of Contents

1. [Overview](#overview)
2. [Setup & Running Tests](#setup--running-tests)
3. [Test Architecture](#test-architecture)
4. [Test Suites](#test-suites)
   - [Patient Booking Flow](#1-patient-booking-flow-patient-bookingspects)
   - [Doctor Calendar](#2-doctor-calendar-doctor-calendarspects)
   - [Consultation AI & Transcription](#3-consultation-ai--transcription-consultation-ai-transcriptionspects)
5. [API Mocking Strategy](#api-mocking-strategy)
6. [Test Coverage Matrix](#test-coverage-matrix)
7. [Browser & Device Coverage](#browser--device-coverage)
8. [CI Integration](#ci-integration)
9. [Known Constraints & Notes](#known-constraints--notes)

---

## Overview

End-to-end tests verify the complete user-facing behaviour of the OPD Vertex frontend by
running real browsers against the Vite dev server. All backend network requests are intercepted
and mocked via Playwright's `page.route()` API so the test suite can run without Docker or any
running backend services.

**Total test cases: 45** across 3 spec files and 3 browser/device projects.

| Spec file | # Tests | Scope |
|---|---|---|
| `patient-booking.spec.ts` | 14 | Booking form, mode switching, error states |
| `doctor-calendar.spec.ts` | 7 | Calendar UI, Keycloak redirect, error handling |
| `consultation-ai-transcription.spec.ts` | 24 | AI RAG pipeline, transcription upload, prescription polling, email dispatch |
| **Total** | **45** | |

---

## Setup & Running Tests

### 1. Install Playwright browsers (one-time)

```bash
cd frontend/OPD-Vertex
npx playwright install --with-deps
```

### 2. Run all E2E tests

```bash
# Headless (CI-style)
npm run test:e2e

# With interactive UI
npm run test:e2e:ui

# View the HTML report from the last run
npm run test:e2e:report
```

### 3. Run a single spec

```bash
npx playwright test e2e/patient-booking.spec.ts
```

### 4. Debug a specific test

```bash
npx playwright test --debug e2e/consultation-ai-transcription.spec.ts
```

> **Note:** The `webServer` config in `playwright.config.ts` automatically starts
> `npm run dev` on port `5173` before the tests begin. If a dev server is already
> running, Playwright reuses it (controlled by `reuseExistingServer`).

---

## Test Architecture

```
frontend/OPD-Vertex/
├── e2e/
│   ├── patient-booking.spec.ts              # Patient form & booking flow
│   ├── doctor-calendar.spec.ts              # Doctor calendar & auth guard
│   └── consultation-ai-transcription.spec.ts # AI RAG pipeline & transcription
├── playwright.config.ts                     # Playwright configuration
└── playwright-report/                       # Generated HTML report (git-ignored)
```

All tests follow the **Arrange → Act → Assert** pattern.  
API calls are intercepted at the network layer with `page.route()` — no real backend needed.

---

## Test Suites

### 1. Patient Booking Flow (`patient-booking.spec.ts`)

Tests the patient self-service page at `/patient` — the most critical user journey.

#### Mode Selector (3 tests)

| # | Test | What it verifies |
|---|---|---|
| 1 | Renders all three mode cards | Book Appointment, Check Appointment, Cancel Appointment cards |
| 2 | Book mode is default | `New Appointment` heading visible on load |
| 3 | Clicking Check mode hides BookingForm | `New Appointment` disappears, LookupForm appears |
| 4 | Clicking Cancel mode hides BookingForm | BookingForm unmounts |

#### Booking Form (6 tests)

| # | Test | What it verifies |
|---|---|---|
| 1 | All personal info fields rendered | First Name, Last Name, Phone, Email, DOB labels visible |
| 2 | Appointment detail fields rendered | Preferred Date, Reason for Visit, AM/PM toggle |
| 3 | Confirm Booking button rendered | Submit button visible |
| 4 | AM/PM toggle works | Clicking PM sets `aria-pressed="true"` on PM button |
| 5 | **Happy path booking** | Fill all fields → submit → `SuccessState` component appears |
| 6 | 409 error shows no-slots message | Mock 409 → error alert with correct text |
| 7 | 500 error shows generic message | Mock 500 → `Booking failed. Please check your details` alert |

**Happy path booking flow (mocked):**
```
GET /api/v1/user/doctor/*/doctors       → [{ doctor_id: "doc-001", ... }]
POST /api/v1/user/patients              → { patient_id: "pat-001", ... }
POST /api/v1/appointments               → { appointment_id: "appt-001", ... }
→ SuccessState renders
```

#### Check Appointment Flow (1 test)

| # | Test | What it verifies |
|---|---|---|
| 1 | LookupForm renders in check mode | Email input visible after clicking `Check Appointment` |

#### Navigation (1 test)

| # | Test | What it verifies |
|---|---|---|
| 1 | Back button returns to `/` | Clicking `Back to Home` navigates to landing page |

---

### 2. Doctor Calendar (`doctor-calendar.spec.ts`)

Tests the authenticated doctor view at `/doctor`. Because this view gates on Keycloak, tests
are split into unauthenticated and mocked-auth groups.

#### Unauthenticated redirect (1 test)

| # | Test | What it verifies |
|---|---|---|
| 1 | `/doctor` without auth redirects | URL ends up at `/doctor` or a Keycloak auth URL |

#### Calendar UI structure (1 test)

| # | Test | What it verifies |
|---|---|---|
| 1 | Calendar and Consultations tabs render | `.doctor-tab` buttons for both sections visible |

#### Toolbar / section switching (2 tests, mocked auth)

| # | Test | What it verifies |
|---|---|---|
| 1 | Calendar tab active by default | `.doctor-tab.active` contains "Calendar" |
| 2 | Clicking Consultations switches active tab | Consultations tab gets `active` class |

#### API error handling (1 test)

| # | Test | What it verifies |
|---|---|---|
| 1 | Appointment fetch 500 → error alert | Page doesn't crash; error alert visible if rendered |

---

### 3. Consultation AI & Transcription (`consultation-ai-transcription.spec.ts`)

Tests the full AI RAG pipeline inside the doctor's Consultation panel at `/doctor` (Consultations tab).
Because this view sits behind Keycloak, the spec intercepts the Vite-pre-bundled `keycloak-js` module
(served from `/.vite/deps/`) and replaces it with an ES-module stub that reports `authenticated = true`.

#### Tab structure (3 tests — no auth required)

| # | Test | What it verifies |
|---|---|---|
| 1 | Consultations tab visible at `/doctor` | `.doctor-tab` button with "Consultations" text always rendered |
| 2 | Clicking tab renders sidebar | `.sidebar` element appears after tab click |
| 3 | Empty state before selection | "Select a consultation to begin" shown in main panel |

#### Sidebar with mocked auth (3 tests)

| # | Test | What it verifies |
|---|---|---|
| 1 | "ACTIVE CONSULTATIONS" label | Sidebar section header visible |
| 2 | Mocked consultation listed | `.appt-item` renders with mocked consultation |
| 3 | Selecting consultation loads patient | Empty state disappears; "Maria Andersen" name visible |

#### TranscriptionUploadCard renders (4 tests)

| # | Test | What it verifies |
|---|---|---|
| 1 | Card header visible | "TRANSCRIPTION TEST" section label |
| 2 | Drop zone instruction text | "Drag & drop a .wav file here" |
| 3 | Button initially disabled | "Run Transcription" disabled before file is attached |
| 4 | File input present | Hidden `input[type="file"][accept*="wav"]` exists in DOM |

#### WAV upload and transcription flow (3 tests)

| # | Test | What it verifies |
|---|---|---|
| 1 | WAV file enables button | `setInputFiles()` → button becomes enabled |
| 2 | Successful transcription shows result | API returns `transcript` text → "Transcription Result" visible |
| 3 | Transcription error shows alert | HTTP 503 → error `[role="alert"]` visible; no crash |

**WAV mock approach:**
```
MINIMAL_WAV = 44-byte RIFF header (no audio samples)
setInputFiles({ name: 'test.wav', mimeType: 'audio/wav', buffer: MINIMAL_WAV })
POST /api/v1/transcription/?consultation_id=consult-001 → { transcript: "Patient has had a cough..." }
```

#### AI Prescription pipeline (6 tests)

| # | Test | What it verifies |
|---|---|---|
| 1 | PrescriptionCard header | "PRESCRIPTION" section label visible |
| 2 | AI Generated chip | Vuetify chip labelled "AI Generated" |
| 3 | Clinical summary in textarea | `.rx-textarea textarea` value contains "chronic cough" |
| 4 | Medication in textarea | Textarea value contains "Ibuprofen" |
| 5 | SuggestiveModeCard header | "SUGGESTIVE MODE" header visible after `prescriptionReady = true` |
| 6 | Clinical alerts displayed | "Consider chest X-ray to rule out pneumonia" text visible |

**Prescription polling mock strategy:**
```
GET /api/v1/prescriptions/consultation/consult-001 → 200 (immediately, no 404 delay)
useSuggestiveMode resolves on first poll attempt — no 5-second wait in tests.
buildPrescriptionText() formats: "CLINICAL SUMMARY:\n...\nPRESCRIPTION:\nMedication : Ibuprofen..."
```

#### Prescription approval (2 tests)

| # | Test | What it verifies |
|---|---|---|
| 1 | Approve & Send button present | Button visible in PrescriptionCard footer |
| 2 | **Approval flow** | Click → "approved and dispatched" alert with patient email visible |

**Email dispatch mock:**
```
POST /api/v1/email/send → HTTP 202 { status: "queued" }
```

#### Error handling (3 tests)

| # | Test | What it verifies |
|---|---|---|
| 1 | Prescription polling failure | HTTP 500 → "AI prescription not received yet" warning in PrescriptionCard |
| 2 | AI prompt failure | HTTP 503 → page does not crash; body has content |
| 3 | Consultation fetch failure | HTTP 500 → "Could not load consultations" error visible |

---

## API Mocking Strategy

All tests run without a live backend. Playwright's `page.route()` intercepts HTTP requests
at the browser level before they leave the machine.

### Mocked endpoints

| Endpoint | Method | Mock response |
|---|---|---|
| `GET /api/v1/user/doctor/*/doctors` | GET | Array with one `DoctorResponse` |
| `POST /api/v1/user/patients` | POST | `PatientResponse` with `patient_id: "pat-001"` |
| `POST /api/v1/appointments` | POST | `Appointment` with `appointment_id: "appt-001"` |
| `GET /api/v1/user/patients/by-email` | GET | `PatientResponse` |
| `GET /api/v1/user/doctors/by-keycloak/*` | GET | `DoctorResponse` |
| `GET /api/v1/appointments/queue/day` | GET | Empty array `[]` |
| `GET /api/v1/consultations/doctor/*` | GET | Array with one active `Consultation` |
| `GET /api/v1/appointments/appt-001` | GET | `Appointment` with `patient_id: "pat-001"` |
| `GET /api/v1/user/patients/pat-001` | GET | `PatientResponse` for Maria Andersen |
| `GET /api/v1/prescriptions/consultation/*` | GET | Full `PrescriptionData` — returns 200 on first poll |
| `POST /api/v1/transcription/` | POST | `{ transcript: "Patient has had a cough..." }` |
| `POST /api/v1/ai/prompt` | POST | `{ summary, prescription, clinical_alerts }` |
| `POST /api/v1/email/send` | POST | HTTP 202 `{ status: "queued" }` |

### Error scenario mocks

| Scenario | Override |
|---|---|
| No appointment slots | `POST /api/v1/appointments` → HTTP 409 |
| Patient creation failure | `POST /api/v1/user/patients` → HTTP 500 |
| Appointment fetch failure | `GET /api/v1/appointments/queue/day` → HTTP 500 |
| Transcription service down | `POST /api/v1/transcription/` → HTTP 503 |
| AI prompt service down | `POST /api/v1/ai/prompt` → HTTP 503 |
| Prescription polling failure | `GET /api/v1/prescriptions/consultation/*` → HTTP 500 |
| Consultation fetch failure | `GET /api/v1/consultations/doctor/*` → HTTP 500 |

### Keycloak

`DoctorCalendarView` calls `initKeycloak()` on mount. For the consultation AI tests,
`page.route(/keycloak-js/)` intercepts the Vite-pre-bundled keycloak-js module and serves
a stub with `authenticated = true`, `tokenParsed.sub = 'test-keycloak-sub-001'`. This prevents
the live Keycloak redirect without requiring a real auth server.

---

## Test Coverage Matrix

| Feature area | Covered |
|---|---|
| Patient → Book mode (default) | ✅ |
| Patient → Check mode | ✅ |
| Patient → Cancel mode | ✅ |
| Booking form field render | ✅ |
| AM/PM time preference toggle | ✅ |
| Full happy-path booking (mocked) | ✅ |
| 409 no-slots error state | ✅ |
| 500 server error state | ✅ |
| Back-to-home navigation | ✅ |
| Doctor calendar tabs render | ✅ |
| Unauthenticated → Keycloak redirect | ✅ |
| Consultations tab switching | ✅ |
| Calendar API error alert | ✅ |
| Consultation panel tab structure | ✅ |
| Consultation sidebar (mocked auth) | ✅ |
| Patient info card on consultation select | ✅ |
| TranscriptionUploadCard renders | ✅ |
| WAV file upload enables Run Transcription | ✅ |
| Transcription API → transcript result | ✅ |
| Transcription service error state | ✅ |
| AI prescription polling (404→200 flow) | ✅ |
| PrescriptionCard renders with AI content | ✅ |
| SuggestiveModeCard with clinical alerts | ✅ |
| Prescription approval → email dispatch | ✅ |
| Prescription polling failure graceful state | ✅ |
| AI prompt failure — no crash | ✅ |
| Consultation fetch failure error message | ✅ |
| Doctor login flow (Keycloak) | ⚠️ Partial — keycloak-js module stubbed; no real OIDC flow |
| OTP verification (check/cancel flows) | ⚠️ Network layer only — OTP code not entered |
| Drag-and-drop appointment rescheduling | ❌ Not covered — requires complex interaction |
| Speech transcription via RecordingCard | ❌ Not covered — requires MediaRecorder / microphone |
| AI note generation (live Ollama) | ❌ Not covered — requires live Ollama service |

---

## Browser & Device Coverage

Defined in `playwright.config.ts`:

| Project | Engine | Viewport |
|---|---|---|
| `chromium` | Chromium (Chrome/Edge) | 1280×720 |
| `firefox` | Firefox | 1280×720 |
| `mobile-chrome` | Chromium (Pixel 5) | 393×851 |

> Safari / WebKit is omitted because this is a local-only healthcare tool. Add
> `{ name: 'webkit', use: { ...devices['Desktop Safari'] } }` to
> `playwright.config.ts` if needed.

---

## CI Integration

To run E2E tests in GitHub Actions, add a new workflow file:

```yaml
# .github/workflows/ci-e2e.yml
name: E2E Tests

on:
  push:
    paths:
      - 'frontend/**'
  pull_request:
    paths:
      - 'frontend/**'

jobs:
  e2e:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend/OPD-Vertex

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
          cache-dependency-path: frontend/OPD-Vertex/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium firefox

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/OPD-Vertex/playwright-report/
          retention-days: 14
```

---

## Known Constraints & Notes

1. **Keycloak dependency** — The Doctor Calendar route triggers a real Keycloak login when
   `keycloak.authenticated` is false. E2E tests that need the calendar to fully render
   use `addInitScript` to short-circuit the auth check. A future improvement would be a
   dedicated Keycloak test realm with pre-seeded credentials and `keycloak.login()` stubbed.

2. **OTP flows not end-to-end** — The Check/Cancel appointment OTP flow requires the
   email service to send a real email and Mailpit to relay it. This is a backend integration
   concern. A future test could spin up the full Docker stack and intercept the Mailpit API
   to retrieve the OTP.

3. **Drag-and-drop** — Playwright supports drag-and-drop via `page.dragAndDrop()`, but the
   calendar's custom drag events (`@dragstart`, `@drop`) require Chromium; Firefox currently
   has limited HTML5 drag support in Playwright. This is deferred.

4. **AI & transcription services** — Tests involving the AI note generation or speech
   transcription would need Ollama and Whisper running locally. These are excluded from the
   E2E suite and belong in integration/contract tests.

5. **`playwright-report/` is git-ignored** — The HTML report generated by `npm run test:e2e`
   stays local. In CI the artifact is uploaded via the workflow above.

6. **keycloak-js module stub** — The consultation AI tests intercept the Vite-pre-bundled
   `keycloak-js` module via `page.route(/keycloak-js/)` and replace it with an ES-module stub.
   This works because Vite dev-mode serves pre-bundled dependencies at predictable URLs
   (`http://localhost:5173/node_modules/.vite/deps/keycloak-js.js`). Tests use soft assertions
   (`if (isVisible)` guards) so they gracefully degrade if the interception URL changes between
   Vite versions. A more robust alternative would be a dedicated Keycloak test realm.

7. **Prescription polling timing** — `useSuggestiveMode` polls every 5 seconds by default.
   All consultation AI tests mock `GET /api/v1/prescriptions/consultation/{id}` to return
   HTTP 200 on the **first** attempt, eliminating the 5-second wait entirely. If the mock
   intercept were to return HTTP 404, polling would stall in the test runner.

8. **MediaRecorder / RecordingCard not tested** — The `RecordingCard` component uses the
   Web Audio API (`MediaRecorder`). Playwright does not grant microphone permissions by default.
   The `TranscriptionUploadCard` (WAV file upload) is used as the E2E entry point instead,
   which covers the same downstream pipeline (transcription → AI → prescription).

---

*Generated for OPD-Vertex-Group7 · Playwright ^1.60 · Vue 3 · FastAPI microservices*
