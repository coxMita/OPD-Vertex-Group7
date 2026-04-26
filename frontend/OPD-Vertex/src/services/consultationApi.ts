import apiClient from './apiClient'
import type { Consultation } from '@/models/consultation/consultation.interface'

export const consultationApi = {
  /**
   * Fetch active consultations for a specific doctor.
   * Maps to: GET /api/v1/consultations?doctor_id=...
   */
  getConsultationsForDoctor(doctorId: string): Promise<Consultation[]> {
    return apiClient
      .get<Consultation[]>(`/api/v1/consultations/doctor/${doctorId}`)
      .then((res) => res.data)
  },

  /**
   * Fetch a single consultation by ID.
   * Maps to: GET /api/v1/consultations/{id}
   */
  getConsultation(consultationId: string): Promise<Consultation> {
    return apiClient
      .get<Consultation>(`/api/v1/consultations/${consultationId}`)
      .then((res) => res.data)
  },
}