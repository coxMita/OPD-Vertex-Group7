// src/services/transcriptionApi.ts
import { type AxiosError } from 'axios'
import { authClient } from './httpClient'

export interface TranscriptionResult {
  transcript: string
}

export interface TranscriptionError {
  detail?: string
}

async function transcribeFile(
  file: File,
  consultationId: string,
  onUploadProgress?: (percent: number) => void,
): Promise<TranscriptionResult> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await authClient.post<{ transcript?: string; text?: string }>(
    '/api/v1/transcription/',
    formData,
    {
      params: { consultation_id: consultationId },
      headers: { 'Content-Type': 'multipart/form-data' },
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