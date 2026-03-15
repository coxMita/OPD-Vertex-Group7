import axios, { type AxiosError } from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_GATEWAY_URL ?? 'http://localhost:8000',
  timeout: 120_000, // Whisper can be slow on large files
})

export interface TranscriptionResult {
  transcript: string
}

export interface TranscriptionError {
  detail?: string
}

/**
 * POST /api/v1/transcription/
 * Accepts a WAV audio file and returns the transcript text.
 */
async function transcribeFile(
  file: File,
  onUploadProgress?: (percent: number) => void,
): Promise<TranscriptionResult> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post<{ transcript?: string; text?: string }>(
    '/api/v1/transcription/',
    formData,
    {
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

/**
 * Formats an AxiosError into a human-readable message, consistent across
 * TranscriptionUploadCard and RecordingCard.
 */
function formatError(err: unknown, gatewayUrl: string): string {
  const axiosErr = err as AxiosError<TranscriptionError>
  if (axiosErr.response) {
    const detail = axiosErr.response.data?.detail
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
  /** Exposed so components can show the URL in error messages without re-reading env */
  gatewayUrl: (import.meta.env.VITE_GATEWAY_URL as string | undefined) ?? 'http://localhost:8000',
}