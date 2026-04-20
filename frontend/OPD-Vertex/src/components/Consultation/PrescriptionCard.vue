<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { pollPrescription, type PrescriptionData } from '@/services/prescriptionApi'

const props = defineProps<{
  initialText: string
  patientName: string
  patientEmail: string
  consultationId?: string | null
}>()

const emit = defineEmits<{
  (e: 'approved', text: string): void
}>()

// ── State ──────────────────────────────────────────────────────────────────
const rxText = ref('')
const approved = ref(false)
const polling = ref(false)
const pollingFailed = ref(false)
const prescriptionData = ref<PrescriptionData | null>(null)

let stopPolling = false

// ── Helpers ────────────────────────────────────────────────────────────────
function buildRxText(data: PrescriptionData): string {
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

// ── Polling trigger ────────────────────────────────────────────────────────
async function startPolling(consultationId: string) {
  polling.value = true
  pollingFailed.value = false
  stopPolling = false

  try {
    // Small initial delay — give RabbitMQ + AI pipeline time to save
    await new Promise((r) => setTimeout(r, 3000))

    if (stopPolling) return

    const data = await pollPrescription(consultationId, {
      intervalMs: 5000,
      maxAttempts: 120,
    })

    if (stopPolling) return

    if (data) {
      prescriptionData.value = data
      rxText.value = buildRxText(data)
      approved.value = false
    } else {
      pollingFailed.value = true
    }
  } catch {
    if (!stopPolling) pollingFailed.value = true
  } finally {
    if (!stopPolling) polling.value = false
  }
}

// Watch consultationId — start polling whenever a new consultation is selected
watch(
  () => props.consultationId,
  (newId) => {
    stopPolling = true // cancel any in-flight poll
    prescriptionData.value = null
    approved.value = false
    pollingFailed.value = false

    if (newId) {
      startPolling(newId)
    } else {
      polling.value = false
    }
  },
  { immediate: true },
)

// initialText is intentionally ignored — prescription content comes only from DB polling

onUnmounted(() => {
  stopPolling = true
})

// ── Actions ────────────────────────────────────────────────────────────────
function regenerate() {
  if (prescriptionData.value) {
    rxText.value = buildRxText(prescriptionData.value)
    approved.value = false
  }
}

function approve() {
  approved.value = true
  emit('approved', rxText.value)
}

function clearText() {
  rxText.value = ''
  approved.value = false
}

function onManualInput() {
  if (polling.value) {
    stopPolling = true
    polling.value = false
    pollingFailed.value = true
  }
}
</script>

<template>
  <v-card rounded="lg" elevation="1">
    <div class="card-header px-5 pt-4 pb-3 d-flex align-center justify-space-between">
      <div class="section-label">
        <v-icon size="14" color="primary" class="mr-1">mdi-circle</v-icon>
        PRESCRIPTION
      </div>
      <v-chip color="deep-purple" size="x-small" variant="tonal" class="font-weight-bold">
        <v-icon start size="12">mdi-creation</v-icon>
        AI Generated
      </v-chip>
    </div>

    <v-divider />

    <div class="pa-5">
      <p class="helper-text mb-3">Review and edit the AI-generated prescription before approving.</p>

      <!-- Polling indicator -->
      <v-expand-transition>
        <div v-if="polling" class="mb-4">
          <div class="d-flex align-center ga-3 mb-2">
            <v-progress-circular indeterminate color="deep-purple" size="18" width="2" />
            <span class="polling-text">Waiting for AI to process consultation recording… You can start typing below to override.</span>
          </div>
          <v-progress-linear indeterminate color="deep-purple" rounded height="3" />
        </div>
      </v-expand-transition>

      <!-- Polling failed -->
      <v-expand-transition>
        <v-alert
          v-if="pollingFailed"
          type="warning"
          variant="tonal"
          density="compact"
          rounded="lg"
          class="mb-3"
        >
          AI prescription not received yet. You can edit the field manually.
        </v-alert>
      </v-expand-transition>

      <v-textarea
        v-model="rxText"
        variant="outlined"
        rounded="lg"
        rows="10"
        auto-grow
        hide-details
        class="rx-textarea mb-4"
        :readonly="approved"
        @input="onManualInput"
        :placeholder="
          polling
            ? 'Waiting for AI Service... Start typing here to write manually.'
            : 'Prescription will be generated automatically once the consultation recording is processed by the AI Service (Llama 3).'
        "
      />

      <v-expand-transition>
        <v-alert
          v-if="approved"
          type="success"
          variant="tonal"
          rounded="lg"
          density="compact"
          class="mb-4"
        >
          Prescription approved and dispatched to <strong>{{ patientEmail }}</strong>.
        </v-alert>
      </v-expand-transition>

      <div class="d-flex justify-end ga-2">
        <v-btn
          variant="tonal"
          color="default"
          size="small"
          :disabled="approved || polling"
          @click="clearText"
        >
          Clear
        </v-btn>
        <v-btn
          variant="tonal"
          color="deep-purple"
          size="small"
          :disabled="approved || polling"
          @click="regenerate"
        >
          <v-icon start size="14">mdi-creation</v-icon>
          Regenerate with AI
        </v-btn>
        <v-btn
          color="teal"
          size="small"
          :disabled="!rxText || approved || polling"
          @click="approve"
        >
          <v-icon start size="14">mdi-check</v-icon>
          Approve &amp; Send
        </v-btn>
      </div>
    </div>
  </v-card>
</template>

<style scoped>
.section-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  opacity: 0.5;
  display: flex;
  align-items: center;
}
.helper-text {
  font-size: 0.78rem;
  opacity: 0.55;
}
.polling-text {
  font-size: 0.78rem;
  opacity: 0.65;
}
.rx-textarea :deep(textarea) {
  font-family: 'DM Mono', 'Fira Code', monospace !important;
  font-size: 0.82rem !important;
  line-height: 1.7 !important;
}
</style>