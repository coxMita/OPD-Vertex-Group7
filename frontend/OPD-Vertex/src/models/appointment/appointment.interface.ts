export type TimePreference = 'AM' | 'PM'
 
export type AppointmentStatus = 'scheduled' | 'handed_off' | 'completed' | 'cancelled'
 
export interface Appointment {
  id: string                     // uuid
  patient_id: string             // uuid
  doctor_id: string              // uuid
  appointment_date: string       // "YYYY-MM-DD"
  time_preference: TimePreference
  assigned_time: string | null   // "HH:MM:SS" or null
  status: AppointmentStatus
  notes: string | null
}