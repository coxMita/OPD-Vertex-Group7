import axios from 'axios'
import type { Appointment } from '@/models/appointment/appointment.interface'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

export interface CreateAppointmentRequest {
  patient_id: string
  doctor_id: string
  appointment_date: string   // "YYYY-MM-DD"
  time_preference: 'AM' | 'PM'
  notes?: string | null
}

export const appointmentApi = {
  getQueueForDay(doctorId: string, appointmentDate: string): Promise<Appointment[]> {
    return apiClient
      .get<Appointment[]>('/api/v1/appointments/queue/day', {
        params: { doctor_id: doctorId, appointment_date: appointmentDate },
      })
      .then((res) => res.data)
  },

  getAppointment(appointmentId: string): Promise<Appointment> {
    return apiClient
      .get<Appointment>(`/api/v1/appointments/${appointmentId}`)
      .then((res) => res.data)
  },

  getPatientAppointments(patientId: string): Promise<Appointment[]> {
    return apiClient
      .get<Appointment[]>(`/api/v1/appointments/patient/${patientId}`)
      .then((res) => res.data)
  },

  createAppointment(data: CreateAppointmentRequest): Promise<Appointment> {
    return apiClient
      .post<Appointment>('/api/v1/appointments', data)
      .then((res) => res.data)
  },

  reorderQueue(
    doctorId: string,
    appointmentDate: string,
    appointmentIds: string[],
  ): Promise<Appointment[]> {
    return apiClient
      .patch<Appointment[]>(
        '/api/v1/appointments/queue/reorder',
        { appointment_ids: appointmentIds },
        { params: { doctor_id: doctorId, appointment_date: appointmentDate } },
      )
      .then((res) => res.data)
  },
}