import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'
import { usePatientLookup } from '@/composables/usePatientLookup'

export type Mode = 'book' | 'check' | 'cancel'

export interface PatientFormData {
  firstName: string
  lastName: string
  phone_number: string      // kept as string in form, converted to number on submit
  email: string
  dateOfBirth: string       // "YYYY-MM-DD"
  gender: string            // "male" | "female" | "other"
  date: string
  time: string
  reason: string
  department: string
  doctor: string
  doctorId: string
}

export interface LookupData {
  contact: string
}

export function usePatientForm() {
  const vuetifyTheme = useTheme()
  const isDark = computed(() => vuetifyTheme.current.value.dark)

  const accentColor = computed(() => isDark.value ? '#29b6f6' : '#c0687a')
  const tealColor = computed(() => isDark.value ? '#4dd0e1' : '#2a9d8f')
  const cardColor = computed(() => isDark.value ? '#1e1e1e' : '#fefdf5')
  const actionCardBg = computed(() => isDark.value ? '#2a2a2a' : '#fefdf5')

  const mode = ref<Mode>('book')
  const submitted = ref(false)
  const submitting = ref(false)
  const submitError = ref<string | null>(null)

  const form = ref<PatientFormData>({
    firstName: '',
    lastName: '',
    phone_number: '',
    email: '',
    dateOfBirth: '',
    gender: '',
    date: '',
    time: 'AM',
    reason: '',
    department: 'General Practice',
    doctor: '',
    doctorId: '',
  })

  const lookup = ref<LookupData>({ contact: '' })

  const {
    loading: lookupLoading,
    error: lookupError,
    patient: lookedUpPatient,
    appointments: lookedUpAppointments,
    lookupByEmail,
  } = usePatientLookup()

  async function handleLookup() {
    if (!lookup.value.contact) return
    await lookupByEmail(lookup.value.contact)
    if (lookedUpPatient.value) {
      submitted.value = true
    }
  }

  function switchMode(m: Mode) {
    mode.value = m
    submitted.value = false
    submitError.value = null
  }

  return {
    isDark,
    accentColor,
    tealColor,
    cardColor,
    actionCardBg,
    lookupLoading,
    lookupError,
    lookedUpPatient,
    lookedUpAppointments,
    mode,
    submitted,
    submitting,
    submitError,
    form,
    lookup,
    handleLookup,
    switchMode,
  }
}