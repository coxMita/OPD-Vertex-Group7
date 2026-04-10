// src/services/consultationApi.ts
import type { Consultation } from '@/models/consultation/consultation.interface'
import { authClient } from './httpClient'

export const consultationApi = {
  // Toate rutele de consultații sunt protejate — doar doctor
  getConsultationsForDoctor(doctorId: string): Promise<Consultation[]> {
    return authClient
      .get<Consultation[]>(`/api/v1/consultations/doctor/${doctorId}`)
      .then((res) => res.data)
  },

  getConsultation(consultationId: string): Promise<Consultation> {
    return authClient
      .get<Consultation>(`/api/v1/consultations/${consultationId}`)
      .then((res) => res.data)
  },
}