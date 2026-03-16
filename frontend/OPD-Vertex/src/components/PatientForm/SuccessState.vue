<script setup lang="ts">
import type { Mode, PatientFormData } from '@/composables/usePatientForm'

const props = defineProps<{
  mode: Mode
  form: PatientFormData
  accentColor: string
  tealColor: string
}>()

const emit = defineEmits<{
  (e: 'back'): void
}>()

const avatarColor = {
  book: props.accentColor,
  check: props.tealColor,
  cancel: '#e57373',
}

const title = {
  book: 'Booking Confirmed!',
  check: 'Appointments Found!',
  cancel: 'Appointments Found!',
}

const subtitle = {
  book: `We'll see you on ${props.form.date} at ${props.form.time} with ${props.form.doctor || 'your doctor'}.`,
  check: 'Check your email or phone for details.',
  cancel: 'Check your email or phone for details.',
}
</script>

<template>
  <div class="text-center py-16">
    <v-avatar :color="avatarColor[mode]" size="80" class="mb-6">
      <v-icon size="44" color="white">mdi-check</v-icon>
    </v-avatar>
    <h2 class="text-h4 font-weight-bold mb-3">{{ title[mode] }}</h2>
    <p class="text-medium-emphasis text-h6 mb-8">{{ subtitle[mode] }}</p>
    <v-btn color="primary" rounded size="large" @click="emit('back')">
      Back to Home
    </v-btn>
  </div>
</template>