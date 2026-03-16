<script setup lang="ts">
import { useRouter } from 'vue-router'
import { usePatientForm } from '@/composables/usePatientForm'
import { useDoctorSelection } from '@/composables/useDoctorSelection'
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
  form,
  lookup,
  handleSubmit,
  handleLookup,
  switchMode,
} = usePatientForm()

const { departments, availableDoctors } = useDoctorSelection(form)
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
        @update:field="(field, value) => (form[field] = value)"
        @submit="handleSubmit"
      />

      <LookupForm
        v-if="(mode === 'check' || mode === 'cancel') && !submitted"
        :mode="mode"
        :contact="lookup.contact"
        :card-color="cardColor"
        :teal-color="tealColor"
        @update:contact="lookup.contact = $event"
        @submit="handleLookup"
      />

      <SuccessState
        v-if="submitted"
        :mode="mode"
        :form="form"
        :accent-color="accentColor"
        :teal-color="tealColor"
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