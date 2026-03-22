<script setup lang="ts">
import type { Consultation } from '@/models/consultation/consultation.interface'

defineProps<{
  consultations: Consultation[]
  selectedId: string | null
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'select', consultation: Consultation): void
}>()

function formatTime(timeStr: string | null): string {
  if (!timeStr) return '—'
  return timeStr.slice(0, 5)
}

function statusColor(status: string): string {
  return status === 'ACTIVE' ? 'success' : 'default'
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header px-4 pt-4 pb-3">
      <p class="sidebar-label mb-3">ACTIVE CONSULTATIONS</p>
      <v-text-field
        placeholder="Search patients..."
        variant="outlined"
        density="compact"
        rounded="lg"
        hide-details
        prepend-inner-icon="mdi-magnify"
      />
    </div>

    <div class="sidebar-list">
      <!-- Loading state -->
      <div v-if="loading" class="pa-4">
        <v-skeleton-loader type="list-item-two-line" />
        <v-skeleton-loader type="list-item-two-line" class="mt-2" />
      </div>

      <!-- Empty state -->
      <div v-else-if="consultations.length === 0" class="empty-state pa-6 text-center">
        <v-icon size="32" opacity="0.2" class="mb-2">mdi-stethoscope</v-icon>
        <p class="empty-text">No active consultations</p>
      </div>

      <!-- Consultation list -->
      <template v-else>
        <div class="date-divider px-4 py-2">
          <span class="date-label">Today</span>
        </div>

        <div
          v-for="consultation in consultations"
          :key="consultation.id"
          class="appt-item"
          :class="{ selected: selectedId === consultation.id }"
          @click="emit('select', consultation)"
        >
          <div class="d-flex justify-space-between align-start mb-1">
            <span class="patient-name">
              {{ consultation.appointment_id.slice(0, 8) }}…
            </span>
            <span class="appt-time">{{ formatTime(consultation.start_time) }}</span>
          </div>
          <p class="appt-dept mb-2">Consultation</p>
          <div class="d-flex align-center justify-end">
          </div>
        </div>
      </template>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 280px;
  min-width: 280px;
  height: 100%;
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.sidebar-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgb(var(--v-theme-on-surface-variant, 148, 163, 184));
  opacity: 0.7;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
}

.date-divider {
  background: transparent;
}

.date-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.5;
}

.appt-item {
  padding: 14px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s;
}

.appt-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.appt-item.selected {
  background: rgba(var(--v-theme-primary), 0.08);
  border-left-color: rgb(var(--v-theme-primary));
}

.patient-name {
  font-size: 0.87rem;
  font-weight: 700;
  font-family: 'DM Mono', monospace;
}

.appt-time {
  font-size: 0.72rem;
  opacity: 0.6;
}

.appt-dept {
  font-size: 0.76rem;
  opacity: 0.65;
  margin: 0;
}

.empty-text {
  font-size: 0.82rem;
  opacity: 0.4;
  margin: 0;
}
</style>