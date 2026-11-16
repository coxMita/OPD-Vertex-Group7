import apiClient from './apiClient'
import type {
  Appointment,
  AppointmentStatus,
  TimePreference,
} from '@/models/appointment/appointment.interface'
import type { Consultation } from '@/models/consultation/consultation.interface'

/** Dev/demo endpoints used by the /admin page. */

export interface StartSessionResult {
  time_preference: TimePreference
  appointment_date: string
  handed_off: number
}

export interface ClearResult {
  message: string
  deleted: number
}

export const adminApi = {
  /** GET /api/v1/appointments/dev/all?appointment_date=YYYY-MM-DD */
  listAppointments(appointmentDate?: string): Promise<Appointment[]> {
    return apiClient
      .get<Appointment[]>('/api/v1/appointments/dev/all', {
        params: appointmentDate ? { appointment_date: appointmentDate } : {},
      })
      .then((res) => res.data)
  },

  /** POST /api/v1/appointments/dev/start-session — runs the AM/PM cron job now. */
  startSession(timePreference: TimePreference, appointmentDate: string): Promise<StartSessionResult> {
    return apiClient
      .post<StartSessionResult>('/api/v1/appointments/dev/start-session', null, {
        params: { time_preference: timePreference, appointment_date: appointmentDate },
      })
      .then((res) => res.data)
  },

  /** PATCH /api/v1/appointments/{id}/status */
  setStatus(appointmentId: string, status: AppointmentStatus): Promise<Appointment> {
    return apiClient
      .patch<Appointment>(`/api/v1/appointments/${appointmentId}/status`, { status })
      .then((res) => res.data)
  },

  /** GET /api/v1/consultations/appointment/{id} — null when none exists yet. */
  getConsultationForAppointment(appointmentId: string): Promise<Consultation | null> {
    return apiClient
      .get<Consultation>(`/api/v1/consultations/appointment/${appointmentId}`, {
        validateStatus: (s) => s === 200 || s === 404,
      })
      .then((res) => (res.status === 200 ? res.data : null))
  },

  clearAppointments(): Promise<ClearResult> {
    return apiClient.delete<ClearResult>('/api/v1/appointments/dev').then((res) => res.data)
  },

  clearConsultations(): Promise<ClearResult> {
    return apiClient.delete<ClearResult>('/api/v1/consultations/dev').then((res) => res.data)
  },

  clearPrescriptions(): Promise<ClearResult> {
    return apiClient.delete<ClearResult>('/api/v1/prescriptions/dev').then((res) => res.data)
  },
}
