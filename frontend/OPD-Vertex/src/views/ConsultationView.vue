<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useConsultationData } from '@/composables/useConsultationData'
import AppointmentSidebar from '@/components/Consultation/AppointmentSidebar.vue'
import PatientInfoCard from '@/components/Consultation/PatientInfoCard.vue'
import RecordingCard from '@/components/Consultation/RecordingCard.vue'
import TranscriptionUploadCard from '@/components/Consultation/TranscriptionUploadCard.vue'
import PrescriptionCard from '@/components/Consultation/PrescriptionCard.vue'

const router = useRouter()
const { appointment, rxDraft } = useConsultationData()

const isSelected = ref(false)
const consultationStatus = ref<'waiting' | 'active' | 'done'>('waiting')
const currentRxText = ref(rxDraft.text)

function onRecordingStatusChange(status: 'idle' | 'recording' | 'done') {
  if (status === 'recording') consultationStatus.value = 'active'
  else if (status === 'done') consultationStatus.value = 'done'
}

function onTranscriptReady(text: string) {
  // When recording finishes, update the rx with enriched draft
  currentRxText.value = `PATIENT: ${appointment.name}
DATE: ${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}  |  DR. HANSEN

TRANSCRIPT SUMMARY:
${text}

MEDICATIONS:
1. Amoxicillin 500mg — 3× daily for 7 days
   Take with food. Complete full course.
2. Ibuprofen 400mg — as needed (max 3/day)
   Avoid on empty stomach.

NOTES:
Follow-up in 1 week if symptoms persist.
Avoid dairy 2h before/after Amoxicillin.`
}

function onUploadTranscript(text: string) {
  currentRxText.value = `PATIENT: ${appointment.name}
DATE: ${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}  |  DR. HANSEN

[From uploaded audio]
TRANSCRIPT:
${text}

MEDICATIONS:
Review transcript above and update accordingly.

NOTES:
AI-assisted draft from uploaded audio file.`
}

function onApproved(_text: string) {
  consultationStatus.value = 'done'
}
</script>

<template>
  <div class="consultation-layout">
    <!-- Sidebar -->
    <AppointmentSidebar
      :appointment="appointment"
      :selected="isSelected"
      @select="isSelected = true"
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

      <!-- Empty state -->
      <div v-if="!isSelected" class="empty-state">
        <v-icon size="64" color="primary" opacity="0.2" class="mb-4">mdi-cursor-default-click</v-icon>
        <p class="empty-title">Select a patient to begin</p>
        <p class="empty-sub">Click on an appointment in the left sidebar</p>
      </div>

      <!-- Consultation content -->
      <div v-else class="content-scroll">
        <div class="content-inner pa-6">
          <PatientInfoCard
            :patient="appointment"
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
            :initial-text="currentRxText"
            :patient-name="appointment.name"
            :patient-email="appointment.email"
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
  height: calc(100vh - 64px); /* subtract app bar */
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
</style>