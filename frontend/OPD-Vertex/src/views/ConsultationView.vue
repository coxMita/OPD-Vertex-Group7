<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConsultationList } from '@/composables/useConsultationList'
import { appointmentApi } from '@/services/appointmentApi'
import { userApi } from '@/services/userApi'
import AppointmentSidebar from '@/components/Consultation/AppointmentSidebar.vue'
import type { ConsultationSidebarItem } from '@/components/Consultation/AppointmentSidebar.vue'
import PatientInfoCard from '@/components/Consultation/PatientInfoCard.vue'
import RecordingCard from '@/components/Consultation/RecordingCard.vue'
import TranscriptionUploadCard from '@/components/Consultation/TranscriptionUploadCard.vue'
import PrescriptionCard from '@/components/Consultation/PrescriptionCard.vue'
import type { Consultation } from '@/models/consultation/consultation.interface'
import type { ConsultationPatient } from '@/composables/useConsultationData'

const props = defineProps<{
  doctorId: string
}>()

const router = useRouter()

const {
  consultations,
  loading,
  error,
  selectedConsultation,
  fetchConsultations,
  selectConsultation,
} = useConsultationList()

// ── Enriched sidebar items ─────────────────────────────────────
const sidebarItems = ref<ConsultationSidebarItem[]>([])

async function enrichConsultationsForSidebar(rawConsultations: Consultation[]) {
  sidebarItems.value = rawConsultations.map((c) => ({
    ...c,
    patient_name: null,
    assigned_time: null,
  }))

  await Promise.allSettled(
    rawConsultations.map(async (c, index) => {
      try {
        const appointment = await appointmentApi.getAppointment(c.appointment_id)
        const patient = await userApi.getPatient(appointment.patient_id)
        sidebarItems.value[index] = {
          ...c,
          patient_name: `${patient.first_name} ${capitalize(patient.last_name)}`,
          assigned_time: appointment.assigned_time,
        }
      } catch {
        // Keep placeholder
      }
    }),
  )
}

// ── Patient state ──────────────────────────────────────────────
const currentPatient = ref<ConsultationPatient | null>(null)
const patientLoading = ref(false)
const patientError = ref<string | null>(null)

async function fetchPatientForConsultation(consultation: Consultation) {
  patientLoading.value = true
  patientError.value = null
  currentPatient.value = null

  try {
    const appointment = await appointmentApi.getAppointment(consultation.appointment_id)
    const patient = await userApi.getPatient(appointment.patient_id)

    currentPatient.value = {
      id: patient.patient_id,
      name: `${patient.first_name} ${capitalize(patient.last_name)}`,
      time: appointment.assigned_time?.slice(0, 5) ?? '—',
      department: '—',
      status: consultation.status === 'ACTIVE' ? 'active' : 'done',
      tag: 'new',
      phone: String(patient.phone_number ?? '—'),
      email: patient.email,
      dob: patient.date_of_birth
        ? new Date(patient.date_of_birth).toLocaleDateString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
          })
        : '—',
      age: patient.date_of_birth ? calculateAge(patient.date_of_birth) : 0,
      gender: patient.gender ?? '—',
      cpr: '—',
      blood: '—',
      allergy: '—',
      reason: appointment.notes ?? '—',
    }
  } catch (err) {
    console.error('Failed to fetch patient data:', err)
    patientError.value = 'Could not load patient data.'
  } finally {
    patientLoading.value = false
  }
}

function capitalize(str: string): string {
  if (!str) return str
  return str.charAt(0).toUpperCase() + str.slice(1)
}

function calculateAge(dateOfBirth: string): number {
  const today = new Date()
  const birth = new Date(dateOfBirth)
  if (isNaN(birth.getTime())) return 0
  let age = today.getFullYear() - birth.getFullYear()
  const monthDiff = today.getMonth() - birth.getMonth()
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) age--
  return Math.max(0, age)
}

// ── Consultation / prescription state ──────────────────────────
const consultationStatus = ref<'waiting' | 'active' | 'done'>('waiting')
const currentRxText = ref('')
const prescriptionKey = ref(0)
// The consultation ID to pass to PrescriptionCard for polling
const activePrescriptionConsultationId = ref<string | null>(null)

onMounted(async () => {
  await fetchConsultations(props.doctorId)
  await enrichConsultationsForSidebar(consultations.value)
})

async function onSelect(consultation: ConsultationSidebarItem) {
  selectConsultation(consultation)
  consultationStatus.value = consultation.status === 'ACTIVE' ? 'active' : 'done'
  currentRxText.value = ''
  prescriptionKey.value++
  // Set the consultationId — PrescriptionCard will start polling automatically
  activePrescriptionConsultationId.value = consultation.id

  await fetchPatientForConsultation(consultation)
}

function onRecordingStatusChange(status: 'idle' | 'recording' | 'processing' | 'done' | 'error') {
  if (status === 'recording') consultationStatus.value = 'active'
  else if (status === 'done') consultationStatus.value = 'done'
}

function onTranscriptReady(_text: string) {
  // Transcript sent to backend — PrescriptionCard polls DB for the AI result
}

function onUploadTranscript(_text: string) {
  // Transcript sent to backend — PrescriptionCard polls DB for the AI result
}

function onApproved(text: string) {
  consultationStatus.value = 'done'

  const toEmail = mockPatient.email !== '—' ? mockPatient.email : 'opdvertex00@gmail.com'

  fetch('http://localhost:8084/api/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      to_email: toEmail,
      subject: 'Consultation Transcript & Prescription',
      message: 'Hello! Your doctor has approved your prescription. Attached is the PDF document for your records.',
      is_html: false,
      document_title: 'Approved Prescription',
      document_content: text
    })
  })
  .then(res => {
    if (!res.ok) throw Error('Network response was not ok')
    return res.json()
  })
  .then(data => console.log('Mock email triggered successfully:', data))
  .catch(err => console.error('Failed to trigger mock email:', err))
}
</script>

<template>
  <div class="consultation-layout">
    <AppointmentSidebar
      :consultations="sidebarItems"
      :selected-id="selectedConsultation?.id ?? null"
      :loading="loading"
      @select="onSelect"
    />

    <main class="main-panel">
      <div class="top-bar px-6 py-3 d-flex align-center ga-3">
        <v-btn
          variant="text"
          size="small"
          prepend-icon="mdi-arrow-left"
          @click="router.push('/')"
        >
          Back
        </v-btn>
        <v-divider vertical class="mx-1" />
        <span class="top-bar-title">Doctor Dashboard</span>
        <v-spacer />
        <v-chip color="teal" variant="tonal" size="small">
          <v-icon start size="12">mdi-stethoscope</v-icon>
          Dr. Hansen
        </v-chip>
      </div>

      <v-divider />

      <v-alert
        v-if="error"
        type="error"
        variant="tonal"
        density="compact"
        closable
        class="mx-4 mt-2"
      >
        {{ error }}
      </v-alert>

      <div v-if="!selectedConsultation" class="empty-state">
        <v-icon size="64" color="primary" opacity="0.2" class="mb-4">mdi-cursor-default-click</v-icon>
        <p class="empty-title">Select a consultation to begin</p>
        <p class="empty-sub">Click on a consultation in the left sidebar</p>
      </div>

      <div v-else class="content-scroll">
        <div class="content-inner pa-6">

          <v-card rounded="lg" elevation="1" class="mb-4 pa-4">
            <div class="d-flex align-center justify-space-between">
              <div>
                <p class="meta-label mb-1">CONSULTATION ID</p>
                <p class="meta-value mono">{{ selectedConsultation.id }}</p>
              </div>
              <div>
                <p class="meta-label mb-1">APPOINTMENT</p>
                <p class="meta-value mono">{{ selectedConsultation.appointment_id }}</p>
              </div>
            </div>
          </v-card>

          <v-card v-if="patientLoading" rounded="lg" elevation="1" class="mb-4 pa-6">
            <div class="d-flex align-center ga-3">
              <v-progress-circular indeterminate color="primary" size="24" />
              <span class="text-body-2 opacity-60">Loading patient data…</span>
            </div>
          </v-card>

          <v-alert
            v-else-if="patientError"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            {{ patientError }}
          </v-alert>

          <PatientInfoCard
            v-else-if="currentPatient"
            :patient="currentPatient"
          />

          <RecordingCard
            :key="`recording-${selectedConsultation?.id}`"
            :consultation-id="activePrescriptionConsultationId"
            @transcript-ready="onTranscriptReady"
            @status-change="onRecordingStatusChange"
          />

          <TranscriptionUploadCard
            :key="`upload-${selectedConsultation?.id}`"
            :consultation-id="activePrescriptionConsultationId"
            @transcript-ready="onUploadTranscript"
          />

          <!-- PrescriptionCard receives consultationId and polls automatically -->
          <PrescriptionCard
            :key="prescriptionKey"
            :initial-text="currentRxText"
            :patient-name="currentPatient?.name ?? ''"
            :patient-email="currentPatient?.email ?? ''"
            :consultation-id="activePrescriptionConsultationId"
            @approved="onApproved"
          />

        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.consultation-layout {
  display: flex;
  height: calc(100vh - 64px);
  overflow: hidden;
}
.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(var(--v-theme-on-surface), 0.02);
}
.top-bar {
  background: rgb(var(--v-theme-surface));
  flex-shrink: 0;
}
.top-bar-title {
  font-size: 0.88rem;
  font-weight: 600;
  opacity: 0.7;
}
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
}
.empty-title {
  font-size: 1.1rem;
  font-weight: 700;
  opacity: 0.4;
  margin: 0 0 6px;
}
.empty-sub {
  font-size: 0.82rem;
  opacity: 0.3;
  margin: 0;
}
.content-scroll {
  flex: 1;
  overflow-y: auto;
}
.content-scroll::-webkit-scrollbar { width: 5px; }
.content-scroll::-webkit-scrollbar-thumb {
  background: rgba(var(--v-border-color), 0.4);
  border-radius: 4px;
}
.content-inner {
  max-width: 760px;
}
.meta-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  opacity: 0.45;
  margin: 0;
}
.meta-value {
  font-size: 0.82rem;
  font-weight: 600;
  margin: 0;
}
.meta-value.mono {
  font-family: 'DM Mono', monospace;
  font-size: 0.72rem;
  word-break: break-all;
}
</style>