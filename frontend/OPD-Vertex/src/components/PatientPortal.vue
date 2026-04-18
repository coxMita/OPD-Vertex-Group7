<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const activePanel = ref('book-panel')
const doctors = ref<any[]>([])
const isLoadingDoctors = ref(false)

const fetchDoctors = async () => {
  if (!authStore.isAuthenticated) return
  
  isLoadingDoctors.value = true
  try {
    const response = await axios.get('http://localhost:8080/api/v1/users/doctors', {
      headers: {
        Authorization: `Bearer ${authStore.keycloakManager?.token}`
      }
    })
    doctors.value = response.data
  } catch (error) {
    console.error('Failed to fetch doctors:', error)
  } finally {
    isLoadingDoctors.value = false
  }
}

onMounted(() => {
  fetchDoctors()
})

const showPanel = (id: string) => {
  activePanel.value = id
}

const showLookup = ref({
  'check-result': false,
  'cancel-result': false
})

const doLookup = (id: 'check-result' | 'cancel-result') => {
  showLookup.value[id] = true
}

const cancelled = ref<{[key: number]: boolean}>({})

const doCancelRow = (id: number) => {
  if (confirm('Cancel this appointment?')) {
    cancelled.value[id] = true
  }
}
</script>

<template>
  <div id="patient-view" class="view patient-view active">
    <div class="patient-card">
      <div class="patient-card-header">
        <h2>Book an Appointment</h2>
        <p>OPD-Vertex Patient Portal · Outpatient Department</p>
      </div>
      <div class="patient-card-body">
        <div class="action-row">
          <button 
            class="action-btn book" 
            :class="{ 'active-btn': activePanel === 'book-panel' }"
            @click="showPanel('book-panel')"
          >
            <span class="btn-icon">📅</span>Book Appointment
          </button>
          <button 
            class="action-btn check" 
            :class="{ 'active-btn': activePanel === 'check-panel' }"
            @click="showPanel('check-panel')"
          >
            <span class="btn-icon">🔍</span>Check Appointment
          </button>
          <button 
            class="action-btn cancel" 
            :class="{ 'active-btn': activePanel === 'cancel-panel' }"
            @click="showPanel('cancel-panel')"
          >
            <span class="btn-icon">✕</span>Cancel
          </button>
        </div>

        <!-- BOOK -->
        <div id="book-panel" class="form-panel" :class="{ visible: activePanel === 'book-panel' }">
          <div class="form-panel-inner">
            <h3>📅 <span class="panel-badge badge-book">New Booking</span></h3>
            <div class="form-row">
              <div class="form-group"><label>First Name</label><input type="text" placeholder="Maria"></div>
              <div class="form-group"><label>Last Name</label><input type="text" placeholder="Andersen"></div>
            </div>
            <div class="form-row">
              <div class="form-group"><label>Phone Number</label><input type="tel" placeholder="+45 12 34 56 78"></div>
              <div class="form-group"><label>Email</label><input type="email" placeholder="maria@example.com"></div>
            </div>
            <div class="form-row">
              <div class="form-group"><label>Preferred Date</label><input type="date"></div>
              <div class="form-group"><label>Preferred Time</label><input type="time"></div>
            </div>
            <div class="form-group"><label>Reason for Visit</label><input type="text" placeholder="e.g. General checkup, follow-up..."></div>
            <div class="form-group">
              <label>Department</label>
              <select>
                <option>General Practice</option>
                <option>Cardiology</option>
                <option>Dermatology</option>
                <option>Neurology</option>
                <option>Orthopedics</option>
              </select>
            </div>
            <div class="form-group">
              <label>Doctor</label>
              <select>
                <option v-if="isLoadingDoctors">Loading doctors...</option>
                <option v-else-if="doctors.length === 0">No doctors available</option>
                <option v-for="doctor in doctors" :key="doctor.doctor_id" :value="doctor.doctor_id">
                  Dr. {{ doctor.full_name }} ({{ doctor.department_name }})
                </option>
              </select>
            </div>
            <button class="submit-btn book-submit" @click="alert('✅ Appointment booked! Confirmation sent to your email.')">Confirm Booking →</button>
          </div>
        </div>

        <!-- CHECK -->
        <div id="check-panel" class="form-panel" :class="{ visible: activePanel === 'check-panel' }">
          <div class="form-panel-inner">
            <h3>🔍 <span class="panel-badge badge-check">Check Status</span></h3>
            <div class="form-group">
              <label>Phone Number or Email</label>
              <input type="text" id="check-input" placeholder="Enter your phone or email...">
            </div>
            <button class="submit-btn check-submit" @click="doLookup('check-result')">Find My Appointments →</button>
            <div id="check-result" class="lookup-result" :class="{ visible: showLookup['check-result'] }">
              <div class="appt-row">
                <div class="appt-info"><strong>Dr. Hansen – General Practice</strong><span>Mon 24 Feb 2026 · 09:00</span></div>
                <span class="appt-confirmed">Confirmed</span>
              </div>
              <div class="appt-row">
                <div class="appt-info"><strong>Dr. Nielsen – Cardiology</strong><span>Thu 27 Feb 2026 · 14:00</span></div>
                <span class="appt-confirmed">Confirmed</span>
              </div>
            </div>
          </div>
        </div>

        <!-- CANCEL -->
        <div id="cancel-panel" class="form-panel" :class="{ visible: activePanel === 'cancel-panel' }">
          <div class="form-panel-inner">
            <h3>✕ <span class="panel-badge badge-cancel">Cancel Appointment</span></h3>
            <div class="form-group">
              <label>Phone Number or Email</label>
              <input type="text" placeholder="Enter your phone or email...">
            </div>
            <button class="submit-btn cancel-submit" @click="doLookup('cancel-result')">Find My Appointments →</button>
            <div id="cancel-result" class="lookup-result" :class="{ visible: showLookup['cancel-result'] }">
              <div v-if="doctors.length > 0">
                <div v-for="(doctor, i) in doctors.slice(0, 2)" :key="doctor.doctor_id" class="appt-row" :style="{ opacity: cancelled[i] ? 0.45 : 1, textDecoration: cancelled[i] ? 'line-through' : 'none' }">
                  <div class="appt-info"><strong>Dr. {{ doctor.full_name }} – {{ doctor.department_name }}</strong><span>Mon 24 Feb 2026 · 09:00</span></div>
                  <button class="cancel-row-btn" :disabled="cancelled[i]" @click="doCancelRow(i)">{{ cancelled[i] ? 'Cancelled' : 'Cancel' }}</button>
                </div>
              </div>
              <div v-else>
                <div class="appt-row" :style="{ opacity: cancelled[1] ? 0.45 : 1, textDecoration: cancelled[1] ? 'line-through' : 'none' }">
                  <div class="appt-info"><strong>Dr. Hansen – General Practice</strong><span>Mon 24 Feb 2026 · 09:00</span></div>
                  <button class="cancel-row-btn" :disabled="cancelled[1]" @click="doCancelRow(1)">{{ cancelled[1] ? 'Cancelled' : 'Cancel' }}</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
