<script setup lang="ts">
import type { Mode, PatientFormData } from '@/composables/usePatientForm'
import type { PatientResponse } from '@/services/userApi'
import type { Appointment } from '@/models/appointment/appointment.interface'
import { STATUS_CONFIG } from '@/composables/useCalendarAppointments'

const props = defineProps<{
  mode: Mode
  form: PatientFormData
  accentColor: string
  tealColor: string
  patient?: PatientResponse | null
  appointments?: Appointment[]
}>()

const emit = defineEmits<{ (e: 'back'): void }>()

const avatarColor = { book: props.accentColor, check: props.tealColor, cancel: '#e57373' }
const title = {
  book: 'Booking Confirmed!',
  check: 'Your Appointments',
  cancel: 'Your Appointments',
}
</script>

<template>
  <!-- BOOK mode — existent -->
  <div v-if="mode === 'book'" class="text-center py-16">
    <v-avatar :color="avatarColor.book" size="80" class="mb-6">
      <v-icon size="44" color="white">mdi-check</v-icon>
    </v-avatar>
    <h2 class="text-h4 font-weight-bold mb-3">Booking Confirmed!</h2>
    <p class="text-medium-emphasis text-h6 mb-8">
      We'll see you on {{ form.date }} at {{ form.time }} with {{ form.doctor || 'your doctor' }}.
    </p>
    <v-btn color="primary" rounded size="large" @click="emit('back')">Back to Home</v-btn>
  </div>

  <!-- CHECK / CANCEL mode — lista programări -->
  <div v-else class="py-6">
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar :color="avatarColor[mode]" size="48">
        <v-icon color="white">mdi-calendar-check</v-icon>
      </v-avatar>
      <div>
        <h2 class="text-h6 font-weight-bold">{{ title[mode] }}</h2>
        <p class="text-medium-emphasis text-caption" v-if="patient">
          {{ patient.first_name }} {{ patient.last_name }} · {{ patient.email }}
        </p>
      </div>
    </div>

    <!-- Empty state -->
    <v-card v-if="!appointments || appointments.length === 0" rounded="xl" elevation="1" class="pa-8 text-center">
      <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-calendar-blank-outline</v-icon>
      <p class="text-medium-emphasis">No appointments found.</p>
    </v-card>

    <!-- Lista -->
    <v-card
      v-for="appt in appointments"
      :key="appt.id"
      rounded="xl"
      elevation="1"
      class="mb-3 pa-5"
      :style="{
        borderLeft: `4px solid ${STATUS_CONFIG[appt.status]?.border ?? '#ccc'}`
      }"
    >
      <div class="d-flex justify-space-between align-center">
        <div>
          <p class="font-weight-bold text-body-1">{{ appt.appointment_date }}</p>
          <p class="text-medium-emphasis text-caption">
            {{ appt.time_preference }} · {{ appt.assigned_time ?? 'Time TBD' }}
          </p>
          <p v-if="appt.notes" class="text-caption mt-1">{{ appt.notes }}</p>
        </div>
        <v-chip
          :color="STATUS_CONFIG[appt.status]?.border ?? 'grey'"
          variant="tonal"
          size="small"
        >
          <v-icon start size="14">{{ STATUS_CONFIG[appt.status]?.icon }}</v-icon>
          {{ STATUS_CONFIG[appt.status]?.label ?? appt.status }}
        </v-chip>
      </div>
    </v-card>

    <v-btn color="primary" rounded size="large" block class="mt-4" @click="emit('back')">
      Back to Home
    </v-btn>
  </div>
</template>