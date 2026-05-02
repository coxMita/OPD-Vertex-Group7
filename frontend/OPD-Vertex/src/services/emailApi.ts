import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

export interface EmailSendRequest {
  to_email: string
  subject: string
  message: string
  is_html?: boolean
  document_title?: string | null
  document_content?: Record<string, unknown> | string | null
}

export const emailApi = {
  /**
   * POST /api/v1/email/send
   * Publishes an email job to the backend email queue.
   */
  async sendEmail(data: EmailSendRequest): Promise<void> {
    await apiClient.post('/api/v1/email/send', data)
  },

  /** POST /api/v1/email/otp/send — generate and send a 6-digit code to the given email. */
  async sendOtp(email: string): Promise<void> {
    await apiClient.post('/api/v1/email/otp/send', { email })
  },

  /** POST /api/v1/email/otp/verify — returns true if the code matches and has not expired. */
  async verifyOtp(email: string, code: string): Promise<boolean> {
    const res = await apiClient.post<{ valid: boolean }>('/api/v1/email/otp/verify', { email, code })
    return res.data.valid
  },
}
