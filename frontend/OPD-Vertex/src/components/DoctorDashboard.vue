<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

const patients = [
  { name: 'Maria Andersen', phone: '+45 28 44 61 02', email: 'm.andersen@gmail.com', time: '09:00 · General Practice', dob: '14 Mar 1988', age: '37', gender: 'Female', cpr: '1403882941', blood: 'A+', allergy: 'Penicillin' },
  { name: 'Lars Christensen', phone: '+45 31 72 09 55', email: 'lars.c@outlook.com', time: '10:30 · Hypertension Follow-up', dob: '02 Jun 1965', age: '59', gender: 'Male', cpr: '0206651234', blood: 'O+', allergy: 'None' },
  { name: 'Sofie Møller', phone: '+45 50 12 38 77', email: 'sofie.m@gmail.com', time: '11:45 · Chest Pain (Urgent)', dob: '29 Sep 1995', age: '29', gender: 'Female', cpr: '2909956789', blood: 'B-', allergy: 'Aspirin' },
  { name: 'Henrik Madsen', phone: '+45 22 66 18 43', email: 'h.madsen@mail.dk', time: '13:00 · General Practice', dob: '11 Jan 1980', age: '45', gender: 'Male', cpr: '1101800001', blood: 'AB+', allergy: 'None' },
  { name: 'Anna Holm', phone: '+45 41 93 72 10', email: 'anna.holm@gmail.com', time: '08:30 · Diabetes Follow-up', dob: '07 Apr 1972', age: '52', gender: 'Female', cpr: '0704725555', blood: 'A-', allergy: 'Sulfonamides' },
  { name: 'Peter Skov', phone: '+45 26 88 43 91', email: 'p.skov@hotmail.com', time: '10:00 · Dermatology', dob: '18 Dec 1990', age: '34', gender: 'Male', cpr: '1812901234', blood: 'O-', allergy: 'None' }
]

const rxDemos = [
  "PATIENT: Maria Andersen\nDATE: 24 Feb 2026 | DR. HANSEN\n\nMEDICATIONS:\n1. Amoxicillin 500mg — 3× daily for 7 days\n Take with food. Complete full course.\n2. Ibuprofen 400mg — as needed (max 3/day)\n Avoid on empty stomach.",
  "PATIENT: Lars Christensen\nDATE: 24 Feb 2026 | DR. HANSEN\n\nMEDICATIONS:\n1. Amlodipine 5mg — 1× daily. Unchanged.\n2. Lisinopril 10mg — 1× daily. Monitor BP weekly.",
  "PATIENT: Sofie Møller ⚡ URGENT\nDATE: 24 Feb 2026 | DR. HANSEN\n\nREFERRAL: Cardiology — same day urgent\n\nIMMEDIATE:\n1. GTN Spray — sublingual if pain worsens",
  "PATIENT: Henrik Madsen\nDATE: 24 Feb 2026 | DR. HANSEN\n\nMEDICATIONS:\n1. Paracetamol 500mg — 4× daily as needed\n2. Vitamin D3 1000IU — 1× daily",
  "PATIENT: Anna Holm\nDATE: 25 Feb 2026 | DR. HANSEN\n\nMEDICATIONS:\n1. Metformin 850mg — 2× daily\n2. Empagliflozin 10mg — 1× daily",
  "PATIENT: Peter Skov\nDATE: 25 Feb 2026 | DR. PETERSEN\n\nMEDICATIONS:\n1. Betamethasone 0.1% cream — apply twice daily\n2. Cetirizine 10mg — 1× nightly"
]

const transcripts = [
  'Patient reports sore throat and mild fever for 3 days. Tonsils inflamed. Temperature 38.2°C. Recommending antibiotic course.',
  'Patient presents for hypertension follow-up. BP today 128/82 — improved. Continuing current regimen.',
  'Patient presents with acute chest pain radiating to left arm. ECG showing borderline ST changes. Urgent cardiology referral.',
  'Annual health check. BMI 24.2, BP 122/80. No complaints. Full blood work requested.',
  'Diabetes management review. HbA1c 7.1%. Foot examination normal. Continue current plan.',
  'New patient with itchy rash on forearms. Consistent with atopic eczema. Prescribing topical corticosteroid.'
]

const currentIdx = ref(0)
const ptStatus = ref('waiting')
const prescription = ref(rxDemos[0])
const transcript = ref('Transcript will appear here after recording stops...')
const isRecording = ref(false)
const waveBars = ref(Array(50).fill({ height: 6, on: false }))
let waveTimer: any = null

const selectPatient = (idx: number) => {
  currentIdx.value = idx
  prescription.value = rxDemos[idx] || ''
  transcript.value = 'Transcript will appear here after recording stops...'
  ptStatus.value = 'waiting'
  stopRec()
}

const startRec = () => {
  isRecording.value = true
  ptStatus.value = 'active'
  waveTimer = setInterval(() => {
    waveBars.value = waveBars.value.map(() => ({
      height: 4 + Math.random() * 32,
      on: Math.random() > 0.25
    }))
  }, 85)
}

const stopRec = () => {
  isRecording.value = false
  clearInterval(waveTimer)
  waveBars.value = Array(50).fill({ height: 6, on: false })
  if (transcript.value === 'Listening...' || transcript.value.includes('Transcript will appear here')) {
    transcript.value = transcripts[currentIdx.value] || transcripts[0]
  }
}

const regenRx = () => {
  prescription.value = '✦ Generating via Llama 3...'
  setTimeout(() => {
    prescription.value = rxDemos[currentIdx.value] || rxDemos[0]
  }, 1100)
}

const approveRx = () => {
  ptStatus.value = 'done'
  alert(`✅ Prescription approved and dispatched to ${patients[currentIdx.value].email} via Email Service.`)
}

onUnmounted(() => {
  clearInterval(waveTimer)
})
</script>

<template>
  <div id="doctor-view" class="view doctor-view active">
    <div class="dashboard">
      <!-- SIDEBAR -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <h3>Upcoming Appointments</h3>
          <div class="sidebar-search">
            <span class="search-icon">⌕</span>
            <input type="text" placeholder="Search patients...">
          </div>
        </div>
        <div class="appt-list">
          <div class="date-label">Today — Mon 24 Feb</div>
          <div 
            v-for="(p, idx) in patients.slice(0, 4)" 
            :key="idx"
            class="appt-item" 
            :class="{ selected: currentIdx === idx, urgent: p.time.includes('Urgent') }"
            @click="selectPatient(idx)"
          >
            <div class="appt-item-top">
              <span class="appt-item-name">{{ p.name }}</span>
              <span class="appt-item-time">{{ p.time.split(' · ')[0] }}</span>
            </div>
            <div class="appt-item-type">{{ p.time.split(' · ')[1] }}</div>
            <span v-if="idx % 2 === 0" class="tag tag-new">New Patient</span>
            <span v-else-if="p.time.includes('Urgent')" class="tag tag-urgent">⚡ Urgent</span>
            <span v-else class="tag tag-follow">Follow-up</span>
          </div>
          <div class="date-label">Tomorrow — Tue 25 Feb</div>
          <div 
            v-for="(p, idx) in patients.slice(4)" 
            :key="idx + 4"
            class="appt-item" 
            :class="{ selected: currentIdx === idx + 4 }"
            @click="selectPatient(idx + 4)"
          >
            <div class="appt-item-top">
              <span class="appt-item-name">{{ p.name }}</span>
              <span class="appt-item-time">{{ p.time.split(' · ')[0] }}</span>
            </div>
            <div class="appt-item-type">{{ p.time.split(' · ')[1] }}</div>
            <span class="tag tag-follow">Follow-up</span>
          </div>
        </div>
      </aside>

      <!-- MAIN PANEL -->
      <main class="main-panel">
        <div class="main-panel-header">
          <div class="patient-meta">
            <h2>{{ patients[currentIdx].name }}</h2>
            <div class="meta-row">
              <span class="meta-pill">📞 {{ patients[currentIdx].phone }}</span>
              <span class="meta-pill">📧 {{ patients[currentIdx].email }}</span>
              <span class="meta-pill">🕐 {{ patients[currentIdx].time }}</span>
            </div>
          </div>
          <span class="status-badge" :class="'status-' + ptStatus">
            {{ ptStatus === 'waiting' ? 'Waiting' : ptStatus === 'active' ? '● Active' : '✓ Done' }}
          </span>
        </div>

        <div class="main-content">
          <!-- Patient Info -->
          <div class="card">
            <div class="card-header">
              <span class="card-title"><span class="cdot cdot-blue"></span>Patient Information</span>
            </div>
            <div class="card-body">
              <div class="info-grid">
                <div class="info-cell"><label>DOB</label><span>{{ patients[currentIdx].dob }}</span></div>
                <div class="info-cell"><label>Age</label><span>{{ patients[currentIdx].age }} years</span></div>
                <div class="info-cell"><label>Gender</label><span>{{ patients[currentIdx].gender }}</span></div>
                <div class="info-cell"><label>CPR / ID</label><span>{{ patients[currentIdx].cpr }}</span></div>
                <div class="info-cell"><label>Blood Type</label><span>{{ patients[currentIdx].blood }}</span></div>
                <div class="info-cell"><label>Allergies</label><span>{{ patients[currentIdx].allergy }}</span></div>
              </div>
            </div>
          </div>

          <!-- Recording -->
          <div class="card">
            <div class="card-header">
              <span class="card-title"><span class="cdot cdot-teal"></span>Consultation Recording</span>
              <div class="rec-status">
                <div class="rec-dot" :class="{ live: isRecording }"></div>
                <span>{{ isRecording ? 'Recording...' : 'Not recording' }}</span>
              </div>
            </div>
            <div class="card-body">
              <div class="rec-zone">
                <div class="rec-controls">
                  <button class="rec-btn start" :disabled="isRecording" @click="startRec()">● Start Recording</button>
                  <button class="rec-btn stop" :disabled="!isRecording" @click="stopRec()">■ Stop Recording</button>
                </div>
                <div class="waveform">
                  <div 
                    v-for="(bar, i) in waveBars" 
                    :key="i" 
                    class="wbar" 
                    :class="{ on: bar.on }"
                    :style="{ height: bar.height + 'px' }"
                  ></div>
                </div>
                <div class="transcript-box">{{ transcript }}</div>
              </div>
            </div>
          </div>

          <!-- Prescription -->
          <div class="card">
            <div class="card-header">
              <span class="card-title"><span class="cdot cdot-navy"></span>Prescription</span>
              <span class="ai-badge">✦ AI Generated</span>
            </div>
            <div class="card-body">
              <div class="rx-meta-row">
                <span class="rx-label">Review and edit the AI-generated prescription</span>
              </div>
              <textarea class="rx-textarea" v-model="prescription"></textarea>
              <div class="rx-actions">
                <button class="rxbtn sec" @click="prescription = ''">Clear</button>
                <button class="rxbtn prim" @click="regenRx()">✦ Regenerate with AI</button>
                <button class="rxbtn app" @click="approveRx()">✓ Approve & Send</button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
