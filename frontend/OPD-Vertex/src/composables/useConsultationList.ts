import { ref } from 'vue'
import type { Consultation } from '@/models/consultation/consultation.interface'
import { consultationApi } from '@/services/consultationApi'

export function useConsultationList() {
  const consultations = ref<Consultation[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedConsultation = ref<Consultation | null>(null)

  async function fetchConsultations(doctorId: string) {
    if (!doctorId) {
      consultations.value = []
      selectedConsultation.value = null
      error.value = null
      loading.value = false
      return
    }

    loading.value = true
    error.value = null
    try {
      consultations.value = await consultationApi.getConsultationsForDoctor(doctorId)
    } catch (err) {
      console.error('Failed to fetch consultations:', err)
      error.value = 'Could not load consultations. Is the backend running?'
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
