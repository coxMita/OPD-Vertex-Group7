<script setup lang="ts">
const props = defineProps<{
  loading: boolean
  suggestion: string | null
  failed?: boolean
  delaySeconds: number
}>()
</script>

<template>
  <v-card rounded="lg" elevation="1" class="mb-4">
    <div class="card-header px-5 pt-4 pb-3 d-flex align-center justify-space-between">
      <div class="section-label">
        <v-icon size="14" color="warning" class="mr-1">mdi-alert-circle-outline</v-icon>
        SUGGESTIVE MODE
      </div>
      <v-chip color="warning" size="x-small" variant="tonal" class="font-weight-bold">
        Symptom Guard
      </v-chip>
    </div>

    <v-divider />

    <div class="pa-5">
      <div v-if="props.loading" class="d-flex align-center ga-3">
        <v-progress-circular indeterminate color="warning" size="18" width="2" />
        <span class="status-text">Checking if patient symptoms were left unaddressed…</span>
      </div>

      <v-alert
        v-else-if="props.suggestion"
        type="warning"
        variant="tonal"
        rounded="lg"
        density="compact"
      >
        <strong>Clinical Alert:</strong> {{ props.suggestion }}
        <div class="status-text mt-1">
          Prescription box will appear in about {{ props.delaySeconds }}s.
        </div>
      </v-alert>

      <v-alert
        v-else-if="props.failed"
        type="info"
        variant="tonal"
        rounded="lg"
        density="compact"
      >
        Suggestive mode is unavailable right now. Loading prescription directly.
      </v-alert>

      <v-alert
        v-else
        type="success"
        variant="tonal"
        rounded="lg"
        density="compact"
      >
        No clinical alerts detected. Loading prescription box…
      </v-alert>
    </div>
  </v-card>
</template>

<style scoped>
.section-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  opacity: 0.6;
  display: flex;
  align-items: center;
}
.status-text {
  font-size: 0.78rem;
  opacity: 0.75;
}
</style>
