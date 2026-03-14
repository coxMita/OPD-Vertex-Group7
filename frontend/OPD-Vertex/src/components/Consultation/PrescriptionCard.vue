<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  initialText: string
  patientName: string
  patientEmail: string
}>()

const emit = defineEmits<{
  (e: 'approved', text: string): void
}>()

const rxText = ref(props.initialText)
const approved = ref(false)

// Allow parent to push transcript-based updates
watch(
  () => props.initialText,
  (val) => {
    rxText.value = val
    approved.value = false
  }
)

function regenerate() {
  const spinner = '✦ Regenerating with AI...'
  rxText.value = spinner
  setTimeout(() => {
    rxText.value = props.initialText
  }, 1100)
}

function approve() {
  approved.value = true
  emit('approved', rxText.value)
}

function clearText() {
  rxText.value = ''
  approved.value = false
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

      <v-textarea
        v-model="rxText"
        variant="outlined"
        rounded="lg"
        rows="10"
        auto-grow
        hide-details
        class="rx-textarea mb-4"
        :readonly="approved"
        placeholder="Prescription will be generated automatically once the consultation recording is processed by the AI Service (Llama 3)."
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
          :disabled="approved"
          @click="clearText"
        >
          Clear
        </v-btn>
        <v-btn
          variant="tonal"
          color="deep-purple"
          size="small"
          :disabled="approved"
          @click="regenerate"
        >
          <v-icon start size="14">mdi-creation</v-icon>
          Regenerate with AI
        </v-btn>
        <v-btn
          color="teal"
          size="small"
          :disabled="!rxText || approved"
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

.rx-textarea :deep(textarea) {
  font-family: 'DM Mono', 'Fira Code', monospace !important;
  font-size: 0.82rem !important;
  line-height: 1.7 !important;
}
</style>