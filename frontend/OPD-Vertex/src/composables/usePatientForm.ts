import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'
import { usePatientLookup } from '@/composables/usePatientLookup'
import { userApi } from '@/services/userApi'
import { emailApi } from '@/services/emailApi'

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

  // OTP state
  const otpStep = ref(false)
  const otpSending = ref(false)
  const otpSendError = ref<string | null>(null)
  const otpVerifying = ref(false)
  const otpVerifyError = ref<string | null>(null)

  async function handleSendOtp() {
    if (!lookup.value.contact) return
    otpSending.value = true
    otpSendError.value = null
    try {
      await userApi.lookupPatientByEmail(lookup.value.contact)
      await emailApi.sendOtp(lookup.value.contact)
      otpStep.value = true
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } }
      if (axiosErr.response?.status === 404) {
        otpSendError.value = 'No account found with this email address.'
      } else {
        otpSendError.value = 'Could not send verification code. Please try again.'
      }
    } finally {
      otpSending.value = false
    }
  }

  async function handleResendOtp() {
    otpSending.value = true
    otpVerifyError.value = null
    try {
      await emailApi.sendOtp(lookup.value.contact)
    } catch {
      otpVerifyError.value = 'Could not resend code. Please try again.'
    } finally {
      otpSending.value = false
    }
  }

  async function handleVerifyOtp(code: string) {
    otpVerifying.value = true
    otpVerifyError.value = null
    try {
      const valid = await emailApi.verifyOtp(lookup.value.contact, code)
      if (!valid) {
        otpVerifyError.value = 'Invalid or expired code. Please try again.'
        return
      }
      await lookupByEmail(lookup.value.contact)
      if (lookedUpPatient.value) {
        otpStep.value = false
        submitted.value = true
      }
    } catch {
      otpVerifyError.value = 'Verification failed. Please try again.'
    } finally {
      otpVerifying.value = false
    }
  }

  function switchMode(m: Mode) {
    mode.value = m
    submitted.value = false
    submitError.value = null
    otpStep.value = false
    otpSendError.value = null
    otpVerifyError.value = null
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
    otpStep,
    otpSending,
    otpSendError,
    otpVerifying,
    otpVerifyError,
    handleSendOtp,
    handleResendOtp,
    handleVerifyOtp,
    switchMode,
  }
}