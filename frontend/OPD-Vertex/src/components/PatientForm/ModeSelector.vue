<script setup lang="ts">
import type { Mode } from '@/composables/usePatientForm'

const props = defineProps<{
  modelValue: Mode
  accentColor: string
  tealColor: string
  actionCardBg: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Mode): void
}>()
</script>

<template>
  <v-row class="mb-8" no-gutters>
    <v-col cols="4" class="pr-2">
      <v-card
        class="action-card"
        :style="modelValue === 'book'
          ? { background: accentColor, border: 'none' }
          : { background: actionCardBg }"
        rounded="xl"
        elevation="0"
        @click="emit('update:modelValue', 'book')"
      >
        <v-card-text class="d-flex flex-column align-center pa-5">
          <v-icon size="32" class="mb-2" :color="modelValue === 'book' ? 'white' : accentColor">
            mdi-calendar-plus
          </v-icon>
          <span
            class="text-body-2 font-weight-bold text-center"
            :style="{ color: modelValue === 'book' ? 'white' : '' }"
          >
            Book Appointment
          </span>
        </v-card-text>
      </v-card>
    </v-col>

    <v-col cols="4" class="px-1">
      <v-card
        class="action-card"
        :style="modelValue === 'check'
          ? { background: tealColor, border: 'none' }
          : { background: actionCardBg }"
        rounded="xl"
        elevation="0"
        @click="emit('update:modelValue', 'check')"
      >
        <v-card-text class="d-flex flex-column align-center pa-5">
          <v-icon size="32" class="mb-2" :color="modelValue === 'check' ? 'white' : tealColor">
            mdi-magnify
          </v-icon>
          <span
            class="text-body-2 font-weight-bold text-center"
            :style="{ color: modelValue === 'check' ? 'white' : '' }"
          >
            Check Appointment
          </span>
        </v-card-text>
      </v-card>
    </v-col>

    <v-col cols="4" class="pl-2">
      <v-card
        class="action-card"
        :style="modelValue === 'cancel'
          ? { background: '#e57373', border: 'none' }
          : { background: actionCardBg }"
        rounded="xl"
        elevation="0"
        @click="emit('update:modelValue', 'cancel')"
      >
        <v-card-text class="d-flex flex-column align-center pa-5">
          <v-icon size="32" class="mb-2" :color="modelValue === 'cancel' ? 'white' : '#e57373'">
            mdi-calendar-remove
          </v-icon>
          <span
            class="text-body-2 font-weight-bold text-center"
            :style="{ color: modelValue === 'cancel' ? 'white' : '' }"
          >
            Cancel Appointment
          </span>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<style scoped>
.action-card {
  cursor: pointer;
  border: 2px solid transparent !important;
  transition: all 0.2s ease;
  height: 100%;
}
.action-card:hover {
  transform: translateY(-2px);
}
</style>