<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConsultationList } from '@/composables/useConsultationList'
import AppointmentSidebar from '@/components/Consultation/AppointmentSidebar.vue'
import PatientInfoCard from '@/components/Consultation/PatientInfoCard.vue'
import RecordingCard from '@/components/Consultation/RecordingCard.vue'
import TranscriptionUploadCard from '@/components/Consultation/TranscriptionUploadCard.vue'
import PrescriptionCard from '@/components/Consultation/PrescriptionCard.vue'
import type { Consultation } from '@/models/consultation/consultation.interface'

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

const consultationStatus = ref<'waiting' | 'active' | 'done'>('waiting')
const currentRxText = ref('')
const prescriptionKey = ref(0)

onMounted(() => {
  fetchConsultations(props.doctorId)
})

function onSelect(consultation: Consultation) {
  selectConsultation(consultation)
  consultationStatus.value = consultation.status === 'ACTIVE' ? 'active' : 'done'
  currentRxText.value = ''
  prescriptionKey.value++
}

function onRecordingStatusChange(status: 'idle' | 'recording' | 'processing' | 'done' | 'error') {
  if (status === 'recording') consultationStatus.value = 'active'
  else if (status === 'done') consultationStatus.value = 'done'
}

function onTranscriptReady(text: string) {
  currentRxText.value = buildRxDraft(text, 'Recording')
  prescriptionKey.value++
}

function onUploadTranscript(text: string) {
  currentRxText.value = buildRxDraft(text, 'Upload')
  prescriptionKey.value++
}

function buildRxDraft(transcript: string, source: string): string {
  const date = new Date().toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
  return `DATE: ${date}  |  DR. (doctor)

[Source: ${source}]
TRANSCRIPT:
${transcript}

MEDICATIONS:
Review transcript above and update accordingly.

NOTES:
AI-assisted draft — please review before approving.`
}

function onApproved(_text: string) {
  consultationStatus.value = 'done'
}

// Mock patient info — replace with real patient data when user-service is connected
const mockPatient = {
  id: '',
  name: 'Patient',
  time: '—',
  department: 'Consultation',
  status: 'waiting' as const,
  tag: 'new' as const,
  phone: '—',
  email: '—',
  dob: '—',
  age: 0,
  gender: '—',
  cpr: '—',
  blood: '—',
  allergy: '—',
  reason: '—',
}
</script>

<template>
  <div class="consultation-layout">
    <!-- Sidebar -->
    <AppointmentSidebar
      :consultations="consultations"
      :selected-id="selectedConsultation?.id ?? null"
      :loading="loading"
      @select="onSelect"
    />

    <!-- Main panel -->
    <main class="main-panel">
      <!-- Top bar -->
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

      <!-- Error -->
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

      <!-- Empty state -->
      <div v-if="!selectedConsultation" class="empty-state">
        <v-icon size="64" color="primary" opacity="0.2" class="mb-4">mdi-cursor-default-click</v-icon>
        <p class="empty-title">Select a consultation to begin</p>
        <p class="empty-sub">Click on a consultation in the left sidebar</p>
      </div>

      <!-- Consultation content -->
      <div v-else class="content-scroll">
        <div class="content-inner pa-6">
          <!-- Consultation meta -->
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

          <!-- TODO: PatientInfoCard — conectează la user-service când e disponibil -->
          <PatientInfoCard
            :patient="mockPatient"
            :status="consultationStatus"
          />

          <RecordingCard
            @transcript-ready="onTranscriptReady"
            @status-change="onRecordingStatusChange"
          />

          <TranscriptionUploadCard
            @transcript-ready="onUploadTranscript"
          />

          <PrescriptionCard
            :key="prescriptionKey"
            :initial-text="currentRxText"
            :patient-name="mockPatient.name"
            :patient-email="mockPatient.email"
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

.content-scroll::-webkit-scrollbar {
  width: 5px;
}

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