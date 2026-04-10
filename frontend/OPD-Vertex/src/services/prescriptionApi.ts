// src/services/prescriptionApi.ts
import { authClient } from './httpClient'

export interface PrescriptionData {
  id: string
  consultation_id: string
  patient_id: string
  doctor_id: string
  status: 'draft' | 'approved' | 'sent'
  prescription_json: Record<string, unknown>
  summary_json: { summary?: string }
  approved_at: string | null
}

export async function getPrescriptionByConsultation(
  consultationId: string,
): Promise<PrescriptionData> {
  const res = await authClient.get<PrescriptionData>(
    `/api/v1/prescriptions/consultation/${consultationId}`,
  )
  return res.data
}

export async function pollPrescription(
  consultationId: string,
  options: { intervalMs?: number; maxAttempts?: number } = {},
): Promise<PrescriptionData | null> {
  const { intervalMs = 5000, maxAttempts = 120 } = options

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await getPrescriptionByConsultation(consultationId)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } }
      if (axiosErr.response?.status !== 404) throw err
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
  return null
}