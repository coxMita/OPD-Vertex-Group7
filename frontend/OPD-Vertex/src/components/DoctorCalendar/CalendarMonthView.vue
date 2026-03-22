<script setup lang="ts">
import type { Appointment } from '@/models/appointment/appointment.interface'
import AppointmentCard from './AppointmentCard.vue'
import { WEEK_DAYS } from '@/composables/useCalendarNavigation'

defineProps<{
  monthDays: { date: Date; isOtherMonth: boolean }[]
  getAppointmentsForDate: (date: Date) => Appointment[]
  getApptStyle: (status: string) => Record<string, string>
  getStatusIcon: (status: string) => string
  getPatientName: (patientId: string) => string | null
  isToday: (date: Date) => boolean
}>()
</script>

<template>
  <div class="calendar-view month-view">
    <div class="month-grid">
      <div v-for="day in WEEK_DAYS" :key="day" class="month-day-header">{{ day }}</div>
      <div
        v-for="(day, idx) in monthDays"
        :key="idx"
        class="month-day"
        :class="{ 'other-month': day.isOtherMonth, today: isToday(day.date) }"
      >
        <div class="month-day-number">{{ day.date.getDate() }}</div>
        <div class="month-appointments">
          <AppointmentCard
            v-for="appt in getAppointmentsForDate(day.date)"
            :key="appt.id"
            :appointmentId="appt.id"
            :statusIcon="getStatusIcon(appt.status)"
            :assignedTime="appt.assigned_time"
            :patientId="appt.patient_id"
            :patientName="getPatientName(appt.patient_id)"
            :apptStyle="getApptStyle(appt.status)"
            pill
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.calendar-view {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}
.month-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}
.month-day-header {
  text-align: center;
  padding: 8px;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: rgba(var(--v-theme-on-surface), 0.45);
  background: rgb(var(--v-theme-surface));
  border-radius: 8px 8px 0 0;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-bottom: none;
}
.month-day {
  background: rgb(var(--v-theme-surface));
  border-radius: 10px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding: 6px;
  min-height: 110px;
  display: flex;
  flex-direction: column;
}
.month-day.other-month {
  background: rgba(var(--v-theme-on-surface), 0.02);
  opacity: 0.4;
}
.month-day.today {
  border: 2px solid #0d9488;
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15);
}
.month-day-number {
  font-size: 0.82rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.65);
  margin-bottom: 4px;
}
.month-appointments {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  max-height: 80px;
  overflow-y: auto;
}
</style>