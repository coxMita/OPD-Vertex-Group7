<script setup lang="ts">
import type { Appointment } from '@/models/appointment/appointment.interface'
import { STATUS_CONFIG } from '@/composables/useCalendarAppointments'
import type { StatusKey } from '@/composables/useCalendarAppointments'

defineProps<{
  appointment: Appointment | null
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

function formatTime(t: string | null): string {
  if (!t) return '—'
  // "HH:MM:SS" → "HH:MM"
  return t.slice(0, 5)
}

function formatDate(d: string): string {
  const [year, month, day] = d.split('-')
  return `${day}/${month}/${year}`
}
</script>

<template>
  <v-dialog
    :model-value="modelValue"
    max-width="420"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card v-if="appointment" rounded="xl" elevation="8">
      <!-- Header -->
      <div
        class="modal-header px-6 pt-5 pb-4"
        :style="{ borderLeft: `4px solid ${STATUS_CONFIG[appointment.status as StatusKey]?.border ?? '#94a3b8'}` }"
      >
        <div class="d-flex align-center justify-space-between">
          <div class="d-flex align-center ga-2">
            <v-icon
              :color="STATUS_CONFIG[appointment.status as StatusKey]?.border ?? '#94a3b8'"
              size="18"
            >
              {{ STATUS_CONFIG[appointment.status as StatusKey]?.icon ?? 'mdi-calendar' }}
            </v-icon>
            <span class="modal-title">Appointment Details</span>
          </div>
          <v-btn
            icon="mdi-close"
            size="x-small"
            variant="text"
            @click="emit('update:modelValue', false)"
          />
        </div>

        <v-chip
          :color="STATUS_CONFIG[appointment.status as StatusKey]?.border ?? '#94a3b8'"
          size="x-small"
          variant="tonal"
          class="mt-2 font-weight-bold"
        >
          {{ STATUS_CONFIG[appointment.status as StatusKey]?.label ?? appointment.status }}
        </v-chip>
      </div>

      <v-divider />

      <!-- Fields -->
      <div class="px-6 py-4">
        <div class="info-grid">
          <div class="info-item">
            <p class="info-label">Date</p>
            <p class="info-value">{{ formatDate(appointment.appointment_date) }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Time</p>
            <p class="info-value">{{ formatTime(appointment.assigned_time) }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Session</p>
            <p class="info-value">{{ appointment.time_preference }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Status</p>
            <p class="info-value">{{ STATUS_CONFIG[appointment.status as StatusKey]?.label ?? appointment.status }}</p>
          </div>
        </div>

        <v-divider class="my-3" />

        <div class="info-item mb-3">
          <p class="info-label">Patient ID</p>
          <p class="info-value mono">{{ appointment.patient_id }}</p>
        </div>

        <div class="info-item" v-if="appointment.notes">
          <p class="info-label">Notes</p>
          <p class="info-value">{{ appointment.notes }}</p>
        </div>
        <div class="info-item" v-else>
          <p class="info-label">Notes</p>
          <p class="info-value muted">No notes</p>
        </div>
      </div>

      <v-divider />

      <div class="px-6 py-3 d-flex justify-end">
        <v-btn
          variant="tonal"
          size="small"
          @click="emit('update:modelValue', false)"
        >
          Close
        </v-btn>
      </div>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.modal-header {
  background: rgba(var(--v-theme-surface), 1);
}
.modal-title {
  font-size: 0.95rem;
  font-weight: 700;
}
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  margin-bottom: 12px;
}
.info-item {}
.info-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  opacity: 0.45;
  margin: 0 0 2px;
}
.info-value {
  font-size: 0.88rem;
  font-weight: 600;
  margin: 0;
}
.info-value.mono {
  font-family: 'DM Mono', monospace;
  font-size: 0.75rem;
  word-break: break-all;
}
.info-value.muted {
  opacity: 0.4;
  font-weight: 400;
  font-style: italic;
}
</style>