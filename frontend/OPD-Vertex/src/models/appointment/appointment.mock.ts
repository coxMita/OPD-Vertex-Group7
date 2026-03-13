/**
 * Mock appointment data for local UI development.
 * Dates are relative to the current week (week of 2026-03-09).
 * Set VITE_USE_MOCK=true in .env.local to use this instead of the real API.
 */

import type { Appointment } from './appointment.interface'

export const mockAppointments: Appointment[] = [
  { id: 1, patient_id: 101, doctor_id: 1, appointment_date: '2026-03-09', time_preference: 'AM', assigned_time: '08:00', status: 'done', notes: null },
  { id: 2, patient_id: 102, doctor_id: 1, appointment_date: '2026-03-09', time_preference: 'AM', assigned_time: '09:00', status: 'done', notes: 'Follow-up required' },
  { id: 3, patient_id: 103, doctor_id: 1, appointment_date: '2026-03-09', time_preference: 'PM', assigned_time: '14:00', status: 'cancelled', notes: 'Patient did not show' },
  { id: 4, patient_id: 104, doctor_id: 1, appointment_date: '2026-03-10', time_preference: 'AM', assigned_time: '08:30', status: 'done', notes: null },
  { id: 5, patient_id: 105, doctor_id: 1, appointment_date: '2026-03-10', time_preference: 'AM', assigned_time: '10:00', status: 'done', notes: null },
  { id: 6, patient_id: 106, doctor_id: 1, appointment_date: '2026-03-10', time_preference: 'PM', assigned_time: '15:00', status: 'done', notes: null },
  { id: 7, patient_id: 107, doctor_id: 1, appointment_date: '2026-03-11', time_preference: 'AM', assigned_time: '09:00', status: 'done', notes: null },
  { id: 8, patient_id: 108, doctor_id: 1, appointment_date: '2026-03-11', time_preference: 'PM', assigned_time: '13:00', status: 'done', notes: null },
  { id: 9, patient_id: 109, doctor_id: 1, appointment_date: '2026-03-12', time_preference: 'AM', assigned_time: '08:00', status: 'done', notes: null },
  { id: 10, patient_id: 110, doctor_id: 1, appointment_date: '2026-03-12', time_preference: 'AM', assigned_time: '11:00', status: 'done', notes: null },
  { id: 11, patient_id: 111, doctor_id: 1, appointment_date: '2026-03-12', time_preference: 'PM', assigned_time: '16:00', status: 'cancelled', notes: null },
  { id: 12, patient_id: 112, doctor_id: 1, appointment_date: '2026-03-13', time_preference: 'AM', assigned_time: '08:00', status: 'done', notes: null },
  { id: 13, patient_id: 113, doctor_id: 1, appointment_date: '2026-03-13', time_preference: 'AM', assigned_time: '09:00', status: 'in_progress', notes: null },
  { id: 14, patient_id: 114, doctor_id: 1, appointment_date: '2026-03-13', time_preference: 'AM', assigned_time: '10:00', status: 'scheduled', notes: 'New patient' },
  { id: 15, patient_id: 115, doctor_id: 1, appointment_date: '2026-03-13', time_preference: 'AM', assigned_time: '11:00', status: 'scheduled', notes: null },
  { id: 16, patient_id: 116, doctor_id: 1, appointment_date: '2026-03-13', time_preference: 'PM', assigned_time: '14:00', status: 'scheduled', notes: null },
  { id: 17, patient_id: 117, doctor_id: 1, appointment_date: '2026-03-13', time_preference: 'PM', assigned_time: '15:00', status: 'scheduled', notes: null },
  { id: 18, patient_id: 118, doctor_id: 1, appointment_date: '2026-03-13', time_preference: 'PM', assigned_time: '17:00', status: 'scheduled', notes: null },
  { id: 19, patient_id: 119, doctor_id: 1, appointment_date: '2026-03-14', time_preference: 'AM', assigned_time: '09:00', status: 'scheduled', notes: null },
  { id: 20, patient_id: 120, doctor_id: 1, appointment_date: '2026-03-14', time_preference: 'AM', assigned_time: '10:00', status: 'scheduled', notes: null },
]

export function getMockAppointmentsForDay(doctorId: number, date: string): Appointment[] {
  return mockAppointments.filter((appointment) => appointment.doctor_id === doctorId && appointment.appointment_date === date)
}
