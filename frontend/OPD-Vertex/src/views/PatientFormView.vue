<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import FormField from '@/components/PatientForm/FormField.vue'
import FormSection from '@/components/PatientForm/FormSection.vue'

const router = useRouter()
const vuetifyTheme = useTheme()
const isDark = computed(() => vuetifyTheme.current.value.dark)

const accentColor = computed(() => isDark.value ? '#29b6f6' : '#c0687a')
const tealColor = computed(() => isDark.value ? '#4dd0e1' : '#2a9d8f')
const cardColor = computed(() => isDark.value ? '#1e1e1e' : '#fefdf5')
const actionCardBg = computed(() => isDark.value ? '#2a2a2a' : '#fefdf5')

type Mode = 'book' | 'check' | 'cancel'
const mode = ref<Mode>('book')
const submitted = ref(false)

const form = ref({
  firstName: '',
  lastName: '',
  phone: '',
  email: '',
  date: '',
  time: 'AM',
  reason: '',
  department: 'General Practice',
  doctor: '',
})

const lookup = ref({ contact: '' })

const departments = [
  'General Practice', 'Cardiology', 'Dermatology',
  'Neurology', 'Orthopedics', 'Pediatrics', 'Psychiatry',
]

const doctorsByDepartment: Record<string, { name: string; specialty: string; avatar: string }[]> = {
  'General Practice': [
    { name: 'Dr. Ana Popescu', specialty: 'General Practitioner', avatar: 'AP' },
    { name: 'Dr. Ion Marinescu', specialty: 'General Practitioner', avatar: 'IM' },
  ],
  'Cardiology': [
    { name: 'Dr. Elena Dumitrescu', specialty: 'Cardiologist', avatar: 'ED' },
    { name: 'Dr. Mihai Ionescu', specialty: 'Interventional Cardiologist', avatar: 'MI' },
  ],
  'Dermatology': [
    { name: 'Dr. Raluca Stan', specialty: 'Dermatologist', avatar: 'RS' },
    { name: 'Dr. Andrei Popa', specialty: 'Cosmetic Dermatologist', avatar: 'AP' },
  ],
  'Neurology': [
    { name: 'Dr. Cristina Vlad', specialty: 'Neurologist', avatar: 'CV' },
    { name: 'Dr. Bogdan Radu', specialty: 'Pediatric Neurologist', avatar: 'BR' },
  ],
  'Orthopedics': [
    { name: 'Dr. Alexandru Marin', specialty: 'Orthopedic Surgeon', avatar: 'AM' },
    { name: 'Dr. Ioana Constantin', specialty: 'Sports Medicine', avatar: 'IC' },
  ],
  'Pediatrics': [
    { name: 'Dr. Maria Georgescu', specialty: 'Pediatrician', avatar: 'MG' },
    { name: 'Dr. Vlad Nistor', specialty: 'Neonatologist', avatar: 'VN' },
  ],
  'Psychiatry': [
    { name: 'Dr. Andreea Matei', specialty: 'Psychiatrist', avatar: 'AM' },
    { name: 'Dr. Radu Florescu', specialty: 'Child Psychiatrist', avatar: 'RF' },
  ],
}

// Resets selected doctor whenever department changes
const availableDoctors = computed(() => {
  form.value.doctor = ''
  return doctorsByDepartment[form.value.department] ?? []
})

const handleSubmit = () => { submitted.value = true }
const handleLookup = () => { submitted.value = true }

const switchMode = (m: Mode) => {
  mode.value = m
  submitted.value = false
}
</script>

<template>
  <div class="page-bg">
    <v-container class="py-10" max-width="680">

      <v-btn variant="text" class="mb-6" @click="router.push('/')">
        <v-icon start>mdi-arrow-left</v-icon>
        Back to Home
      </v-btn>

      <!-- Action selector -->
      <v-row class="mb-8" no-gutters>
        <v-col cols="4" class="pr-2">
          <v-card
            class="action-card"
            :style="mode === 'book'
              ? { background: accentColor, border: 'none' }
              : { background: actionCardBg }"
            rounded="xl"
            elevation="0"
            @click="switchMode('book')"
          >
            <v-card-text class="d-flex flex-column align-center pa-5">
              <v-icon size="32" class="mb-2" :color="mode === 'book' ? 'white' : accentColor">
                mdi-calendar-plus
              </v-icon>
              <span class="text-body-2 font-weight-bold text-center"
                :style="{ color: mode === 'book' ? 'white' : '' }">
                Book Appointment
              </span>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="4" class="px-1">
          <v-card
            class="action-card"
            :style="mode === 'check'
              ? { background: tealColor, border: 'none' }
              : { background: actionCardBg }"
            rounded="xl"
            elevation="0"
            @click="switchMode('check')"
          >
            <v-card-text class="d-flex flex-column align-center pa-5">
              <v-icon size="32" class="mb-2" :color="mode === 'check' ? 'white' : tealColor">
                mdi-magnify
              </v-icon>
              <span class="text-body-2 font-weight-bold text-center"
                :style="{ color: mode === 'check' ? 'white' : '' }">
                Check Appointment
              </span>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="4" class="pl-2">
          <v-card
            class="action-card"
            :style="mode === 'cancel'
              ? { background: '#e57373', border: 'none' }
              : { background: actionCardBg }"
            rounded="xl"
            elevation="0"
            @click="switchMode('cancel')"
          >
            <v-card-text class="d-flex flex-column align-center pa-5">
              <v-icon size="32" class="mb-2" :color="mode === 'cancel' ? 'white' : '#e57373'">
                mdi-calendar-remove
              </v-icon>
              <span class="text-body-2 font-weight-bold text-center"
                :style="{ color: mode === 'cancel' ? 'white' : '' }">
                Cancel Appointment
              </span>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- BOOK -->
      <div v-if="mode === 'book' && !submitted">
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
                <FormField label="First Name" placeholder="Maria"
                  :model-value="form.firstName" @update:model-value="form.firstName = $event" />
              </v-col>
              <v-col cols="12" sm="6">
                <FormField label="Last Name" placeholder="Andersen"
                  :model-value="form.lastName" @update:model-value="form.lastName = $event" />
              </v-col>
              <v-col cols="12" sm="6">
                <FormField label="Phone Number" placeholder="+45 12 34 56 78"
                  :model-value="form.phone" @update:model-value="form.phone = $event" />
              </v-col>
              <v-col cols="12" sm="6">
                <FormField label="Email" placeholder="maria@example.com" type="email"
                  :model-value="form.email" @update:model-value="form.email = $event" />
              </v-col>
            </v-row>
          </FormSection>

          <FormSection title="Appointment Details" icon="mdi-calendar-clock">
            <v-row>
              <v-col cols="12" sm="6">
                <FormField label="Preferred Date" type="date"
                  :model-value="form.date" @update:model-value="form.date = $event" />
              </v-col>
              <v-col cols="12" sm="6">
                <label class="field-label">Preferred Time</label>
                <v-btn-toggle
                  v-model="form.time"
                  color="primary"
                  rounded="lg"
                  variant="outlined"
                  mandatory
                  divided
                  class="w-100"
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
                <FormField label="Reason for Visit" placeholder="e.g. General checkup, follow-up..."
                  :model-value="form.reason" @update:model-value="form.reason = $event" />
              </v-col>
              <v-col cols="12">
                <label class="field-label">Department</label>
                <v-select v-model="form.department" :items="departments"
                  variant="outlined" rounded="lg" density="comfortable" hide-details />
              </v-col>

              <!-- Doctor list — resets and animates when department changes -->
              <v-col cols="12">
                <v-expand-transition>
                  <div v-if="availableDoctors.length">
                    <label class="field-label mt-1">Select Doctor</label>
                    <div class="mt-2">
                      <v-card
                        v-for="doctor in availableDoctors"
                        :key="doctor.name"
                        :style="form.doctor === doctor.name
                          ? { border: `2px solid ${accentColor}`, background: isDark ? '#2a2a2a' : '#fff5f5' }
                          : { border: '2px solid transparent', background: actionCardBg }"
                        rounded="lg"
                        elevation="0"
                        class="doctor-card mb-2"
                        @click="form.doctor = doctor.name"
                      >
                        <v-card-text class="d-flex align-center ga-3 pa-4">
                          <v-avatar
                            :color="form.doctor === doctor.name ? accentColor : (isDark ? '#444' : '#e0e0e0')"
                            size="42"
                          >
                            <span class="text-caption font-weight-bold"
                              :style="{ color: form.doctor === doctor.name ? 'white' : (isDark ? '#ccc' : '#555') }">
                              {{ doctor.avatar }}
                            </span>
                          </v-avatar>
                          <div class="flex-grow-1">
                            <div class="text-body-2 font-weight-bold">{{ doctor.name }}</div>
                            <div class="text-caption text-medium-emphasis">{{ doctor.specialty }}</div>
                          </div>
                          <v-icon v-if="form.doctor === doctor.name" :color="accentColor" size="20">
                            mdi-check-circle
                          </v-icon>
                        </v-card-text>
                      </v-card>
                    </div>
                  </div>
                </v-expand-transition>
              </v-col>

            </v-row>
          </FormSection>

          <v-btn color="primary" size="x-large" rounded="lg" block elevation="0"
            class="mt-4" @click="handleSubmit">
            <span class="font-weight-bold">Confirm Booking</span>
            <v-icon end>mdi-arrow-right</v-icon>
          </v-btn>
        </v-card>
      </div>

      <!-- CHECK -->
      <div v-if="mode === 'check' && !submitted">
        <v-card rounded="xl" elevation="2" :color="cardColor" class="pa-8">
          <div class="d-flex align-center ga-3 mb-6">
            <v-avatar :color="tealColor" size="40">
              <v-icon color="white" size="20">mdi-magnify</v-icon>
            </v-avatar>
            <div>
              <h2 class="text-h6 font-weight-bold">Check Appointment</h2>
              <p class="text-medium-emphasis text-caption">Enter your contact info to find your bookings</p>
            </div>
          </div>
          <FormField label="Phone Number or Email" placeholder="Enter your phone or email..."
            :model-value="lookup.contact" @update:model-value="lookup.contact = $event" />
          <v-btn :color="tealColor" size="x-large" rounded="lg" block elevation="0"
            class="mt-6" @click="handleLookup">
            <span class="font-weight-bold" style="color:white">Find My Appointments</span>
            <v-icon end color="white">mdi-arrow-right</v-icon>
          </v-btn>
        </v-card>
      </div>

      <!-- CANCEL -->
      <div v-if="mode === 'cancel' && !submitted">
        <v-card rounded="xl" elevation="2" :color="cardColor" class="pa-8">
          <div class="d-flex align-center ga-3 mb-6">
            <v-avatar color="#e57373" size="40">
              <v-icon color="white" size="20">mdi-calendar-remove</v-icon>
            </v-avatar>
            <div>
              <h2 class="text-h6 font-weight-bold">Cancel Appointment</h2>
              <p class="text-medium-emphasis text-caption">We'll find your appointments so you can cancel</p>
            </div>
          </div>
          <FormField label="Phone Number or Email" placeholder="Enter your phone or email..."
            :model-value="lookup.contact" @update:model-value="lookup.contact = $event" />
          <v-btn color="#e57373" size="x-large" rounded="lg" block elevation="0"
            class="mt-6" @click="handleLookup">
            <span class="font-weight-bold" style="color:white">Find My Appointments</span>
            <v-icon end color="white">mdi-arrow-right</v-icon>
          </v-btn>
        </v-card>
      </div>

      <!-- SUCCESS -->
      <div v-if="submitted" class="text-center py-16">
        <v-avatar :color="mode === 'cancel' ? '#e57373' : mode === 'check' ? tealColor : 'primary'" size="80" class="mb-6">
          <v-icon size="44" color="white">mdi-check</v-icon>
        </v-avatar>
        <h2 class="text-h4 font-weight-bold mb-3">
          {{ mode === 'book' ? 'Booking Confirmed!' : 'Appointments Found!' }}
        </h2>
        <p class="text-medium-emphasis text-h6 mb-8">
          {{ mode === 'book'
            ? `We'll see you on ${form.date} at ${form.time} with ${form.doctor || 'your doctor'}.`
            : 'Check your email or phone for details.' }}
        </p>
        <v-btn color="primary" rounded size="large" @click="router.push('/')">
          Back to Home
        </v-btn>
      </div>

    </v-container>
  </div>
</template>

<style scoped>
.page-bg {
  min-height: 100vh;
  background: v-bind('isDark ? "linear-gradient(135deg, #1a1c52 20%, #2d1940 50%, #326071 100%)" : "linear-gradient(135deg, #fcf9ea 0%, #badfdb 50%, #ffa4a4 100%)"');
}
.field-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 6px;
  color: #6b7280;
}
.action-card {
  cursor: pointer;
  border: 2px solid transparent !important;
  transition: all 0.2s ease;
  height: 100%;
}
.action-card:hover {
  transform: translateY(-2px);
}
.doctor-card {
  cursor: pointer;
  transition: all 0.2s ease;
}
.doctor-card:hover {
  transform: translateX(3px);
}
</style>