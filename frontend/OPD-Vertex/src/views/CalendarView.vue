<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useTheme } from 'vuetify'
import type { Appointment } from '@/models/appointment/appointment.interface'
import { getMockAppointmentsForDay } from '@/models/appointment/appointment.mock'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8082'
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const vuetifyTheme = useTheme()
const isDark = computed(() => vuetifyTheme.current.value.dark)

const doctorId = ref(1)

const currentView = ref<'day' | 'week' | 'month'>('week')
const currentDate = ref(new Date())
const appointments = ref<Appointment[]>([])
const loading = ref(false)

type StatusKey = 'scheduled' | 'in_progress' | 'done' | 'cancelled'

interface StatusCfg {
  lightBg: string
  darkBg: string
  lightText: string
  darkText: string
  border: string
  icon: string
  label: string
}

const statusConfig: Record<StatusKey, StatusCfg> = {
  scheduled: {
    lightBg: '#dbeafe', darkBg: '#1e3558',
    lightText: '#1d4ed8', darkText: '#93c5fd',
    border: '#3b82f6', icon: 'mdi-clock-outline', label: 'Scheduled',
  },
  in_progress: {
    lightBg: '#fef3c7', darkBg: '#3d1f00',
    lightText: '#b45309', darkText: '#fcd34d',
    border: '#f59e0b', icon: 'mdi-progress-clock', label: 'In Progress',
  },
  done: {
    lightBg: '#ccfbf1', darkBg: '#032b28',
    lightText: '#0d7a70', darkText: '#2dd4bf',
    border: '#14b8a6', icon: 'mdi-check-circle-outline', label: 'Done',
  },
  cancelled: {
    lightBg: '#f1f5f9', darkBg: '#1a2133',
    lightText: '#64748b', darkText: '#94a3b8',
    border: '#94a3b8', icon: 'mdi-close-circle-outline', label: 'Cancelled',
  },
}

function getApptStyle(status: string) {
  const cfg = statusConfig[status as StatusKey] ?? statusConfig.scheduled
  return {
    background: isDark.value ? cfg.darkBg : cfg.lightBg,
    color: isDark.value ? cfg.darkText : cfg.lightText,
    borderLeftColor: cfg.border,
  }
}

function getStatusIcon(status: string): string {
  return statusConfig[status as StatusKey]?.icon ?? 'mdi-calendar'
}

const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const timeSlots = Array.from({ length: 24 }, (_, i) => i)

const weekBodyRef = ref<HTMLElement | null>(null)
const dayViewRef = ref<HTMLElement | null>(null)

const SLOT_HEIGHT_WEEK = 50
const SLOT_HEIGHT_DAY = 56
const SCROLL_START_HOUR = 6

function scrollTo6am() {
  nextTick(() => {
    if (currentView.value === 'week' && weekBodyRef.value) {
      weekBodyRef.value.scrollTop = SCROLL_START_HOUR * SLOT_HEIGHT_WEEK
    } else if (currentView.value === 'day' && dayViewRef.value) {
      dayViewRef.value.scrollTop = SCROLL_START_HOUR * SLOT_HEIGHT_DAY
    }
  })
}

// --- Date helpers ---

function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getWeekStart(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  d.setDate(d.getDate() - day + (day === 0 ? -6 : 1))
  return d
}

function isToday(date: Date): boolean {
  return formatDate(date) === formatDate(new Date())
}

// --- Navigation ---

function navigate(direction: number) {
  const d = new Date(currentDate.value)
  if (currentView.value === 'day') {
    d.setDate(d.getDate() + direction)
  } else if (currentView.value === 'week') {
    d.setDate(d.getDate() + direction * 7)
  } else {
    d.setMonth(d.getMonth() + direction)
  }
  currentDate.value = d
}

function goToToday() {
  currentDate.value = new Date()
}

// --- Computed view data ---

const currentDateDisplay = computed(() => {
  const options: Intl.DateTimeFormatOptions = { month: 'long', year: 'numeric' }
  if (currentView.value === 'day') {
    return currentDate.value.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }
  if (currentView.value === 'week') {
    const weekStart = getWeekStart(currentDate.value)
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekEnd.getDate() + 6)
    return `${weekStart.toLocaleDateString('en-US', options)} – ${weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  }
  return currentDate.value.toLocaleDateString('en-US', options)
})

const weekDaysInView = computed(() => {
  const weekStart = getWeekStart(currentDate.value)
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + i)
    return d
  })
})

const monthDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startOffset = (firstDay.getDay() + 6) % 7
  const prevMonthLastDay = new Date(year, month, 0).getDate()

  const days: { date: Date; isOtherMonth: boolean }[] = []

  for (let i = startOffset - 1; i >= 0; i--) {
    days.push({ date: new Date(year, month - 1, prevMonthLastDay - i), isOtherMonth: true })
  }
  for (let d = 1; d <= lastDay.getDate(); d++) {
    days.push({ date: new Date(year, month, d), isOtherMonth: false })
  }
  for (let d = 1; d <= 42 - days.length; d++) {
    days.push({ date: new Date(year, month + 1, d), isOtherMonth: true })
  }

  return days
})

// Dates visible in the current view — drives the data fetch
const visibleDates = computed<Date[]>(() => {
  if (currentView.value === 'day') return [currentDate.value]
  if (currentView.value === 'week') return weekDaysInView.value
  return monthDays.value.filter((d) => !d.isOtherMonth).map((d) => d.date)
})

// --- Appointment filtering ---

function getAppointmentsForDate(date: Date): Appointment[] {
  const dateStr = formatDate(date)
  return appointments.value.filter((a) => a.appointment_date === dateStr)
}

function getAppointmentsForTimeSlot(date: Date, hour: number): Appointment[] {
  return getAppointmentsForDate(date).filter((a) => {
    if (!a.assigned_time) return false
    return parseInt(a.assigned_time.split(':')[0] ?? '0') === hour
  })
}

// --- Data fetching ---

async function fetchDayAppointments(date: Date): Promise<Appointment[]> {
  if (USE_MOCK) {
    return getMockAppointmentsForDay(doctorId.value, formatDate(date))
  }
  const response = await fetch(
    `${API_BASE_URL}/api/v1/appointments/queue/day?doctor_id=${doctorId.value}&appointment_date=${formatDate(date)}`,
  )
  if (!response.ok) return []
  return response.json()
}

async function fetchAppointments() {
  loading.value = true
  try {
    const results = await Promise.all(visibleDates.value.map(fetchDayAppointments))
    appointments.value = results.flat()
  } catch (error) {
    console.error('Failed to fetch appointments:', error)
    appointments.value = []
  } finally {
    loading.value = false
  }
}

watch(visibleDates, fetchAppointments)
watch(currentView, scrollTo6am)
onMounted(() => {
  fetchAppointments()
  scrollTo6am()
})
</script>

<template>
  <div class="calendar-container">
    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
      height="2"
      class="progress-bar"
    />

    <div class="calendar-toolbar">
      <div class="toolbar-left">
        <div class="date-nav">
          <v-btn icon variant="outlined" size="small" @click="navigate(-1)">
            <v-icon>mdi-chevron-left</v-icon>
          </v-btn>
          <v-btn icon variant="outlined" size="small" @click="navigate(1)">
            <v-icon>mdi-chevron-right</v-icon>
          </v-btn>
          <span class="current-date">{{ currentDateDisplay }}</span>
        </div>
        <v-btn variant="tonal" color="primary" size="small" @click="goToToday">Today</v-btn>
      </div>

      <div class="toolbar-right">
        <v-btn-toggle v-model="currentView" mandatory variant="outlined" density="compact" divided>
          <v-btn value="day" size="small">Day</v-btn>
          <v-btn value="week" size="small">Week</v-btn>
          <v-btn value="month" size="small">Month</v-btn>
        </v-btn-toggle>
      </div>
    </div>

    <div class="calendar-view day-view" ref="dayViewRef" v-if="currentView === 'day'">
      <div class="time-grid">
        <template v-for="hour in timeSlots" :key="hour">
          <div class="time-label">{{ hour.toString().padStart(2, '0') }}:00</div>
          <div class="time-slot">
            <div
              v-for="appt in getAppointmentsForTimeSlot(currentDate, hour)"
              :key="appt.id"
              class="appt-card"
              :style="getApptStyle(appt.status)"
            >
              <div class="appt-header-row">
                <v-icon size="12" style="color: currentColor">{{ getStatusIcon(appt.status) }}</v-icon>
                <span class="appt-time">{{ appt.assigned_time }}</span>
              </div>
              <div class="appt-name">Patient #{{ appt.patient_id }}</div>
              <div class="appt-type">{{ appt.time_preference }} · {{ appt.status.replace('_', ' ') }}</div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="calendar-view week-view" v-if="currentView === 'week'">
      <div class="week-header">
        <div class="week-corner"></div>
        <div v-for="(day, idx) in weekDaysInView" :key="idx" class="week-day-header">
          <div class="week-day-name">{{ weekDays[idx] }}</div>
          <div class="week-day-date" :class="{ today: isToday(day) }">{{ day.getDate() }}</div>
        </div>
      </div>

      <div class="week-body" ref="weekBodyRef">
      <div class="week-grid">
        <template v-for="hour in timeSlots" :key="hour">
          <div class="week-time-label">{{ hour.toString().padStart(2, '0') }}:00</div>
          <div
            v-for="(day, dayIdx) in weekDaysInView"
            :key="`${hour}-${dayIdx}`"
            class="week-time-slot"
          >
            <div
              v-for="appt in getAppointmentsForTimeSlot(day, hour)"
              :key="appt.id"
              class="appt-card appt-card--compact"
              :style="getApptStyle(appt.status)"
            >
              <v-icon size="10" style="color: currentColor; flex-shrink: 0">{{ getStatusIcon(appt.status) }}</v-icon>
              <span class="appt-time ml-1">{{ appt.assigned_time }}</span>
              <div class="appt-name">P#{{ appt.patient_id }}</div>
            </div>
          </div>
        </template>
      </div>
      </div>
    </div>

    <div class="calendar-view month-view" v-if="currentView === 'month'">
      <div class="month-grid">
        <div v-for="day in weekDays" :key="day" class="month-day-header">{{ day }}</div>
        <div
          v-for="(day, idx) in monthDays"
          :key="idx"
          class="month-day"
          :class="{ 'other-month': day.isOtherMonth, today: isToday(day.date) }"
        >
          <div class="month-day-number">{{ day.date.getDate() }}</div>
          <div class="month-appointments">
            <div
              v-for="appt in getAppointmentsForDate(day.date)"
              :key="appt.id"
              class="month-appt-card"
              :style="getApptStyle(appt.status)"
            >
              <v-icon size="9" style="color: currentColor; flex-shrink: 0">{{ getStatusIcon(appt.status) }}</v-icon>
              <span class="month-appt-time">{{ appt.assigned_time ?? '' }}</span>
              <span class="month-appt-name">P#{{ appt.patient_id }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Container ───────────────────────────────────────────── */
.calendar-container {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-background));
  position: relative;
}

.progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
}

/* ── Toolbar ─────────────────────────────────────────────── */
.calendar-toolbar {
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.date-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-date {
  font-family: 'DM Serif Display', serif;
  font-size: 1.15rem;
  color: rgb(var(--v-theme-on-surface));
  min-width: 240px;
}

.toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

/* ── Shared scrollable view ───────────────────────────────── */
.calendar-view {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

/* ── Day View ────────────────────────────────────────────── */
.day-view {
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
}

/* ── Week View ───────────────────────────────────────────── */
.week-view {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
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
}

/* ── Month View ──────────────────────────────────────────── */
.month-view {
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

/* ── Appointment Cards (shared) ──────────────────────────── */
.appt-card {
  border-radius: 6px;
  padding: 7px 10px;
  border-left: 3px solid transparent;
  margin-bottom: 3px;
  cursor: pointer;
  transition: filter 0.15s ease, transform 0.1s ease;
}

.appt-card:hover {
  filter: brightness(0.93);
  transform: translateX(1px);
}

.appt-card--compact {
  padding: 4px 6px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
}

.appt-header-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.appt-time {
  font-size: 0.68rem;
  font-weight: 700;
  opacity: 0.85;
}

.appt-name {
  font-size: 0.82rem;
  font-weight: 600;
  width: 100%;
}

.appt-type {
  font-size: 0.67rem;
  opacity: 0.68;
  margin-top: 1px;
}

/* Month compact pill */
.month-appt-card {
  border-radius: 4px;
  padding: 2px 5px;
  border-left: 3px solid transparent;
  display: flex;
  align-items: center;
  gap: 3px;
  overflow: hidden;
}

.month-appt-time {
  font-size: 0.65rem;
  font-weight: 700;
  opacity: 0.8;
  flex-shrink: 0;
}

.month-appt-name {
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
