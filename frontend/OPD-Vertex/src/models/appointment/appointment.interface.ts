export interface Appointment {
  id: number
  patient_id: number
  doctor_id: number
  appointment_date: string
  time_preference: 'AM' | 'PM'
  assigned_time: string | null
  status: 'scheduled' | 'in_progress' | 'done' | 'cancelled'
  notes: string | null
}
