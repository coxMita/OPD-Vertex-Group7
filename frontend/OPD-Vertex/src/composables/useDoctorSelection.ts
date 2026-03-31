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

function getAvatarInitials(fullName: string): string {
  const parts = fullName.trim().split(' ').filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0]!.charAt(0)}${parts[parts.length - 1]!.charAt(0)}`.toUpperCase()
  }
  return (parts[0] ?? '?').charAt(0).toUpperCase()
}

export function useDoctorSelection(form: { value: PatientFormData }) {
  const availableDoctors = ref<Doctor[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchDoctorsByDepartment(department: string) {
    if (!department) {
      availableDoctors.value = []
      return
    }
    loading.value = true
    error.value = null
    try {
      const data = await userApi.getDoctorsByDepartment(department)
      availableDoctors.value = data.map((d) => ({
        id: d.doctor_id,
        name: `Dr. ${d.full_name}`,
        specialty: d.department_name,
        avatar: getAvatarInitials(d.full_name),
      }))
    } catch (err) {
      console.error('Failed to fetch doctors:', err)
      error.value = 'Could not load doctors.'
      availableDoctors.value = []
    } finally {
      loading.value = false
    }
  }

  // Re-fetch doctors when department changes, reset selected doctor
  watch(
    () => form.value.department,
    (newDepartment) => {
      form.value.doctor = ''
      fetchDoctorsByDepartment(newDepartment)
    },
  )

  return {
    departments: DEPARTMENTS,
    availableDoctors,
    loading,
    error,
    fetchDoctorsByDepartment,
  }
}