<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  text: string
  loading: boolean
  failed?: boolean
  patientName: string
  patientEmail: string
}>()

const emit = defineEmits<{
  (e: 'approved', text: string): void
}>()

const rxText = ref('')
const approved = ref(false)
watch(
  () => props.text,
  (newText) => {
    if (!approved.value) {
      rxText.value = newText
    }
  },
  { immediate: true },
)

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

      <v-alert
        v-if="props.failed"
        type="warning"
        variant="tonal"
        density="compact"
        rounded="lg"
        class="mb-3"
      >
        AI prescription not received yet. You can edit the field manually.
      </v-alert>

      <v-textarea
        v-model="rxText"
        variant="outlined"
        rounded="lg"
        rows="10"
        auto-grow
        hide-details
        class="rx-textarea mb-4"
        :readonly="approved || props.loading"
        :placeholder="
          props.loading
            ? 'Waiting for AI service answer...'
            : 'Prescription will be generated automatically once the consultation recording is processed by the AI service.'
        "
      />

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

      <div class="d-flex justify-end ga-2">
        <v-btn
          variant="tonal"
          color="default"
          size="small"
          :disabled="approved || props.loading"
          @click="clearText"
        >
          Clear
        </v-btn>
        <v-btn
          color="teal"
          size="small"
          :disabled="!rxText || approved || props.loading"
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
