import axios from 'axios'
import type { Appointment } from '@/models/appointment/appointment.interface'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

export const appointmentApi = {
  /**
   * Fetch the ordered appointment queue for a doctor on a specific date.
   * Maps to: GET /api/v1/appointments/queue/day?doctor_id=...&appointment_date=...
   */
  getQueueForDay(doctorId: string, appointmentDate: string): Promise<Appointment[]> {
    return apiClient
      .get<Appointment[]>('/api/v1/appointments/queue/day', {
        params: {
          doctor_id: doctorId,
          appointment_date: appointmentDate,
        },
      })
      .then((res) => res.data)
  },

  /**
   * Fetch a single appointment by ID.
   * Maps to: GET /api/v1/appointments/{id}
   */
  getAppointment(appointmentId: string): Promise<Appointment> {
    return apiClient
      .get<Appointment>(`/api/v1/appointments/${appointmentId}`)
      .then((res) => res.data)
  },

  /**
   * Fetch all appointments for a patient.
   * Maps to: GET /api/v1/appointments/patient/{patient_id}
   */
  getPatientAppointments(patientId: string): Promise<Appointment[]> {
    return apiClient
      .get<Appointment[]>(`/api/v1/appointments/patient/${patientId}`)
      .then((res) => res.data)
  },

  /**
   * Reorder the appointment queue for a doctor on a specific date.
   * Redistributes assigned_time slots based on the new order.
   * Maps to: PATCH /api/v1/appointments/queue/reorder?doctor_id=...&appointment_date=...
   */
  reorderQueue(
    doctorId: string,
    appointmentDate: string,
    appointmentIds: string[],
  ): Promise<Appointment[]> {
    return apiClient
      .patch<Appointment[]>(
        '/api/v1/appointments/queue/reorder',
        { appointment_ids: appointmentIds },
        {
          params: {
            doctor_id: doctorId,
            appointment_date: appointmentDate,
          },
        },
      )
      .then((res) => res.data)
  },
}