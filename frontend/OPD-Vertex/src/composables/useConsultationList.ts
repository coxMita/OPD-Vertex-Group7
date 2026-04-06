import { ref } from 'vue'
import type { Consultation } from '@/models/consultation/consultation.interface'
import { consultationApi } from '@/services/consultationApi'

export function useConsultationList() {
  const consultations = ref<Consultation[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedConsultation = ref<Consultation | null>(null)

  async function fetchConsultations(doctorId: string) {
    loading.value = true
    error.value = null
    try {
      consultations.value = await consultationApi.getConsultationsForDoctor(doctorId)
    } catch (err) {
      console.warn('Failed to fetch consultations. Using mock data instead.', err)
      error.value = 'Could not load from backend. Using mock consultation data for testing.'
      
      // Fallback mock data so you can test the UI without the backend services!
      consultations.value = [
        {
          id: 'test-consultation-1234',
          appointment_id: 'app-999',
          doctor_id: doctorId,
          start_time: '14:00:00',
          end_time: null,
          status: 'ACTIVE',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ]
    } finally {
      loading.value = false
    }
  }

  function selectConsultation(consultation: Consultation) {
    selectedConsultation.value = consultation
  }

  return {
    consultations,
    loading,
    error,
    selectedConsultation,
    fetchConsultations,
    selectConsultation,
  }
}