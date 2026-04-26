import apiClient from './apiClient'

export interface PrescriptionData {
  id: string
  consultation_id: string
  patient_id: string
  doctor_id: string
  status: 'draft' | 'approved' | 'sent'
  prescription_json: Record<string, unknown>
  summary_json: { summary?: string }
  clinical_alert?: string | null
  clinical_alerts?: string[]
  approved_at: string | null
}

/**
 * GET /api/v1/prescriptions/consultation/{consultationId}
 * Returns the prescription for a consultation, or throws 404 if not ready yet.
 */
export async function getPrescriptionByConsultation(
  consultationId: string,
): Promise<PrescriptionData> {
  const res = await apiClient.get<PrescriptionData>(
    `/api/v1/prescriptions/consultation/${consultationId}`,
  )
  return res.data
}

/**
 * Poll until prescription appears in DB (AI pipeline may take a few seconds).
 * Resolves with PrescriptionData or null if timed out.
 */
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
      // 404 = not ready yet, keep polling
      if (axiosErr.response?.status !== 404) throw err
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
  return null // timed out
}