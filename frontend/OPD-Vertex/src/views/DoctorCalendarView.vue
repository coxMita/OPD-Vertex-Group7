<script setup lang="ts">
import { ref, watch, onMounted, nextTick, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCalendarNavigation } from '@/composables/useCalendarNavigation'
import { useCalendarAppointments } from '@/composables/useCalendarAppointments'
import { useCalendarDragDrop } from '@/composables/useCalendarDragDrop'
import CalendarToolbar from '@/components/DoctorCalendar/CalendarToolbar.vue'
import CalendarDayView from '@/components/DoctorCalendar/CalendarDayView.vue'
import CalendarWeekView from '@/components/DoctorCalendar/CalendarWeekView.vue'
import CalendarMonthView from '@/components/DoctorCalendar/CalendarMonthView.vue'
import AppointmentDetailModal from '@/components/DoctorCalendar/AppointmentDetailModal.vue'
import ConsultationView from '@/views/ConsultationView.vue'
import type { Appointment } from '@/models/appointment/appointment.interface'

const authStore = useAuthStore()
type DoctorSection = 'calendar' | 'consultations'
const activeSection = ref<DoctorSection>('calendar')

const SLOT_HEIGHT_WEEK = 50
const SLOT_HEIGHT_DAY = 56
const SCROLL_START_HOUR = 6

const doctorId = computed(() => authStore.doctorId ?? '')

const {
  currentView,
  currentDate,
  currentDateDisplay,
  weekDaysInView,
  monthDays,
  visibleDates,
  navigate,
  goToToday,
  isToday,
  formatDate,
} = useCalendarNavigation()

const {
  appointments,
  loading,
  error,
  getApptStyle,
  getStatusIcon,
  getPatientName,
  getAppointmentsForDate,
  getAppointmentsForTimeSlot,
  fetchAppointments,
} = useCalendarAppointments(doctorId)

const {
  editMode,
  draggingId,
  toggleEditMode,
  onDragStart,
  onDragOver,
  onDragLeave,
  onDrop,
  isDragOver,
} = useCalendarDragDrop(appointments)

const modalOpen = ref(false)
const selectedAppointment = ref<Appointment | null>(null)

function handleSelectAppointment(id: string) {
  const appt = appointments.value.find((a) => a.id === id) ?? null
  selectedAppointment.value = appt
  modalOpen.value = true
}

function handleDrop(date: string, hour: number) {
  onDrop(date, hour, doctorId.value)
}

const dayViewRef = ref<InstanceType<typeof CalendarDayView> | null>(null)
const weekViewRef = ref<InstanceType<typeof CalendarWeekView> | null>(null)

function scrollTo6am() {
  nextTick(() => {
    if (currentView.value === 'week' && weekViewRef.value?.weekBodyRef) {
      weekViewRef.value.weekBodyRef.scrollTop = SCROLL_START_HOUR * SLOT_HEIGHT_WEEK
    } else if (currentView.value === 'day' && dayViewRef.value?.dayViewRef) {
      dayViewRef.value.dayViewRef.scrollTop = SCROLL_START_HOUR * SLOT_HEIGHT_DAY
    }
  })
}

watch(visibleDates, () => {
  if (doctorId.value) {
    fetchAppointments(visibleDates.value)
  }
})

watch(
  () => authStore.doctorId,
  (newId) => {
    if (newId) {
      fetchAppointments(visibleDates.value)
    }
  },
)

onMounted(() => {
  if (doctorId.value) {
    fetchAppointments(visibleDates.value)
  }
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

    <v-expand-transition>
      <div v-if="editMode" class="edit-banner">
        <v-icon size="16" class="mr-2">mdi-drag</v-icon>
        Edit mode active — drag appointments to reschedule. Click any appointment to view details.
      </div>
    </v-expand-transition>

    <div class="doctor-tabs">
      <button
        class="doctor-tab"
        :class="{ active: activeSection === 'calendar' }"
        @click="activeSection = 'calendar'"
      >
        <v-icon size="16" class="tab-icon">mdi-calendar-month</v-icon>
        Calendar
      </button>
      <button
        class="doctor-tab"
        :class="{ active: activeSection === 'consultations' }"
        @click="activeSection = 'consultations'"
      >
        <v-icon size="16" class="tab-icon">mdi-stethoscope</v-icon>
        Consultations
      </button>
    </div>

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

    <template v-if="activeSection === 'calendar'">
      <CalendarToolbar
        :currentDateDisplay="currentDateDisplay"
        :currentView="currentView"
        :editMode="editMode"
        @navigate="navigate"
        @go-to-today="goToToday"
        @update:currentView="currentView = $event"
        @toggle-edit-mode="toggleEditMode"
      />

      <CalendarDayView
        v-if="currentView === 'day'"
        ref="dayViewRef"
        :currentDate="currentDate"
        :getAppointmentsForTimeSlot="getAppointmentsForTimeSlot"
        :getApptStyle="getApptStyle"
        :getStatusIcon="getStatusIcon"
        :getPatientName="getPatientName"
        :editMode="editMode"
        :draggingId="draggingId"
        :isDragOver="isDragOver"
        :formatDate="formatDate"
        @dragstart="onDragStart"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="handleDrop"
        @select="handleSelectAppointment"
      />

      <CalendarWeekView
        v-if="currentView === 'week'"
        ref="weekViewRef"
        :weekDaysInView="weekDaysInView"
        :getAppointmentsForTimeSlot="getAppointmentsForTimeSlot"
        :getApptStyle="getApptStyle"
        :getStatusIcon="getStatusIcon"
        :getPatientName="getPatientName"
        :isToday="isToday"
        :editMode="editMode"
        :draggingId="draggingId"
        :isDragOver="isDragOver"
        :formatDate="formatDate"
        @dragstart="onDragStart"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="handleDrop"
        @select="handleSelectAppointment"
      />

      <CalendarMonthView
        v-if="currentView === 'month'"
        :monthDays="monthDays"
        :getAppointmentsForDate="getAppointmentsForDate"
        :getApptStyle="getApptStyle"
        :getStatusIcon="getStatusIcon"
        :getPatientName="getPatientName"
        :isToday="isToday"
        @select="handleSelectAppointment"
      />
    </template>

    <template v-if="activeSection === 'consultations'">
      <ConsultationView :doctorId="doctorId" />
    </template>

    <AppointmentDetailModal
      v-model="modalOpen"
      :appointment="selectedAppointment"
    />
  </div>
</template>

<style scoped>
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
.edit-banner {
  background: rgba(var(--v-theme-warning), 0.1);
  border-bottom: 1px solid rgba(var(--v-theme-warning), 0.25);
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.78rem;
  font-weight: 500;
  padding: 6px 24px;
  display: flex;
  align-items: center;
  opacity: 0.85;
  flex-shrink: 0;
}
.doctor-tabs {
  display: flex;
  align-items: flex-end;
  gap: 0;
  padding: 0 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}
.doctor-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 14px 18px 12px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.5);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color 0.18s ease, border-color 0.18s ease;
  margin-bottom: -1px;
  letter-spacing: 0.01em;
  white-space: nowrap;
}
.doctor-tab:hover {
  color: rgba(var(--v-theme-on-surface), 0.85);
}
.doctor-tab.active {
  color: rgb(var(--v-theme-primary));
  border-bottom-color: rgb(var(--v-theme-primary));
  font-weight: 600;
}
.doctor-tab .tab-icon {
  opacity: 0.75;
  transition: opacity 0.18s ease;
}
.doctor-tab.active .tab-icon {
  opacity: 1;
}
</style>