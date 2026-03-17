<script setup lang="ts">
import FormField from '@/components/PatientForm/FormField.vue'
import FormSection from '@/components/PatientForm/FormSection.vue'
import DoctorPicker from '@/components/PatientForm/DoctorPicker.vue'
import type { PatientFormData } from '@/composables/usePatientForm'
import type { Doctor } from '@/composables/useDoctorSelection'

const props = defineProps<{
  form: PatientFormData
  departments: string[]
  availableDoctors: Doctor[]
  accentColor: string
  actionCardBg: string
  cardColor: string
  isDark: boolean
}>()

const emit = defineEmits<{
  (e: 'update:field', field: keyof PatientFormData, value: string): void
  (e: 'submit'): void
}>()

function update(field: keyof PatientFormData, value: string) {
  emit('update:field', field, value)
}
</script>

<template>
  <v-card rounded="xl" elevation="2" :color="cardColor" class="pa-8">
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar color="primary" size="40">
        <v-icon color="white" size="20">mdi-calendar-plus</v-icon>
      </v-avatar>
      <div>
        <h2 class="text-h6 font-weight-bold">New Appointment</h2>
        <p class="text-medium-emphasis text-caption">Fill in your details below</p>
      </div>
    </div>

    <FormSection title="Personal Information" icon="mdi-account">
      <v-row>
        <v-col cols="12" sm="6">
          <FormField
            label="First Name"
            placeholder="Maria"
            :model-value="form.firstName"
            @update:model-value="update('firstName', $event)"
          />
        </v-col>
        <v-col cols="12" sm="6">
          <FormField
            label="Last Name"
            placeholder="Andersen"
            :model-value="form.lastName"
            @update:model-value="update('lastName', $event)"
          />
        </v-col>
        <v-col cols="12" sm="6">
          <FormField
            label="Phone Number"
            placeholder="+45 12 34 56 78"
            :model-value="form.phone"
            @update:model-value="update('phone', $event)"
          />
        </v-col>
        <v-col cols="12" sm="6">
          <FormField
            label="Email"
            placeholder="maria@example.com"
            type="email"
            :model-value="form.email"
            @update:model-value="update('email', $event)"
          />
        </v-col>
      </v-row>
    </FormSection>

    <FormSection title="Appointment Details" icon="mdi-calendar-clock">
      <v-row>
        <v-col cols="12" sm="6">
          <FormField
            label="Preferred Date"
            type="date"
            :model-value="form.date"
            @update:model-value="update('date', $event)"
          />
        </v-col>
        <v-col cols="12" sm="6">
          <label class="field-label">Preferred Time</label>
          <v-btn-toggle
            :model-value="form.time"
            color="primary"
            rounded="lg"
            variant="outlined"
            mandatory
            divided
            class="w-100"
            @update:model-value="update('time', $event)"
          >
            <v-btn value="AM" class="flex-grow-1">
              <v-icon start size="16">mdi-weather-sunny</v-icon>AM
            </v-btn>
            <v-btn value="PM" class="flex-grow-1">
              <v-icon start size="16">mdi-weather-sunset</v-icon>PM
            </v-btn>
          </v-btn-toggle>
        </v-col>
        <v-col cols="12">
          <FormField
            label="Reason for Visit"
            placeholder="e.g. General checkup, follow-up..."
            :model-value="form.reason"
            @update:model-value="update('reason', $event)"
          />
        </v-col>
        <v-col cols="12">
          <label class="field-label">Department</label>
          <v-select
            :model-value="form.department"
            :items="departments"
            variant="outlined"
            rounded="lg"
            density="comfortable"
            hide-details
            @update:model-value="update('department', $event)"
          />
        </v-col>
        <v-col cols="12">
          <DoctorPicker
            :doctors="availableDoctors"
            :model-value="form.doctor"
            :accent-color="accentColor"
            :action-card-bg="actionCardBg"
            :is-dark="isDark"
            @update:model-value="update('doctor', $event)"
          />
        </v-col>
      </v-row>
    </FormSection>

    <v-btn
      color="primary"
      size="x-large"
      rounded="lg"
      block
      elevation="0"
      class="mt-4"
      @click="emit('submit')"
    >
      <span class="font-weight-bold">Confirm Booking</span>
      <v-icon end>mdi-arrow-right</v-icon>
    </v-btn>
  </v-card>
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