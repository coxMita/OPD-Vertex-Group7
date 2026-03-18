<script setup lang="ts">
import { ref } from 'vue'
import type { Appointment } from '@/models/appointment/appointment.interface'
import AppointmentCard from './AppointmentCard.vue'
import { TIME_SLOTS } from '@/composables/useCalendarNavigation'
import { STATUS_CONFIG } from '@/composables/useCalendarAppointments'
import type { StatusKey } from '@/composables/useCalendarAppointments'

const props = defineProps<{
  currentDate: Date
  getAppointmentsForTimeSlot: (date: Date, hour: number) => Appointment[]
  getApptStyle: (status: string) => Record<string, string>
  getStatusIcon: (status: string) => string
  editMode: boolean
  draggingId: string | null
  isDragOver: (date: string, hour: number) => boolean
  formatDate: (date: Date) => string
}>()

const emit = defineEmits<{
  (e: 'dragstart', id: string): void
  (e: 'dragover', date: string, hour: number): void
  (e: 'dragleave'): void
  (e: 'drop', date: string, hour: number): void
  (e: 'select', id: string): void
}>()

const dayViewRef = ref<HTMLElement | null>(null)

defineExpose({ dayViewRef })
</script>

<template>
  <div class="calendar-view day-view" ref="dayViewRef">
    <div class="time-grid">
      <template v-for="hour in TIME_SLOTS" :key="hour">
        <div class="time-label">{{ hour.toString().padStart(2, '0') }}:00</div>
        <div
          class="time-slot"
          :class="{
            'drop-target': editMode && isDragOver(formatDate(currentDate), hour),
            'edit-mode': editMode,
          }"
          @dragover.prevent="emit('dragover', formatDate(currentDate), hour)"
          @dragleave="emit('dragleave')"
          @drop.prevent="emit('drop', formatDate(currentDate), hour)"
        >
          <AppointmentCard
            v-for="appt in getAppointmentsForTimeSlot(currentDate, hour)"
            :key="appt.id"
            :appointmentId="appt.id"
            :statusIcon="getStatusIcon(appt.status)"
            :assignedTime="appt.assigned_time"
            :patientId="appt.patient_id"
            :timePreference="appt.time_preference"
            :statusLabel="STATUS_CONFIG[appt.status as StatusKey]?.label ?? appt.status.replace('_', ' ')"
            :apptStyle="getApptStyle(appt.status)"
            :editMode="editMode"
            :isDragging="draggingId === appt.id"
            @dragstart="emit('dragstart', $event)"
            @select="emit('select', $event)"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.calendar-view {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}
.time-grid {
  display: grid;
  grid-template-columns: 72px 1fr;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.time-label {
  padding: 14px 12px;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.07);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.45);
  text-align: right;
  background: rgba(var(--v-theme-on-surface), 0.02);
}
.time-slot {
  padding: 6px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  min-height: 56px;
  transition: background 0.12s ease;
}
.time-slot.edit-mode {
  /* Subtle hint that slots are droppable */
  cursor: default;
}
.time-slot.drop-target {
  background: rgba(var(--v-theme-primary), 0.08);
  outline: 2px dashed rgba(var(--v-theme-primary), 0.4);
  outline-offset: -2px;
}
</style>