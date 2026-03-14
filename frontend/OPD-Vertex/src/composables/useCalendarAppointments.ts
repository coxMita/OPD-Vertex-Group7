import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'
import type { Appointment } from '@/models/appointment/appointment.interface'
import { appointmentApi } from '@/services/appointmentApi'

export type StatusKey = 'scheduled' | 'handed_off' | 'completed' | 'cancelled'

interface StatusCfg {
  lightBg: string
  darkBg: string
  lightText: string
  darkText: string
  border: string
  icon: string
  label: string
}

export const STATUS_CONFIG: Record<StatusKey, StatusCfg> = {
  scheduled: {
    lightBg: '#dbeafe', darkBg: '#1e3558',
    lightText: '#1d4ed8', darkText: '#93c5fd',
    border: '#3b82f6', icon: 'mdi-clock-outline', label: 'Scheduled',
  },
  handed_off: {
    lightBg: '#fef3c7', darkBg: '#3d1f00',
    lightText: '#b45309', darkText: '#fcd34d',
    border: '#f59e0b', icon: 'mdi-progress-clock', label: 'In Progress',
  },
  completed: {
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

export function useCalendarAppointments(doctorId: { value: string }) {
  const vuetifyTheme = useTheme()
  const isDark = computed(() => vuetifyTheme.current.value.dark)

  const appointments = ref<Appointment[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  function formatDate(date: Date): string {
    const year = date.getFullYear()
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  function getApptStyle(status: string) {
    const cfg = STATUS_CONFIG[status as StatusKey] ?? STATUS_CONFIG.scheduled
    return {
      background: isDark.value ? cfg.darkBg : cfg.lightBg,
      color: isDark.value ? cfg.darkText : cfg.lightText,
      borderLeftColor: cfg.border,
    }
  }

  function getStatusIcon(status: string): string {
    return STATUS_CONFIG[status as StatusKey]?.icon ?? 'mdi-calendar'
  }

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

  async function fetchAppointments(visibleDates: Date[]) {
    loading.value = true
    error.value = null
    try {
      const results = await Promise.all(
        visibleDates.map((date) =>
          appointmentApi.getQueueForDay(doctorId.value, formatDate(date))
        ),
      )
      appointments.value = results.flat()
    } catch (err) {
      console.error('Failed to fetch appointments:', err)
      error.value = 'Could not load appointments. Is the backend running?'
      appointments.value = []
    } finally {
      loading.value = false
    }
  }

  return {
    appointments,
    loading,
    error,
    formatDate,
    getApptStyle,
    getStatusIcon,
    getAppointmentsForDate,
    getAppointmentsForTimeSlot,
    fetchAppointments,
  }
}