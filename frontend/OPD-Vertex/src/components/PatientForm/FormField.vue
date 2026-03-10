<script setup lang="ts">
defineProps<{
  label: string
  modelValue: string
  placeholder?: string
  type?: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
</script>

<template>
  <div>
    <label class="field-label">{{ label }}</label>
    <v-text-field
      :model-value="modelValue"
      :placeholder="placeholder"
      :type="type ?? 'text'"
      variant="outlined"
      rounded="lg"
      density="comfortable"
      hide-details
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </div>
</template>

<style scoped>
.field-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 6px;
  color: #6b7280;
}
</style>