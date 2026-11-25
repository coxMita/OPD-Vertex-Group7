<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { requireLogin } from '@/services/keycloak'
import { adminApi } from '@/services/adminApi'
import { appointmentApi } from '@/services/appointmentApi'
import { userApi, type DoctorResponse } from '@/services/userApi'
import { DEPARTMENTS } from '@/composables/useDoctorSelection'
import type {
  Appointment,
  AppointmentStatus,
  TimePreference,
} from '@/models/appointment/appointment.interface'
import type { Consultation } from '@/models/consultation/consultation.interface'

// ── Helpers ──────────────────────────────────────────────────────────────────
function localIsoDate(d = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function errorMessage(err: unknown): string {
  const e = err as { response?: { status?: number; data?: { message?: string; detail?: string } }; message?: string }
  const data = e.response?.data
  return data?.message ?? data?.detail ?? (e.response?.status ? `HTTP ${e.response.status}` : e.message ?? 'Unknown error')
}

// ── State ────────────────────────────────────────────────────────────────────
const ready = ref(false)
const selectedDate = ref(localIsoDate())
const appointments = ref<Appointment[]>([])
const consultations = reactive<Record<string, Consultation | null>>({})
const doctors = ref<DoctorResponse[]>([])
const patientNames = reactive<Record<string, string>>({})
const loading = ref(false)
const busy = ref<string | null>(null)

const snackbar = reactive({ show: false, text: '', color: 'success' })
function notify(text: string, color: 'success' | 'error' | 'info' = 'success') {
  Object.assign(snackbar, { show: true, text, color })
}

const doctorName = (id: string) => doctors.value.find((d) => d.doctor_id === id)?.full_name ?? id.slice(0, 8)

const counts = computed(() => {
  const c = { AM: 0, PM: 0, scheduled: 0, handed_off: 0, completed: 0, cancelled: 0 }
  for (const a of appointments.value) {
    if (a.status === 'scheduled') c[a.time_preference]++
    c[a.status]++
  }
  return c
})

// ── Loading ──────────────────────────────────────────────────────────────────
async function loadDoctors() {
  const results = await Promise.allSettled(DEPARTMENTS.map((d) => userApi.getDoctorsByDepartment(d)))
  doctors.value = results.flatMap((r) => (r.status === 'fulfilled' ? r.value : []))
}

async function loadPatientNames(ids: string[]) {
  const missing = [...new Set(ids)].filter((id) => !(id in patientNames))
  await Promise.allSettled(
    missing.map(async (id) => {
      try {
        const p = await userApi.getPatient(id)
        patientNames[id] = `${p.first_name} ${p.last_name}`
      } catch {
        patientNames[id] = id.slice(0, 8)
      }
    }),
  )
}

async function loadConsultations(list: Appointment[]) {
  await Promise.allSettled(
    list.map(async (a) => {
      try {
        consultations[a.id] = await adminApi.getConsultationForAppointment(a.id)
      } catch {
        consultations[a.id] = null
      }
    }),
  )
}

async function refresh() {
  loading.value = true
  try {
    const list = await adminApi.listAppointments(selectedDate.value || undefined)
    appointments.value = list
    await Promise.all([loadPatientNames(list.map((a) => a.patient_id)), loadConsultations(list)])
  } catch (err) {
    notify(`Could not load appointments: ${errorMessage(err)}`, 'error')
  } finally {
    loading.value = false
  }
}

watch(selectedDate, refresh)

onMounted(async () => {
  if (!(await requireLogin('/admin'))) return
  ready.value = true
  await loadDoctors()
  if (doctors.value.length && !quick.doctorId) quick.doctorId = doctors.value[0]!.doctor_id
  await refresh()
})

// ── Session control ──────────────────────────────────────────────────────────
async function startSession(pref: TimePreference) {
  busy.value = `session-${pref}`
  try {
    const res = await adminApi.startSession(pref, selectedDate.value)
    notify(
      res.handed_off
        ? `${pref} session started — ${res.handed_off} appointment(s) handed off to consultations`
        : `No ${pref} appointments on ${res.appointment_date}`,
      res.handed_off ? 'success' : 'info',
    )
    // consultation-service creates consultations asynchronously via RabbitMQ
    setTimeout(refresh, 800)
  } catch (err) {
    notify(`Start ${pref} failed: ${errorMessage(err)}`, 'error')
  } finally {
    busy.value = null
  }
}

async function setStatus(a: Appointment, status: AppointmentStatus) {
  try {
    await adminApi.setStatus(a.id, status)
    await refresh()
  } catch (err) {
    notify(`Status update failed: ${errorMessage(err)}`, 'error')
  }
}

// ── Quick booking ────────────────────────────────────────────────────────────
const quick = reactive({
  doctorId: '',
  timePreference: 'AM' as TimePreference,
  firstName: 'Demo',
  lastName: 'Patient',
  email: 'demo.patient@example.com',
  dateOfBirth: '1990-01-01',
  gender: 'Male',
  phone: '12345678',
  notes: 'Demo appointment',
  count: 1,
})

async function quickBook() {
  if (!quick.doctorId) return notify('Pick a doctor first', 'error')
  busy.value = 'book'
  try {
    const patient = await userApi.findOrCreatePatient({
      first_name: quick.firstName,
      last_name: quick.lastName,
      date_of_birth: quick.dateOfBirth,
      gender: quick.gender,
      phone_number: quick.phone,
      email: quick.email,
    })
    let ok = 0
    let lastError = ''
    for (let i = 0; i < Math.max(1, quick.count); i++) {
      try {
        await appointmentApi.createAppointment({
          patient_id: patient.patient_id,
          doctor_id: quick.doctorId,
          appointment_date: selectedDate.value,
          time_preference: quick.timePreference,
          notes: quick.notes || null,
        })
        ok++
      } catch (err) {
        lastError = errorMessage(err)
        break
      }
    }
    if (ok) notify(`Booked ${ok} ${quick.timePreference} appointment(s) for ${selectedDate.value}`)
    if (lastError) notify(`Booking stopped: ${lastError}`, 'error')
    await refresh()
  } catch (err) {
    notify(`Booking failed: ${errorMessage(err)}`, 'error')
  } finally {
    busy.value = null
  }
}

// ── Danger zone ──────────────────────────────────────────────────────────────
type ClearTarget = 'appointments' | 'consultations' | 'prescriptions' | 'all'
const confirm = reactive({ show: false, target: 'all' as ClearTarget })

function askClear(target: ClearTarget) {
  Object.assign(confirm, { show: true, target })
}

async function doClear() {
  const target = confirm.target
  confirm.show = false
  busy.value = `clear-${target}`
  const jobs: [string, () => Promise<{ deleted: number }>][] = []
  if (target === 'prescriptions' || target === 'all') jobs.push(['prescriptions', adminApi.clearPrescriptions])
  if (target === 'consultations' || target === 'all') jobs.push(['consultations', adminApi.clearConsultations])
  if (target === 'appointments' || target === 'all') jobs.push(['appointments', adminApi.clearAppointments])

  const parts: string[] = []
  const failures: string[] = []
  for (const [name, fn] of jobs) {
    try {
      const res = await fn()
      parts.push(`${res.deleted ?? '?'} ${name}`)
    } catch (err) {
      failures.push(`${name}: ${errorMessage(err)}`)
    }
  }
  if (parts.length) notify(`Deleted ${parts.join(', ')}`)
  if (failures.length) notify(`Failed — ${failures.join('; ')}`, 'error')
  for (const k of Object.keys(consultations)) delete consultations[k]
  busy.value = null
  await refresh()
}

// ── Table ────────────────────────────────────────────────────────────────────
const headers = [
  { title: 'Date', key: 'appointment_date' },
  { title: 'Time', key: 'assigned_time' },
  { title: 'Slot', key: 'time_preference' },
  { title: 'Doctor', key: 'doctor' },
  { title: 'Patient', key: 'patient' },
  { title: 'Appointment', key: 'status' },
  { title: 'Consultation', key: 'consultation' },
  { title: '', key: 'actions', sortable: false, align: 'end' as const },
]

const STATUS_COLOR: Record<AppointmentStatus, string> = {
  scheduled: 'blue',
  handed_off: 'orange',
  completed: 'green',
  cancelled: 'grey',
}

const links = [
  { title: 'Doctor page', href: '/doctor', icon: 'mdi-stethoscope' },
  { title: 'Patient booking', href: '/patient', icon: 'mdi-account-plus' },
  { title: 'Mailpit', href: 'http://localhost:8025', icon: 'mdi-email-outline' },
  { title: 'RabbitMQ', href: 'http://localhost:9000', icon: 'mdi-rabbit' },
  { title: 'pgAdmin', href: 'http://localhost:5050', icon: 'mdi-database' },
  { title: 'Gateway docs', href: 'http://localhost:8080/docs', icon: 'mdi-api' },
]
</script>

<template>
  <v-container v-if="ready" fluid class="admin pa-4 pa-md-6">
    <div class="d-flex flex-wrap align-center ga-3 mb-4">
      <div>
        <h1 class="text-h5 font-weight-bold">Demo control panel</h1>
        <div class="text-body-2 text-medium-emphasis">
          Book appointments, run the AM/PM session jobs on demand, and reset the data.
        </div>
      </div>
      <v-spacer />
      <v-text-field
        v-model="selectedDate"
        type="date"
        label="Date"
        density="compact"
        variant="outlined"
        hide-details
        style="max-width: 190px"
      />
      <v-btn variant="tonal" size="small" @click="selectedDate = localIsoDate()">Today</v-btn>
      <v-btn variant="text" size="small" @click="selectedDate = ''">All dates</v-btn>
      <v-btn icon="mdi-refresh" variant="text" :loading="loading" @click="refresh" />
    </div>

    <v-row>
      <!-- Session control -->
      <v-col cols="12" md="4">
        <v-card variant="outlined" class="h-100">
          <v-card-title class="d-flex align-center ga-2">
            <v-icon icon="mdi-play-circle-outline" /> Start sessions
          </v-card-title>
          <v-card-text>
            <p class="text-body-2 mb-4">
              Runs the scheduler job now (normally 07:00 / 12:00) for
              <strong>{{ selectedDate || 'today' }}</strong>: creates consultations and marks
              appointments <em>handed_off</em>, so they show up on the doctor page.
            </p>
            <div class="d-flex ga-2">
              <v-btn
                color="primary"
                class="flex-grow-1"
                prepend-icon="mdi-weather-sunset-up"
                :loading="busy === 'session-AM'"
                :disabled="!selectedDate"
                @click="startSession('AM')"
              >
                Start AM
                <v-badge v-if="counts.AM" :content="counts.AM" inline color="white" />
              </v-btn>
              <v-btn
                color="primary"
                class="flex-grow-1"
                prepend-icon="mdi-weather-sunset-down"
                :loading="busy === 'session-PM'"
                :disabled="!selectedDate"
                @click="startSession('PM')"
              >
                Start PM
                <v-badge v-if="counts.PM" :content="counts.PM" inline color="white" />
              </v-btn>
            </div>
            <div v-if="!selectedDate" class="text-caption text-medium-emphasis mt-2">
              Pick a date to start a session.
            </div>
            <div class="d-flex flex-wrap ga-1 mt-4">
              <v-chip size="small" color="blue" variant="tonal">{{ counts.scheduled }} scheduled</v-chip>
              <v-chip size="small" color="orange" variant="tonal">{{ counts.handed_off }} handed off</v-chip>
              <v-chip size="small" color="green" variant="tonal">{{ counts.completed }} completed</v-chip>
              <v-chip size="small" color="grey" variant="tonal">{{ counts.cancelled }} cancelled</v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Quick booking -->
      <v-col cols="12" md="5">
        <v-card variant="outlined" class="h-100">
          <v-card-title class="d-flex align-center ga-2">
            <v-icon icon="mdi-calendar-plus" /> Quick book
          </v-card-title>
          <v-card-text>
            <v-row dense>
              <v-col cols="12" sm="8">
                <v-select
                  v-model="quick.doctorId"
                  :items="doctors"
                  item-title="full_name"
                  item-value="doctor_id"
                  :item-props="(d: DoctorResponse) => ({ subtitle: d.department_name })"
                  label="Doctor"
                  density="compact"
                  variant="outlined"
                  hide-details
                />
              </v-col>
              <v-col cols="12" sm="4">
                <v-btn-toggle v-model="quick.timePreference" mandatory density="compact" variant="outlined" divided class="w-100">
                  <v-btn value="AM" class="flex-grow-1">AM</v-btn>
                  <v-btn value="PM" class="flex-grow-1">PM</v-btn>
                </v-btn-toggle>
              </v-col>
              <v-col cols="6"><v-text-field v-model="quick.firstName" label="First name" density="compact" variant="outlined" hide-details /></v-col>
              <v-col cols="6"><v-text-field v-model="quick.lastName" label="Last name" density="compact" variant="outlined" hide-details /></v-col>
              <v-col cols="12" sm="8"><v-text-field v-model="quick.email" label="Patient email" density="compact" variant="outlined" hide-details /></v-col>
              <v-col cols="12" sm="4"><v-text-field v-model.number="quick.count" type="number" min="1" max="10" label="How many" density="compact" variant="outlined" hide-details /></v-col>
              <v-col cols="12"><v-text-field v-model="quick.notes" label="Notes" density="compact" variant="outlined" hide-details /></v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <span class="text-caption text-medium-emphasis">
              Books for {{ selectedDate || 'a date (pick one)' }}
            </span>
            <v-spacer />
            <v-btn
              color="primary"
              variant="flat"
              prepend-icon="mdi-plus"
              :loading="busy === 'book'"
              :disabled="!selectedDate"
              @click="quickBook"
            >
              Book
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Danger zone + links -->
      <v-col cols="12" md="3">
        <v-card variant="outlined" class="mb-4 danger">
          <v-card-title class="d-flex align-center ga-2 text-error">
            <v-icon icon="mdi-alert-outline" /> Reset data
          </v-card-title>
          <v-card-text class="d-flex flex-column ga-2">
            <v-btn color="error" variant="flat" prepend-icon="mdi-delete-sweep" :loading="busy === 'clear-all'" @click="askClear('all')">
              Delete everything
            </v-btn>
            <v-btn color="error" variant="outlined" size="small" :loading="busy === 'clear-appointments'" @click="askClear('appointments')">Appointments only</v-btn>
            <v-btn color="error" variant="outlined" size="small" :loading="busy === 'clear-consultations'" @click="askClear('consultations')">Consultations only</v-btn>
            <v-btn color="error" variant="outlined" size="small" :loading="busy === 'clear-prescriptions'" @click="askClear('prescriptions')">Prescriptions only</v-btn>
            <div class="text-caption text-medium-emphasis">Patients and doctors are kept.</div>
          </v-card-text>
        </v-card>
        <v-card variant="outlined">
          <v-list density="compact" nav>
            <v-list-subheader>Shortcuts</v-list-subheader>
            <v-list-item
              v-for="l in links"
              :key="l.href"
              :href="l.href"
              :target="l.href.startsWith('http') ? '_blank' : undefined"
              :prepend-icon="l.icon"
              :title="l.title"
            />
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <!-- Appointments table -->
    <v-card variant="outlined" class="mt-4">
      <v-card-title class="d-flex align-center ga-2">
        <v-icon icon="mdi-format-list-bulleted" />
        Appointments {{ selectedDate ? `on ${selectedDate}` : '(all dates)' }}
        <v-chip size="small" variant="tonal">{{ appointments.length }}</v-chip>
      </v-card-title>
      <v-data-table
        :headers="headers"
        :items="appointments"
        :loading="loading"
        density="comfortable"
        items-per-page="25"
        no-data-text="No appointments — book one above."
      >
        <template #[`item.assigned_time`]="{ item }">{{ item.assigned_time?.slice(0, 5) ?? '—' }}</template>
        <template #[`item.doctor`]="{ item }">{{ doctorName(item.doctor_id) }}</template>
        <template #[`item.patient`]="{ item }">{{ patientNames[item.patient_id] ?? '…' }}</template>
        <template #[`item.status`]="{ item }">
          <v-chip size="small" :color="STATUS_COLOR[item.status]" variant="tonal">{{ item.status }}</v-chip>
        </template>
        <template #[`item.consultation`]="{ item }">
          <v-chip v-if="consultations[item.id]" size="small" :color="consultations[item.id]!.status === 'active' ? 'teal' : 'green'" variant="tonal">
            {{ consultations[item.id]!.status }}
          </v-chip>
          <span v-else class="text-medium-emphasis">—</span>
        </template>
        <template #[`item.actions`]="{ item }">
          <v-menu>
            <template #activator="{ props }">
              <v-btn v-bind="props" icon="mdi-dots-vertical" size="small" variant="text" />
            </template>
            <v-list density="compact">
              <v-list-subheader>Set status</v-list-subheader>
              <v-list-item
                v-for="s in (['scheduled', 'handed_off', 'completed', 'cancelled'] as AppointmentStatus[])"
                :key="s"
                :title="s"
                :disabled="item.status === s"
                @click="setStatus(item, s)"
              />
            </v-list>
          </v-menu>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="confirm.show" max-width="420">
      <v-card>
        <v-card-title>Delete {{ confirm.target === 'all' ? 'all demo data' : confirm.target }}?</v-card-title>
        <v-card-text>
          {{
            confirm.target === 'all'
              ? 'This removes every appointment, consultation and prescription in all services.'
              : `This removes every ${confirm.target.slice(0, -1)} in the database.`
          }}
          This cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirm.show = false">Cancel</v-btn>
          <v-btn color="error" variant="flat" @click="doClear">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="4000" location="bottom right">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>

  <div v-else class="d-flex justify-center align-center" style="min-height: 60vh">
    <v-progress-circular indeterminate color="primary" />
  </div>
</template>

<style scoped>
.danger {
  border-color: rgb(var(--v-theme-error));
}
</style>
