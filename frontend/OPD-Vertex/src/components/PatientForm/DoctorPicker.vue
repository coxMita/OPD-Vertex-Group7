<script setup lang="ts">
import type { Doctor } from '@/composables/useDoctorSelection'

const props = defineProps<{
  doctors: Doctor[]
  modelValue: string       // selected doctor display name (for UI highlight)
  modelDoctorId: string    // selected doctor id (for API)
  accentColor: string
  actionCardBg: string
  isDark: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'update:modelDoctorId', value: string): void
}>()

function selectDoctor(doctor: Doctor) {
  emit('update:modelValue', doctor.name)
  emit('update:modelDoctorId', doctor.id)
}
</script>

<template>
  <v-expand-transition>
    <div v-if="doctors.length">
      <label class="field-label mt-1">Select Doctor</label>
      <div class="mt-2">
        <v-card
          v-for="doctor in doctors"
          :key="doctor.id"
          :style="modelValue === doctor.name
            ? { border: `2px solid ${accentColor}`, background: isDark ? '#2a2a2a' : '#fff5f5' }
            : { border: '2px solid transparent', background: actionCardBg }"
          rounded="lg"
          elevation="0"
          class="doctor-card mb-2"
          @click="selectDoctor(doctor)"
        >
          <v-card-text class="d-flex align-center ga-3 pa-4">
            <v-avatar
              :color="modelValue === doctor.name ? accentColor : (isDark ? '#444' : '#e0e0e0')"
              size="42"
            >
              <span
                class="text-caption font-weight-bold"
                :style="{ color: modelValue === doctor.name ? 'white' : (isDark ? '#ccc' : '#555') }"
              >
                {{ doctor.avatar }}
              </span>
            </v-avatar>
            <div class="flex-grow-1">
              <div class="text-body-2 font-weight-bold">{{ doctor.name }}</div>
              <div class="text-caption text-medium-emphasis">{{ doctor.specialty }}</div>
            </div>
            <v-icon v-if="modelValue === doctor.name" :color="accentColor" size="20">
              mdi-check-circle
            </v-icon>
          </v-card-text>
        </v-card>
      </div>
    </div>
  </v-expand-transition>
</template>

<style scoped>
.field-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 6px;
  color: #6b7280;
}
.doctor-card {
  cursor: pointer;
  transition: all 0.2s ease;
}
.doctor-card:hover {
  transform: translateX(3px);
}
</style>