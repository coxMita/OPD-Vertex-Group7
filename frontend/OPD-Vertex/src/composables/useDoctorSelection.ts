import { ref, computed, watch } from 'vue'
import { userApi } from '@/services/userApi'
import type { PatientFormData } from './usePatientForm'

export interface Doctor {
  id: string
  name: string
  specialty: string
  avatar: string
}

export const DEPARTMENTS = [
  'General Practice',
  'Cardiology',
  'Dermatology',
  'Neurology',
  'Orthopedics',
  'Pediatrics',
  'Psychiatry',
]

// Mapare department → specialization (exact cum e în user-service)
const DEPARTMENT_TO_SPECIALIZATION: Record<string, string> = {
  'General Practice': 'General Practice',
  'Cardiology': 'Cardiology',
  'Dermatology': 'Dermatology',
  'Neurology': 'Neurology',
  'Orthopedics': 'Orthopedics',
  'Pediatrics': 'Pediatrics',
  'Psychiatry': 'Psychiatry',
}

function getAvatarInitials(firstName: string, lastName: string): string {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
}

export function useDoctorSelection(form: { value: PatientFormData }) {
  const allDoctors = ref<Doctor[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAllDoctors() {
    loading.value = true
    error.value = null
    try {
      const data = await userApi.getAllDoctors()
      allDoctors.value = data.map((d) => ({
        id: d.id,
        name: `Dr. ${d.first_name} ${d.last_name}`,
        specialty: d.specialization,
        avatar: getAvatarInitials(d.first_name, d.last_name),
      }))
    } catch (err) {
      console.error('Failed to fetch doctors:', err)
      error.value = 'Could not load doctors.'
      allDoctors.value = []
    } finally {
      loading.value = false
    }
  }

  // Reset selected doctor when department changes
  watch(
    () => form.value.department,
    () => {
      form.value.doctor = ''
    },
  )

  const availableDoctors = computed<Doctor[]>(() => {
    const targetSpecialization = DEPARTMENT_TO_SPECIALIZATION[form.value.department]
    if (!targetSpecialization) return []
    return allDoctors.value.filter((d) => d.specialty === targetSpecialization)
  })

  return {
    departments: DEPARTMENTS,
    availableDoctors,
    loading,
    error,
    fetchAllDoctors,
  }
}