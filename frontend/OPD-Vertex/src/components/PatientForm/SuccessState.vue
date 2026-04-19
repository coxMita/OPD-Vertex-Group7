<script setup lang="ts">
import { ref } from 'vue'
import type { Mode, PatientFormData } from '@/composables/usePatientForm'
import type { PatientResponse } from '@/services/userApi'
import type { Appointment } from '@/models/appointment/appointment.interface'
import { STATUS_CONFIG } from '@/composables/useCalendarAppointments'
import { appointmentApi } from '@/services/appointmentApi'

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

// ── Cancel logic ───────────────────────────────────────────────
const cancellingId = ref<string | null>(null)
const cancelError = ref<string | null>(null)
const localAppointments = ref<Appointment[]>(props.appointments ? [...props.appointments] : [])

async function cancelAppointment(appointmentId: string) {
  if (!props.patient) return
  cancellingId.value = appointmentId
  cancelError.value = null

  try {
    const updated = await appointmentApi.cancelAppointment(appointmentId, props.patient.patient_id)
    const idx = localAppointments.value.findIndex((a) => a.id === appointmentId)
    if (idx !== -1) {
      localAppointments.value[idx] = updated
    }
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { message?: string } } }
    cancelError.value = axiosErr.response?.data?.message ?? 'Could not cancel appointment. Please try again.'
  } finally {
    cancellingId.value = null
  }
}
</script>

<template>
  <!-- BOOK mode -->
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

  <!-- CHECK / CANCEL mode -->
  <div v-else class="py-6">
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar :color="avatarColor[mode]" size="48">
        <v-icon color="white">mdi-calendar-check</v-icon>
      </v-avatar>
      <div>
        <h2 class="text-h6 font-weight-bold">{{ title[mode] }}</h2>
        <p v-if="patient" class="text-medium-emphasis text-caption">
          {{ patient.first_name }} {{ patient.last_name }} · {{ patient.email }}
        </p>
      </div>
    </div>

    <!-- Cancel error -->
    <v-expand-transition>
      <v-alert
        v-if="cancelError"
        type="error"
        variant="tonal"
        density="compact"
        rounded="lg"
        closable
        class="mb-4"
        @click:close="cancelError = null"
      >
        {{ cancelError }}
      </v-alert>
    </v-expand-transition>

    <!-- Empty state -->
    <v-card
      v-if="localAppointments.length === 0"
      rounded="xl"
      elevation="1"
      class="pa-8 text-center"
    >
      <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-calendar-blank-outline</v-icon>
      <p class="text-medium-emphasis">No appointments found.</p>
    </v-card>

    <!-- List -->
    <v-card
      v-for="appt in localAppointments"
      :key="appt.id"
      rounded="xl"
      elevation="1"
      class="mb-3 pa-5"
      :style="{
        borderLeft: `4px solid ${STATUS_CONFIG[appt.status]?.border ?? '#ccc'}`,
        opacity: appt.status === 'cancelled' ? 0.6 : 1,
        transition: 'opacity 0.2s ease',
      }"
    >
      <div class="d-flex justify-space-between align-center gap-3">
        <div class="flex-grow-1">
          <p class="font-weight-bold text-body-1">{{ appt.appointment_date }}</p>
          <p class="text-medium-emphasis text-caption">
            {{ appt.time_preference }} · {{ appt.assigned_time ?? 'Time TBD' }}
          </p>
          <p v-if="appt.notes" class="text-caption mt-1">{{ appt.notes }}</p>
        </div>

        <div class="d-flex align-center ga-2">
          <v-chip
            :color="STATUS_CONFIG[appt.status]?.border ?? 'grey'"
            variant="tonal"
            size="small"
          >
            <v-icon start size="14">{{ STATUS_CONFIG[appt.status]?.icon }}</v-icon>
            {{ STATUS_CONFIG[appt.status]?.label ?? appt.status }}
          </v-chip>

          <!-- Cancel button — only in cancel mode, only for scheduled appointments -->
          <v-btn
            v-if="mode === 'cancel' && appt.status === 'scheduled' && patient"
            size="small"
            color="error"
            variant="tonal"
            rounded="lg"
            :loading="cancellingId === appt.id"
            :disabled="cancellingId !== null"
            @click="cancelAppointment(appt.id)"
          >
            <v-icon start size="14">mdi-close-circle-outline</v-icon>
            Cancel
          </v-btn>
        </div>
      </div>
    </v-card>

    <v-btn color="primary" rounded size="large" block class="mt-4" @click="emit('back')">
      Back to Home
    </v-btn>
  </div>
</template>