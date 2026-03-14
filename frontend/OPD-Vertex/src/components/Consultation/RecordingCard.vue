<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

const emit = defineEmits<{
  (e: 'transcriptReady', text: string): void
  (e: 'statusChange', status: 'idle' | 'recording' | 'done'): void
}>()

const isRecording = ref(false)
const transcript = ref('')
const waveHeights = ref<number[]>(Array.from({ length: 48 }, () => 4))
let waveTimer: ReturnType<typeof setInterval> | null = null

const mockTranscript =
  'Patient reports sore throat and mild fever for 3 days. Tonsils inflamed. Temperature 38.2°C. BP 118/76. No allergies to penicillin confirmed. Recommending antibiotic course and analgesics.'

function startRecording() {
  isRecording.value = true
  transcript.value = ''
  emit('statusChange', 'recording')

  waveTimer = setInterval(() => {
    waveHeights.value = Array.from({ length: 48 }, () =>
      Math.floor(4 + Math.random() * 30)
    )
  }, 90)
}

function stopRecording() {
  isRecording.value = false
  if (waveTimer) {
    clearInterval(waveTimer)
    waveTimer = null
  }
  waveHeights.value = Array.from({ length: 48 }, () => 4)
  transcript.value = mockTranscript
  emit('transcriptReady', mockTranscript)
  emit('statusChange', 'done')
}

onUnmounted(() => {
  if (waveTimer) clearInterval(waveTimer)
})
</script>

<template>
  <v-card rounded="lg" elevation="1" class="mb-4">
    <div class="card-header px-5 pt-4 pb-3 d-flex align-center justify-space-between">
      <div class="section-label">
        <v-icon size="14" color="teal" class="mr-1">mdi-circle</v-icon>
        CONSULTATION RECORDING
      </div>
      <div class="rec-status d-flex align-center ga-2">
        <span class="rec-dot" :class="{ live: isRecording }" />
        <span class="rec-status-text">{{ isRecording ? 'Recording...' : 'Not recording' }}</span>
      </div>
    </div>

    <v-divider />

    <div class="pa-5">
      <!-- Controls -->
      <div class="d-flex justify-center ga-3 mb-4">
        <v-btn
          color="teal"
          rounded="pill"
          :disabled="isRecording"
          @click="startRecording"
          prepend-icon="mdi-record-circle"
        >
          Start Recording
        </v-btn>
        <v-btn
          color="error"
          rounded="pill"
          variant="tonal"
          :disabled="!isRecording"
          @click="stopRecording"
          prepend-icon="mdi-stop-circle"
        >
          Stop Recording
        </v-btn>
      </div>

      <!-- Waveform -->
      <div class="waveform mb-4">
        <div
          v-for="(h, i) in waveHeights"
          :key="i"
          class="wbar"
          :class="{ active: isRecording }"
          :style="{ height: `${h}px` }"
        />
      </div>

      <!-- Transcript -->
      <div class="transcript-box">
        <p v-if="!transcript" class="transcript-placeholder">
          Transcript will appear here after recording stops...
        </p>
        <p v-else class="transcript-text">{{ transcript }}</p>
      </div>
    </div>
  </v-card>
</template>

<style scoped>
.section-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  opacity: 0.5;
  display: flex;
  align-items: center;
}

.rec-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  flex-shrink: 0;
  transition: background 0.2s;
}

.rec-dot.live {
  background: #ef4444;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.rec-status-text {
  font-size: 0.75rem;
  opacity: 0.65;
}

.waveform {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  height: 44px;
}

.wbar {
  width: 3px;
  border-radius: 2px;
  background: rgba(var(--v-border-color), 0.5);
  transition: height 0.09s ease;
  min-height: 4px;
}

.wbar.active {
  background: rgb(var(--v-theme-teal, 0, 150, 136));
  background: #0d9488;
}

.transcript-box {
  min-height: 72px;
  padding: 14px 16px;
  border-radius: 10px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.transcript-placeholder {
  font-size: 0.84rem;
  font-style: italic;
  opacity: 0.45;
  margin: 0;
  line-height: 1.6;
}

.transcript-text {
  font-size: 0.84rem;
  line-height: 1.7;
  margin: 0;
  opacity: 0.85;
}
</style>