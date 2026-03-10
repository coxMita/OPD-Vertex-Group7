<script setup lang="ts">
defineProps<{ index: number; title: string; description: string }>()
</script>

<template>
  <div class="text-center">
    <v-avatar color="primary" size="72" class="mb-4">
      <span class="text-h4 font-weight-bold text-white">{{ index }}</span>
    </v-avatar>
    <h3 class="text-h6 font-weight-bold mb-3">{{ title }}</h3>
    <p class="text-medium-emphasis">{{ description }}</p>
  </div>
</template>