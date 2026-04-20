import apiClient from './apiClient'
import type { AxiosError } from 'axios'

export interface TranscriptionResult {
  transcript: string
}

export interface TranscriptionError {
  detail?: string
}

/**
 * POST /api/v1/transcription/?consultation_id={consultationId}
 * Accepts a WAV audio file and returns the transcript text.
 */
async function transcribeFile(
  file: File,
  consultationId: string,
  onUploadProgress?: (percent: number) => void,
): Promise<TranscriptionResult> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post<{ transcript?: string; text?: string }>(
    '/api/v1/transcription/',
    formData,
    {
      params: { consultation_id: consultationId },
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000,
      onUploadProgress(ev) {
        if (onUploadProgress && ev.total) {
          onUploadProgress(Math.round((ev.loaded * 100) / ev.total))
        }
      },
    },
  )

  const text =
    response.data.transcript ?? response.data.text ?? JSON.stringify(response.data)

  return { transcript: text }
}

function formatError(err: unknown, gatewayUrl: string): string {
  const axiosErr = err as AxiosError<TranscriptionError>
  if (axiosErr.response) {
    const detail = axiosErr.response.data?.detail
    // detail may be an array (FastAPI validation errors) or a string
    if (Array.isArray(detail)) {
      return `Validation error: ${detail.map((d: Record<string, unknown>) => d.msg ?? d).join(', ')}`
    }
    return detail
      ? `Service error: ${detail}`
      : `HTTP ${axiosErr.response.status}: ${axiosErr.response.statusText}`
  }
  if (axiosErr.request) {
    return `No response from gateway — is Docker running? (${gatewayUrl})`
  }
  return axiosErr.message ?? 'Unknown error'
}

export const transcriptionApi = {
  transcribeFile,
  formatError,
  gatewayUrl: (import.meta.env.VITE_GATEWAY_URL as string | undefined) ?? 'http://localhost:8080',
}