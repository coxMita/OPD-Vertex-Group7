import { onUnmounted, ref, type Ref, watch } from 'vue'
import { pollPrescription, type PrescriptionData } from '@/services/prescriptionApi'

type UseSuggestiveModeOptions = {
  intervalMs?: number
  maxAttempts?: number
}

function extractClinicalAlerts(data: PrescriptionData): string[] {
  const alerts: string[] = []

  const topLevelSingle = typeof data.clinical_alert === 'string' ? data.clinical_alert : ''
  if (topLevelSingle.trim()) alerts.push(topLevelSingle.trim())

  if (Array.isArray(data.clinical_alerts)) {
    data.clinical_alerts.forEach((item) => {
      if (typeof item === 'string' && item.trim()) alerts.push(item.trim())
    })
  }

  const rx = data.prescription_json as Record<string, unknown>

  const nestedSingle = typeof rx.clinical_alert === 'string' ? rx.clinical_alert : ''
  if (nestedSingle.trim()) alerts.push(nestedSingle.trim())

  if (Array.isArray(rx.clinical_alerts)) {
    rx.clinical_alerts.forEach((item) => {
      if (typeof item === 'string' && item.trim()) alerts.push(item.trim())
    })
  }

  return [...new Set(alerts)]
}

function buildPrescriptionText(data: PrescriptionData): string {
  const rx = data.prescription_json as Record<string, string | null>
  const summary = data.summary_json?.summary ?? ''

  const lines: string[] = []

  if (summary) {
    lines.push('CLINICAL SUMMARY:')
    lines.push(summary)
    lines.push('')
  }

  lines.push('PRESCRIPTION:')

  if (rx.medication_name) {
    lines.push(`Medication : ${rx.medication_name}`)
  }
  if (rx.dosage) {
    lines.push(`Dosage     : ${rx.dosage}`)
  }
  if (rx.frequency) {
    lines.push(`Frequency  : ${rx.frequency}`)
  }
  if (rx.duration) {
    lines.push(`Duration   : ${rx.duration}`)
  }
  if (rx.notes) {
    lines.push('')
    lines.push(`Notes      : ${rx.notes}`)
  }

  return lines.join('\n')
}

export function useSuggestiveMode(
  consultationId: Ref<string | null>,
  options: UseSuggestiveModeOptions = {},
) {
  const intervalMs = options.intervalMs ?? 5000
  const maxAttempts = options.maxAttempts ?? 120

  const prescriptionLoading = ref(false)
  const prescriptionFailed = ref(false)
  const prescriptionText = ref('')
  const prescriptionReady = ref(false)
  const suggestionTexts = ref<string[]>([])

  let runToken = 0

  watch(
    consultationId,
    async (newId) => {
      runToken += 1
      const localToken = runToken

      prescriptionLoading.value = false
      prescriptionFailed.value = false
      prescriptionText.value = ''
      prescriptionReady.value = false
      suggestionTexts.value = []

      if (!newId) return

      prescriptionLoading.value = true

      try {
        const data = await pollPrescription(newId, {
          intervalMs,
          maxAttempts,
        })

        if (localToken !== runToken) return

        if (!data) {
          prescriptionFailed.value = true
          prescriptionReady.value = true
          return
        }

        prescriptionText.value = buildPrescriptionText(data)
        suggestionTexts.value = extractClinicalAlerts(data)
        prescriptionReady.value = true
      } catch {
        if (localToken !== runToken) return
        prescriptionFailed.value = true
        prescriptionReady.value = true
      } finally {
        if (localToken === runToken) {
          prescriptionLoading.value = false
        }
      }
    },
    { immediate: true },
  )

  onUnmounted(() => {
    runToken += 1
  })

  return {
    prescriptionLoading,
    prescriptionFailed,
    prescriptionText,
    prescriptionReady,
    suggestionTexts,
  }
}
