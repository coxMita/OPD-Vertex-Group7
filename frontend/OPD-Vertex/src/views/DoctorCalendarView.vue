<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import { useCalendarNavigation } from '@/composables/useCalendarNavigation'
import { useCalendarAppointments } from '@/composables/useCalendarAppointments'
import CalendarToolbar from '@/components/DoctorCalendar/CalendarToolbar.vue'
import CalendarDayView from '@/components/DoctorCalendar/CalendarDayView.vue'
import CalendarWeekView from '@/components/DoctorCalendar/CalendarWeekView.vue'
import CalendarMonthView from '@/components/DoctorCalendar/CalendarMonthView.vue'
// import ConsultationView from '@/components/DoctorConsultation/ConsultationView.vue'

type DoctorSection = 'calendar' | 'consultations'
const activeSection = ref<DoctorSection>('calendar')

const SLOT_HEIGHT_WEEK = 50
const SLOT_HEIGHT_DAY = 56
const SCROLL_START_HOUR = 6

const doctorId = ref('00000000-0000-0000-0000-000000000001')

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
} = useCalendarNavigation()

const {
  appointments,
  loading,
  error,
  getApptStyle,
  getStatusIcon,
  getAppointmentsForDate,
  getAppointmentsForTimeSlot,
  fetchAppointments,
} = useCalendarAppointments(doctorId)

// Refs to child scroll containers
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

watch(visibleDates, () => fetchAppointments(visibleDates.value))
watch(currentView, scrollTo6am)

onMounted(() => {
  fetchAppointments(visibleDates.value)
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

    <!-- Doctor section tabs -->
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

    <!-- Calendar section -->
    <template v-if="activeSection === 'calendar'">
      <CalendarToolbar
        :currentDateDisplay="currentDateDisplay"
        :currentView="currentView"
        @navigate="navigate"
        @go-to-today="goToToday"
        @update:currentView="currentView = $event"
      />

      <CalendarDayView
        v-if="currentView === 'day'"
        ref="dayViewRef"
        :currentDate="currentDate"
        :getAppointmentsForTimeSlot="getAppointmentsForTimeSlot"
        :getApptStyle="getApptStyle"
        :getStatusIcon="getStatusIcon"
      />

      <CalendarWeekView
        v-if="currentView === 'week'"
        ref="weekViewRef"
        :weekDaysInView="weekDaysInView"
        :getAppointmentsForTimeSlot="getAppointmentsForTimeSlot"
        :getApptStyle="getApptStyle"
        :getStatusIcon="getStatusIcon"
        :isToday="isToday"
      />

      <CalendarMonthView
        v-if="currentView === 'month'"
        :monthDays="monthDays"
        :getAppointmentsForDate="getAppointmentsForDate"
        :getApptStyle="getApptStyle"
        :getStatusIcon="getStatusIcon"
        :isToday="isToday"
      />
    </template>

    <!-- Consultations section — swap comment when component is ready -->
    <template v-if="activeSection === 'consultations'">
      <!-- <ConsultationView :doctorId="doctorId" /> -->
      <div class="consultations-placeholder">
        <v-icon size="48" color="primary" class="mb-4">mdi-stethoscope</v-icon>
        <p class="text-h6 font-weight-medium">Consultations</p>
        <p class="text-medium-emphasis text-body-2">Connect your ConsultationView component here.</p>
      </div>
    </template>
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

/* ── Doctor section tabs ─────────────────────────────────── */
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

/* ── Consultations placeholder ───────────────────────────── */
.consultations-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
}
</style>