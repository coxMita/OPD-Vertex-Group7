import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'

export type Mode = 'book' | 'check' | 'cancel'

export interface PatientFormData {
  firstName: string
  lastName: string
  phone: string
  email: string
  date: string
  time: string
  reason: string
  department: string
  doctor: string
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

  const form = ref<PatientFormData>({
    firstName: '',
    lastName: '',
    phone: '',
    email: '',
    date: '',
    time: 'AM',
    reason: '',
    department: 'General Practice',
    doctor: '',
  })

  const lookup = ref<LookupData>({ contact: '' })

  function handleSubmit() {
    submitted.value = true
  }

  function handleLookup() {
    submitted.value = true
  }

  function switchMode(m: Mode) {
    mode.value = m
    submitted.value = false
  }

  return {
    isDark,
    accentColor,
    tealColor,
    cardColor,
    actionCardBg,
    mode,
    submitted,
    form,
    lookup,
    handleSubmit,
    handleLookup,
    switchMode,
  }
}