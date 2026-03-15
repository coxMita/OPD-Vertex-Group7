<script setup lang="ts">
defineProps<{
  title: string
  icon: string
}>()
</script>

<template>
  <div class="form-section mb-6">
    <div class="d-flex align-center ga-2 mb-4">
      <v-icon :icon="icon" color="primary" size="20" />
      <h3 class="text-subtitle-1 font-weight-bold">{{ title }}</h3>
    </div>
    <slot />
  </div>
</template>

<style scoped>
.form-section {
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 24px;
}
.form-section:last-of-type {
  border-bottom: none;
}
</style>