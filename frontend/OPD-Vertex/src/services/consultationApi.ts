import axios from 'axios'
import type { Consultation } from '@/models/consultation/consultation.interface'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

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