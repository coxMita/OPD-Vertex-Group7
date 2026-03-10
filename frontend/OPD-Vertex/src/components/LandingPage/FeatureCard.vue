<script setup lang="ts">
defineProps<{ icon: string; color: string; title: string; description: string }>()
</script>

<template>
  <v-card class="pa-6 h-100" elevation="2" rounded="lg">
    <v-avatar :color="color" size="56" class="mb-4">
      <v-icon size="28" color="white">{{ icon }}</v-icon>
    </v-avatar>
    <h3 class="text-h6 font-weight-bold mb-3">{{ title }}</h3>
    <p class="text-medium-emphasis">{{ description }}</p>
  </v-card>
</template>