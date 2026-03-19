import { ref, computed } from 'vue'
import type { PatientFormData } from './usePatientForm'

export interface Doctor {
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

const DOCTORS_BY_DEPARTMENT: Record<string, Doctor[]> = {
  'General Practice': [
    { name: 'Dr. Ana Popescu', specialty: 'General Practitioner', avatar: 'AP' },
    { name: 'Dr. Ion Marinescu', specialty: 'General Practitioner', avatar: 'IM' },
  ],
  'Cardiology': [
    { name: 'Dr. Elena Dumitrescu', specialty: 'Cardiologist', avatar: 'ED' },
    { name: 'Dr. Mihai Ionescu', specialty: 'Interventional Cardiologist', avatar: 'MI' },
  ],
  'Dermatology': [
    { name: 'Dr. Raluca Stan', specialty: 'Dermatologist', avatar: 'RS' },
    { name: 'Dr. Andrei Popa', specialty: 'Cosmetic Dermatologist', avatar: 'AP' },
  ],
  'Neurology': [
    { name: 'Dr. Cristina Vlad', specialty: 'Neurologist', avatar: 'CV' },
    { name: 'Dr. Bogdan Radu', specialty: 'Pediatric Neurologist', avatar: 'BR' },
  ],
  'Orthopedics': [
    { name: 'Dr. Alexandru Marin', specialty: 'Orthopedic Surgeon', avatar: 'AM' },
    { name: 'Dr. Ioana Constantin', specialty: 'Sports Medicine', avatar: 'IC' },
  ],
  'Pediatrics': [
    { name: 'Dr. Maria Georgescu', specialty: 'Pediatrician', avatar: 'MG' },
    { name: 'Dr. Vlad Nistor', specialty: 'Neonatologist', avatar: 'VN' },
  ],
  'Psychiatry': [
    { name: 'Dr. Andreea Matei', specialty: 'Psychiatrist', avatar: 'AM' },
    { name: 'Dr. Radu Florescu', specialty: 'Child Psychiatrist', avatar: 'RF' },
  ],
}

export function useDoctorSelection(form: { value: PatientFormData }) {
  // Resets selected doctor whenever department changes
  const availableDoctors = computed<Doctor[]>(() => {
    form.value.doctor = ''
    return DOCTORS_BY_DEPARTMENT[form.value.department] ?? []
  })

  return {
    departments: DEPARTMENTS,
    availableDoctors,
  }
}