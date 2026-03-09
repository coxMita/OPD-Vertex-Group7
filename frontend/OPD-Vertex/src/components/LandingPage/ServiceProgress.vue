<script setup lang="ts">
defineProps<{ name: string; value: number; status: string }>()
</script>

<template>
  <div class="mb-3">
    <div class="d-flex justify-space-between mb-1">
      <span class="text-body-2 font-weight-medium">{{ name }}</span>
      <span class="text-body-2 text-success">{{ status }}</span>
    </div>
    <v-progress-linear :model-value="value" color="primary" height="6" rounded />
  </div>
</template>