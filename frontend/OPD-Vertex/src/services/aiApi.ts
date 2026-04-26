import apiClient from './apiClient'

export interface AiGatewayResponse {
  summary: string
  prescription: Record<string, unknown>
  clinical_alerts: string[]
}

export async function processTranscriptWithAi(transcript: string): Promise<AiGatewayResponse> {
  const response = await apiClient.post<AiGatewayResponse>('/api/v1/ai/prompt', {
    transcript,
  }, {
    timeout: 300_000,
  })
  return response.data
}
