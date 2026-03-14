<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import { useCalendarNavigation } from '@/composables/useCalendarNavigation'
import { useCalendarAppointments } from '@/composables/useCalendarAppointments'
import CalendarToolbar from '@/components/DoctorCalendar/CalendarToolbar.vue'
import CalendarDayView from '@/components/DoctorCalendar/CalendarDayView.vue'
import CalendarWeekView from '@/components/DoctorCalendar/CalendarWeekView.vue'
import CalendarMonthView from '@/components/DoctorCalendar/CalendarMonthView.vue'

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
</style>