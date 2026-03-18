<script setup lang="ts">
import type { ConsultationPatient } from '@/composables/useConsultationData'

defineProps<{
  appointment: ConsultationPatient
  selected: boolean
}>()

const emit = defineEmits<{ (e: 'select'): void }>()

const tagConfig: Record<string, { label: string; color: string }> = {
  'new': { label: 'New Patient', color: 'primary' },
  'follow-up': { label: 'Follow-up', color: 'teal' },
  'urgent': { label: '⚡ Urgent', color: 'warning' },
}

const statusConfig: Record<string, { label: string; color: string }> = {
  'waiting': { label: 'Waiting', color: 'warning' },
  'active': { label: '● Active', color: 'success' },
  'done': { label: '✓ Done', color: 'default' },
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header px-4 pt-4 pb-3">
      <p class="sidebar-label mb-3">UPCOMING APPOINTMENTS</p>
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
      <div class="date-divider px-4 py-2">
        <span class="date-label">Today — Mon 24 Feb</span>
      </div>

      <!-- The one consultation card -->
      <div
        class="appt-item"
        :class="{ selected }"
        @click="emit('select')"
      >
        <div class="d-flex justify-space-between align-start mb-1">
          <span class="patient-name">{{ appointment.name }}</span>
          <span class="appt-time">{{ appointment.time }}</span>
        </div>
        <p class="appt-dept mb-2">{{ appointment.department }}</p>
        <div class="d-flex align-center justify-space-between">
          <v-chip
            :color="tagConfig[appointment.tag].color"
            size="x-small"
            variant="tonal"
            class="font-weight-bold"
          >
            {{ tagConfig[appointment.tag].label }}
          </v-chip>
          <v-chip
            :color="statusConfig[appointment.status].color"
            size="x-small"
            variant="tonal"
          >
            {{ statusConfig[appointment.status].label }}
          </v-chip>
        </div>
      </div>
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
</style>