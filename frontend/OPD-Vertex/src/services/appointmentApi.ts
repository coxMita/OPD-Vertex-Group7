// src/services/appointmentApi.ts
import type { Appointment } from '@/models/appointment/appointment.interface'
import { authClient, publicClient } from './httpClient'

export interface CreateAppointmentRequest {
  patient_id: string
  doctor_id: string
  appointment_date: string
  time_preference: 'AM' | 'PM'
  notes?: string | null
}

export const appointmentApi = {
  // ── PUBLIC (pacient) ──────────────────────────────────────────
  createAppointment(data: CreateAppointmentRequest): Promise<Appointment> {
    return publicClient
      .post<Appointment>('/api/v1/appointments', data)
      .then((res) => res.data)
  },

  getPatientAppointments(patientId: string): Promise<Appointment[]> {
    return publicClient
      .get<Appointment[]>(`/api/v1/appointments/patient/${patientId}`)
      .then((res) => res.data)
  },

  // ── PROTECTED (doctor) ────────────────────────────────────────
  getQueueForDay(doctorId: string, appointmentDate: string): Promise<Appointment[]> {
    return authClient
      .get<Appointment[]>('/api/v1/appointments/queue/day', {
        params: { doctor_id: doctorId, appointment_date: appointmentDate },
      })
      .then((res) => res.data)
  },

  getAppointment(appointmentId: string): Promise<Appointment> {
    return authClient
      .get<Appointment>(`/api/v1/appointments/${appointmentId}`)
      .then((res) => res.data)
  },

  reorderQueue(
    doctorId: string,
    appointmentDate: string,
    appointmentIds: string[],
  ): Promise<Appointment[]> {
    return authClient
      .patch<Appointment[]>(
        '/api/v1/appointments/queue/reorder',
        { appointment_ids: appointmentIds },
        { params: { doctor_id: doctorId, appointment_date: appointmentDate } },
      )
      .then((res) => res.data)
  },
}