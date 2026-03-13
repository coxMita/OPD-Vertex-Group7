<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { Appointment } from '@/models/appointment/appointment.interface'
import { getMockAppointmentsForDay } from '@/models/appointment/appointment.mock'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8082'
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// TODO: replace with authenticated doctor ID from auth store
const doctorId = ref(1)

const currentView = ref<'day' | 'week' | 'month'>('week')
const currentDate = ref(new Date())
const appointments = ref<Appointment[]>([])
const loading = ref(false)

const statusColors: Record<string, string> = {
  scheduled: '#1a56db',
  in_progress: '#d97706',
  done: '#0d9488',
  cancelled: '#94a3b8',
}

const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const timeSlots = Array.from({ length: 11 }, (_, i) => i + 8)

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
onMounted(fetchAppointments)
</script>

<template>
  <div class="calendar-container">
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
        <v-btn variant="tonal" color="primary" size="small" @click="goToToday">
          Today
        </v-btn>
      </div>

      <div class="toolbar-right">
        <v-btn-toggle v-model="currentView" mandatory variant="outlined" density="compact" divided>
          <v-btn value="day" size="small">Day</v-btn>
          <v-btn value="week" size="small">Week</v-btn>
          <v-btn value="month" size="small">Month</v-btn>
        </v-btn-toggle>
      </div>
    </div>

    <div class="calendar-view day-view" v-if="currentView === 'day'">
      <div class="time-grid">
        <template v-for="hour in timeSlots" :key="hour">
          <div class="time-label">{{ hour.toString().padStart(2, '0') }}:00</div>
          <div class="time-slot">
            <div
              v-for="appt in getAppointmentsForTimeSlot(currentDate, hour)"
              :key="appt.id"
              class="appt-card"
              :style="{ borderLeftColor: statusColors[appt.status] }"
            >
              <div class="appt-time">{{ appt.assigned_time }}</div>
              <div class="appt-name">Patient #{{ appt.patient_id }}</div>
              <div class="appt-type">{{ appt.time_preference }} · {{ appt.status }}</div>
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
      <div class="week-grid">
        <template v-for="hour in timeSlots" :key="hour">
          <div class="week-time-label">{{ hour.toString().padStart(2, '0') }}:00</div>
          <div v-for="(day, dayIdx) in weekDaysInView" :key="`${hour}-${dayIdx}`" class="week-time-slot">
            <div
              v-for="appt in getAppointmentsForTimeSlot(day, hour)"
              :key="appt.id"
              class="appt-card"
              :style="{ borderLeftColor: statusColors[appt.status] }"
            >
              <div class="appt-time">{{ appt.assigned_time }}</div>
              <div class="appt-name">Patient #{{ appt.patient_id }}</div>
            </div>
          </div>
        </template>
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
              :style="{ borderLeftColor: statusColors[appt.status] }"
            >
              <div class="month-appt-time">{{ appt.assigned_time ?? '' }}</div>
              <div class="month-appt-name">Patient #{{ appt.patient_id }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.calendar-container {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.calendar-toolbar {
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  padding: 16px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.date-nav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.current-date {
  font-family: 'DM Serif Display', serif;
  font-size: 1.25rem;
  color: #1e293b;
  min-width: 280px;
}

.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.calendar-view {
  flex: 1;
  overflow-y: auto;
  padding: 20px 28px;
}

.time-grid {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 0;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.time-label {
  padding: 20px 16px;
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.75rem;
  font-weight: 500;
  color: #94a3b8;
  text-align: right;
  background: #f8fafc;
}

.time-slot {
  padding: 8px 16px;
  border-bottom: 1px solid #f1f5f9;
  min-height: 60px;
  position: relative;
}

.week-header {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.week-corner {
  background: transparent;
}

.week-day-header {
  text-align: center;
  padding: 12px 8px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.week-day-name {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  margin-bottom: 4px;
}

.week-day-date {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
}

.week-day-date.today {
  color: #fff;
  background: #0d9488;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.week-grid {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  gap: 0 8px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.week-time-label {
  padding: 8px 16px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.75rem;
  font-weight: 500;
  color: #94a3b8;
  text-align: right;
  background: #f8fafc;
}

.week-time-slot {
  padding: 4px;
  border-bottom: 1px solid #f1f5f9;
  border-left: 1px solid #f1f5f9;
  min-height: 50px;
  position: relative;
}

.month-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.month-day-header {
  text-align: center;
  padding: 10px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  background: #fff;
  border-radius: 8px 8px 0 0;
  border: 1px solid #e2e8f0;
  border-bottom: none;
}

.month-day {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 8px;
  min-height: 120px;
  display: flex;
  flex-direction: column;
}

.month-day.other-month {
  background: #f8fafc;
  opacity: 0.5;
}

.month-day.today {
  border: 2px solid #0d9488;
  box-shadow: 0 0 0 3px #e0f2f1;
}

.month-day-number {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 6px;
}

.month-appointments {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  overflow-y: auto;
}

.appt-card {
  background: linear-gradient(135deg, #1e3a5f 0%, #0f1e38 100%);
  border-radius: 6px;
  padding: 8px 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border-left: 4px solid;
  margin-bottom: 4px;
}

.appt-time {
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 2px;
}

.appt-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #fff;
}

.appt-type {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.7);
}

.month-appt-card {
  background: #1e293b;
  border-radius: 4px;
  padding: 3px 6px;
  border-left: 3px solid;
  margin-bottom: 2px;
}

.month-appt-time {
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.month-appt-name {
  font-size: 0.72rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
