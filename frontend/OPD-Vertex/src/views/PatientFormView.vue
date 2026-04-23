<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePatientForm } from '@/composables/usePatientForm'
import { useDoctorSelection } from '@/composables/useDoctorSelection'
import { userApi } from '@/services/userApi'
import { appointmentApi } from '@/services/appointmentApi'
import { emailApi } from '@/services/emailApi'
import ModeSelector from '@/components/PatientForm/ModeSelector.vue'
import BookingForm from '@/components/PatientForm/BookingForm.vue'
import LookupForm from '@/components/PatientForm/LookupForm.vue'
import SuccessState from '@/components/PatientForm/SuccessState.vue'

const router = useRouter()

const {
  isDark,
  accentColor,
  tealColor,
  cardColor,
  actionCardBg,
  mode,
  submitted,
  submitting,
  submitError,
  form,
  lookupLoading,
  lookupError,
  lookedUpPatient,
  lookedUpAppointments,
  lookup,
  handleLookup,
  switchMode,
} = usePatientForm()

const { departments, availableDoctors, fetchDoctorsByDepartment } = useDoctorSelection(form)

onMounted(() => {
  // Fetch doctors for the default department on load
  fetchDoctorsByDepartment(form.value.department)
})

async function handleSubmit() {
  submitError.value = null
  submitting.value = true

  try {
    // Step 1: find-or-create patient
    const patient = await userApi.findOrCreatePatient({
      first_name: form.value.firstName,
      last_name: form.value.lastName,
      email: form.value.email,
      phone_number: Number(form.value.phone_number),
      date_of_birth: form.value.dateOfBirth,
      gender: form.value.gender,
    })

    // Step 2: create appointment
    const appointment = await appointmentApi.createAppointment({
      patient_id: patient.patient_id,
      doctor_id: form.value.doctorId,
      appointment_date: form.value.date,
      time_preference: form.value.time as 'AM' | 'PM',
      notes: form.value.reason || null,
    })

    // Step 3: Send confirmation email
    try {
      await emailApi.sendEmail({
        to_email: form.value.email,
        subject: 'Appointment Confirmation - OPD Vertex',
        message: `Hello ${form.value.firstName},\n\nYour appointment has been successfully booked.\n\nDate: ${form.value.date}\nAssigned Time: ${appointment.assigned_time || form.value.time}\n\nPlease arrive 10 minutes early.\n\nBest regards,\nOPD Vertex Staff`,
        is_html: false,
      })
    } catch (emailErr) {
      console.warn('Could not dispatch confirmation email:', emailErr)
    }

    submitted.value = true
  } catch (err: unknown) {
    console.error('Booking failed:', err)
    const axiosErr = err as { response?: { data?: { message?: string }; status?: number } }
    if (axiosErr.response?.status === 409) {
      submitError.value = 'No available slots for this doctor on the selected date and time. Please choose another date or time.'
    } else if (axiosErr.response?.data?.message) {
      submitError.value = axiosErr.response.data.message
    } else {
      submitError.value = 'Booking failed. Please check your details and try again.'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-bg">
    <v-container class="py-10" max-width="680">

      <v-btn variant="text" class="mb-6" @click="router.push('/')">
        <v-icon start>mdi-arrow-left</v-icon>
        Back to Home
      </v-btn>

      <ModeSelector
        :model-value="mode"
        :accent-color="accentColor"
        :teal-color="tealColor"
        :action-card-bg="actionCardBg"
        @update:model-value="switchMode($event)"
      />

      <BookingForm
        v-if="mode === 'book' && !submitted"
        :form="form"
        :departments="departments"
        :available-doctors="availableDoctors"
        :accent-color="accentColor"
        :action-card-bg="actionCardBg"
        :card-color="cardColor"
        :is-dark="isDark"
        :submitting="submitting"
        :submit-error="submitError"
        @update:field="(field, value) => (form[field] = value as any)"
        @submit="handleSubmit"
      />

      <LookupForm
        v-if="(mode === 'check' || mode === 'cancel') && !submitted"
        :mode="mode"
        :contact="lookup.contact"
        :card-color="cardColor"
        :teal-color="tealColor"
        :loading="lookupLoading"
        :error="lookupError"
        @update:contact="lookup.contact = $event"
        @submit="handleLookup"
      />

      <SuccessState
        v-if="submitted"
        :mode="mode"
        :form="form"
        :accent-color="accentColor"
        :teal-color="tealColor"
        :patient="lookedUpPatient"
        :appointments="lookedUpAppointments"
        @back="router.push('/')"
      />

    </v-container>
  </div>
</template>

<style scoped>
.page-bg {
  min-height: 100vh;
  background: v-bind('isDark ? "linear-gradient(135deg, #1a1c52 20%, #2d1940 50%, #326071 100%)" : "linear-gradient(135deg, #fcf9ea 0%, #badfdb 50%, #ffa4a4 100%)"');
}
</style>