import { ref, computed } from 'vue'

export type CalendarView = 'day' | 'week' | 'month'

export const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
export const TIME_SLOTS = Array.from({ length: 24 }, (_, i) => i)

export function useCalendarNavigation() {
  const currentView = ref<CalendarView>('week')
  const currentDate = ref(new Date())

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

  const visibleDates = computed<Date[]>(() => {
    if (currentView.value === 'day') return [currentDate.value]
    if (currentView.value === 'week') return weekDaysInView.value
    return monthDays.value.filter((d) => !d.isOtherMonth).map((d) => d.date)
  })

  return {
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
    getWeekStart,
  }
}