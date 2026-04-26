<script setup lang="ts">
const props = defineProps<{
  suggestions: string[]
  failed?: boolean
}>()
</script>

<template>
  <v-card rounded="lg" elevation="1" class="mb-4">
    <div class="card-header px-5 pt-4 pb-3 d-flex align-center justify-space-between">
      <div class="section-label">
        <v-icon size="14" color="warning" class="mr-1">mdi-alert-circle-outline</v-icon>
        SUGGESTIVE MODE
      </div>
    </div>

    <v-divider />

    <div class="pa-5">
      <v-alert
        v-if="props.suggestions.length"
        type="warning"
        variant="tonal"
        rounded="lg"
        density="compact"
      >
        <strong>Clinical Alerts:</strong>
        <div
          v-for="(suggestion, index) in props.suggestions"
          :key="`${index}-${suggestion}`"
          class="status-text mt-1"
        >
          {{ index + 1 }}. {{ suggestion }}
        </div>
      </v-alert>

      <v-alert
        v-else-if="props.failed"
        type="info"
        variant="tonal"
        rounded="lg"
        density="compact"
      >
        Suggestive mode is unavailable right now.
      </v-alert>

      <v-alert
        v-else
        type="success"
        variant="tonal"
        rounded="lg"
        density="compact"
      >
        No suggestions were generated for this consultation.
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
