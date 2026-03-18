<script setup lang="ts">
import FormField from '@/components/PatientForm/FormField.vue'
import type { Mode } from '@/composables/usePatientForm'

const props = defineProps<{
  mode: Extract<Mode, 'check' | 'cancel'>
  contact: string
  cardColor: string
  tealColor: string
}>()

const emit = defineEmits<{
  (e: 'update:contact', value: string): void
  (e: 'submit'): void
}>()

const config = {
  check: {
    icon: 'mdi-magnify',
    color: props.tealColor,
    title: 'Check Appointment',
    subtitle: 'Enter your contact info to find your bookings',
    buttonLabel: 'Find My Appointments',
  },
  cancel: {
    icon: 'mdi-calendar-remove',
    color: '#e57373',
    title: 'Cancel Appointment',
    subtitle: "We'll find your appointments so you can cancel",
    buttonLabel: 'Find My Appointments',
  },
}
</script>

<template>
  <v-card rounded="xl" elevation="2" :color="cardColor" class="pa-8">
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar :color="config[mode].color" size="40">
        <v-icon color="white" size="20">{{ config[mode].icon }}</v-icon>
      </v-avatar>
      <div>
        <h2 class="text-h6 font-weight-bold">{{ config[mode].title }}</h2>
        <p class="text-medium-emphasis text-caption">{{ config[mode].subtitle }}</p>
      </div>
    </div>

    <FormField
      label="Phone Number or Email"
      placeholder="Enter your phone or email..."
      :model-value="contact"
      @update:model-value="emit('update:contact', $event)"
    />

    <v-btn
      :color="config[mode].color"
      size="x-large"
      rounded="lg"
      block
      elevation="0"
      class="mt-6"
      @click="emit('submit')"
    >
      <span class="font-weight-bold" style="color: white">
        {{ config[mode].buttonLabel }}
      </span>
      <v-icon end color="white">mdi-arrow-right</v-icon>
    </v-btn>
  </v-card>
</template>