import { ref } from 'vue'
import type { Appointment } from '@/models/appointment/appointment.interface'
import { appointmentApi } from '@/services/appointmentApi'

export interface DragOverSlot {
  date: string  // "YYYY-MM-DD"
  hour: number
}

export function useCalendarDragDrop(appointments: { value: Appointment[] }) {
  const editMode = ref(false)
  const draggingId = ref<string | null>(null)
  const dragOverSlot = ref<DragOverSlot | null>(null)

  function toggleEditMode() {
    editMode.value = !editMode.value
    // Clear any leftover drag state when toggling off
    if (!editMode.value) {
      draggingId.value = null
      dragOverSlot.value = null
    }
  }

  function onDragStart(appointmentId: string) {
    if (!editMode.value) return
    draggingId.value = appointmentId
  }

  function onDragOver(date: string, hour: number) {
    if (!editMode.value || !draggingId.value) return
    dragOverSlot.value = { date, hour }
  }

  function onDragLeave() {
    dragOverSlot.value = null
  }

  function isDragOver(date: string, hour: number): boolean {
    return (
      dragOverSlot.value?.date === date &&
      dragOverSlot.value?.hour === hour
    )
  }

async function onDrop(
    targetDate: string,
    targetHour: number,
    doctorId: string,
  ) {
    if (!editMode.value || !draggingId.value) return

    const apptId = draggingId.value
    draggingId.value = null
    dragOverSlot.value = null

    const appt = appointments.value.find((a) => a.id === apptId)
    if (!appt) return

    const previousTime = appt.assigned_time
    const previousDate = appt.appointment_date

    // All the appointments from target day, without the one we are moving
    // sorted by the current hour
    const otherAppts = appointments.value
    .filter((a) =>
        a.appointment_date === targetDate &&
        a.status !== 'cancelled' &&
        a.id !== apptId
    )
    .sort((a, b) => {
        const aHour = parseInt(a.assigned_time?.split(':')[0] ?? '0')
        const bHour = parseInt(b.assigned_time?.split(':')[0] ?? '0')
        return aHour - bHour
    })

    // Inserts after appointmets with hour < targethour
    const insertIndex = otherAppts.findIndex((a) => {
    const hour = parseInt(a.assigned_time?.split(':')[0] ?? '0')
    return hour > targetHour
    })

    const reordered = [...otherAppts]
    if (insertIndex === -1) {
    reordered.push(appt)
    } else {
    reordered.splice(insertIndex, 0, appt)
    }

    const orderedIds = reordered.map((a) => a.id)

    // --- Backend call ---
    console.log('orderedIds trimis la backend:', orderedIds)
    console.log('ore curente:', reordered.map(a => ({ id: a.id.slice(0,8), time: a.assigned_time, notes: a.notes })))
    try {
      const updated = await appointmentApi.reorderQueue(doctorId, targetDate, orderedIds)
      // gets each appointmetn with the response from backend
      for (const serverAppt of updated) {
        const idx = appointments.value.findIndex((a) => a.id === serverAppt.id)
        if (idx !== -1) {
          appointments.value[idx] = { ...appointments.value[idx], ...serverAppt }
        }
      }
    } catch (err) {
      console.error('Reorder failed, rolling back', err)
      appt.assigned_time = previousTime
      appt.appointment_date = previousDate
    }
  }

  return {
    editMode,
    draggingId,
    dragOverSlot,
    toggleEditMode,
    onDragStart,
    onDragOver,
    onDragLeave,
    onDrop,
    isDragOver,
  }
}