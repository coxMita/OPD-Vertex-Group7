import { onUnmounted, ref, type Ref, watch } from 'vue'
import { pollPrescription, type PrescriptionData } from '@/services/prescriptionApi'

type UseSuggestiveModeOptions = {
  delayMs?: number
  intervalMs?: number
  maxAttempts?: number
}

function extractClinicalAlert(data: PrescriptionData): string | null {
  const topLevelSingle = typeof data.clinical_alert === 'string' ? data.clinical_alert : ''
  if (topLevelSingle.trim()) return topLevelSingle.trim()

  const topLevelList = Array.isArray(data.clinical_alerts)
    ? data.clinical_alerts.find((item) => typeof item === 'string' && item.trim())
    : null
  if (topLevelList) return topLevelList.trim()

  const rx = data.prescription_json as Record<string, unknown>

  const nestedSingle = typeof rx.clinical_alert === 'string' ? rx.clinical_alert : ''
  if (nestedSingle.trim()) return nestedSingle.trim()

  if (Array.isArray(rx.clinical_alerts)) {
    const nestedListItem = rx.clinical_alerts.find(
      (item) => typeof item === 'string' && item.trim(),
    ) as string | undefined
    if (nestedListItem) return nestedListItem.trim()
  }

  return null
}

export function useSuggestiveMode(
  consultationId: Ref<string | null>,
  options: UseSuggestiveModeOptions = {},
) {
  const delayMs = options.delayMs ?? 4000
  const intervalMs = options.intervalMs ?? 5000
  const maxAttempts = options.maxAttempts ?? 120

  const suggestionLoading = ref(false)
  const suggestionFailed = ref(false)
  const suggestionText = ref<string | null>(null)
  const showPrescription = ref(false)

  let runToken = 0
  let revealTimer: ReturnType<typeof setTimeout> | null = null

  function clearRevealTimer() {
    if (revealTimer) {
      clearTimeout(revealTimer)
      revealTimer = null
    }
  }

  watch(
    consultationId,
    async (newId) => {
      runToken += 1
      const localToken = runToken

      clearRevealTimer()
      suggestionLoading.value = false
      suggestionFailed.value = false
      suggestionText.value = null
      showPrescription.value = false

      if (!newId) return

      suggestionLoading.value = true

      try {
        const data = await pollPrescription(newId, {
          intervalMs,
          maxAttempts,
        })

        if (localToken !== runToken) return

        if (!data) {
          suggestionFailed.value = true
          showPrescription.value = true
          return
        }

        suggestionText.value = extractClinicalAlert(data)

        revealTimer = setTimeout(() => {
          if (localToken !== runToken) return
          showPrescription.value = true
        }, delayMs)
      } catch {
        if (localToken !== runToken) return
        suggestionFailed.value = true
        showPrescription.value = true
      } finally {
        if (localToken === runToken) {
          suggestionLoading.value = false
        }
      }
    },
    { immediate: true },
  )

  onUnmounted(() => {
    runToken += 1
    clearRevealTimer()
  })

  return {
    suggestionLoading,
    suggestionFailed,
    suggestionText,
    showPrescription,
  }
}
