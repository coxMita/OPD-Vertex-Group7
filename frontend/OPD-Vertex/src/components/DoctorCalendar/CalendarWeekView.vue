<script setup lang="ts">
import { ref } from 'vue'
import type { Appointment } from '@/models/appointment/appointment.interface'
import AppointmentCard from './AppointmentCard.vue'
import { TIME_SLOTS, WEEK_DAYS } from '@/composables/useCalendarNavigation'

const props = defineProps<{
  weekDaysInView: Date[]
  getAppointmentsForTimeSlot: (date: Date, hour: number) => Appointment[]
  getApptStyle: (status: string) => Record<string, string>
  getStatusIcon: (status: string) => string
  getPatientName: (patientId: string) => string | null
  isToday: (date: Date) => boolean
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

const weekBodyRef = ref<HTMLElement | null>(null)

defineExpose({ weekBodyRef })
</script>

<template>
  <div class="calendar-view week-view">
    <div class="week-header">
      <div class="week-corner"></div>
      <div v-for="(day, idx) in weekDaysInView" :key="idx" class="week-day-header">
        <div class="week-day-name">{{ WEEK_DAYS[idx] }}</div>
        <div class="week-day-date" :class="{ today: isToday(day) }">{{ day.getDate() }}</div>
      </div>
    </div>

    <div class="week-body" ref="weekBodyRef">
      <div class="week-grid">
        <template v-for="hour in TIME_SLOTS" :key="hour">
          <div class="week-time-label">{{ hour.toString().padStart(2, '00') }}:00</div>
          <div
            v-for="(day, dayIdx) in weekDaysInView"
            :key="`${hour}-${dayIdx}`"
            class="week-time-slot"
            :class="{
              'drop-target': editMode && isDragOver(formatDate(day), hour),
              'edit-mode': editMode,
            }"
            @dragover.prevent="emit('dragover', formatDate(day), hour)"
            @dragleave="emit('dragleave')"
            @drop.prevent="emit('drop', formatDate(day), hour)"
          >
            <AppointmentCard
              v-for="appt in getAppointmentsForTimeSlot(day, hour)"
              :key="appt.id"
              :appointmentId="appt.id"
              :statusIcon="getStatusIcon(appt.status)"
              :assignedTime="appt.assigned_time"
              :patientId="appt.patient_id"
              :patientName="getPatientName(appt.patient_id)"
              :apptStyle="getApptStyle(appt.status)"
              :editMode="editMode"
              :isDragging="draggingId === appt.id"
              compact
              @dragstart="emit('dragstart', $event)"
              @select="emit('select', $event)"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.calendar-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.week-header {
  display: grid;
  grid-template-columns: 72px repeat(7, 1fr);
  gap: 6px;
  padding: 12px 20px 8px;
  flex-shrink: 0;
  background: rgb(var(--v-theme-background));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.07);
}
.week-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 0 16px;
}
.week-corner {
  background: transparent;
}
.week-day-header {
  text-align: center;
  padding: 10px 6px;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}
.week-day-name {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: rgba(var(--v-theme-on-surface), 0.45);
  margin-bottom: 4px;
}
.week-day-date {
  font-size: 1.05rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}
.week-day-date.today {
  color: #fff;
  background: #0d9488;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}
.week-grid {
  display: grid;
  grid-template-columns: 72px repeat(7, 1fr);
  gap: 0 6px;
  margin: 8px 20px 0;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.week-time-label {
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  font-size: 0.68rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.4);
  text-align: right;
  background: rgba(var(--v-theme-on-surface), 0.02);
}
.week-time-slot {
  padding: 3px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-left: 1px solid rgba(var(--v-theme-on-surface), 0.04);
  min-height: 50px;
  box-sizing: border-box;
  transition: background 0.12s ease;
}
.week-time-slot.edit-mode {
  cursor: default;
}
.week-time-slot.drop-target {
  background: rgba(var(--v-theme-primary), 0.08);
  outline: 2px dashed rgba(var(--v-theme-primary), 0.4);
  outline-offset: -2px;
}
</style>