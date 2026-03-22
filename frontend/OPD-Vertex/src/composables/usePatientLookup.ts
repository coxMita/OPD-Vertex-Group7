import { ref } from 'vue'
import { userApi, type PatientResponse } from '@/services/userApi'
import { appointmentApi } from '@/services/appointmentApi'
import type { Appointment } from '@/models/appointment/appointment.interface'

export function usePatientLookup() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const patient = ref<PatientResponse | null>(null)
  const appointments = ref<Appointment[]>([])

  async function lookupByEmail(email: string) {
    loading.value = true
    error.value = null
    patient.value = null
    appointments.value = []

    try {
      patient.value = await userApi.lookupPatientByEmail(email)
      appointments.value = await appointmentApi.getPatientAppointments(patient.value.id)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } }
      if (axiosErr.response?.status === 404) {
        error.value = 'No account found with this email address.'
      } else {
        error.value = 'Something went wrong. Please try again.'
      }
    } finally {
      loading.value = false
    }
  }

  return { loading, error, patient, appointments, lookupByEmail }
}