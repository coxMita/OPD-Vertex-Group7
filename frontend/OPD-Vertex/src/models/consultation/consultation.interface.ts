export type ConsultationStatus = 'active' | 'completed'

export interface Consultation {
  id: string           // uuid
  appointment_id: string
  doctor_id: string
  start_time: string | null   // "HH:MM:SS" or null
  end_time: string | null
  status: ConsultationStatus
  created_at: string
  updated_at: string
}