<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'transcriptReady', text: string): void
}>()

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isProcessing = ref(false)
const result = ref('')
const error = ref('')

// Simulated gateway endpoint
const TRANSCRIPTION_ENDPOINT = 'http://localhost:8000/api/transcription/transcribe'

function handleFileChange(files: File[]) {
  if (files.length > 0) {
    selectedFile.value = files[0]
    result.value = ''
    error.value = ''
  }
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer?.files ?? [])
  const wav = files.find(f => f.name.endsWith('.wav') || f.type === 'audio/wav')
  if (wav) {
    selectedFile.value = wav
    result.value = ''
    error.value = ''
  }
}

async function runTranscription() {
  if (!selectedFile.value) return
  isProcessing.value = true
  result.value = ''
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await fetch(TRANSCRIPTION_ENDPOINT, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    // Transcription service returns { text: string } or { transcript: string }
    const text = data.text ?? data.transcript ?? JSON.stringify(data)
    result.value = text
    emit('transcriptReady', text)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to reach transcription service'
  } finally {
    isProcessing.value = false
  }
}

function clearFile() {
  selectedFile.value = null
  result.value = ''
  error.value = ''
}

function formatSize(bytes: number) {
  return bytes > 1024 * 1024
    ? `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    : `${(bytes / 1024).toFixed(1)} KB`
}
</script>

<template>
  <v-card rounded="lg" elevation="1" class="mb-4">
    <div class="card-header px-5 pt-4 pb-3 d-flex align-center justify-space-between">
      <div class="section-label">
        <v-icon size="14" color="indigo" class="mr-1">mdi-circle</v-icon>
        TRANSCRIPTION TEST — WAV UPLOAD
      </div>
      <v-chip color="indigo" size="x-small" variant="tonal">
        <v-icon start size="12">mdi-flask</v-icon>
        Dev Testing
      </v-chip>
    </div>

    <v-divider />

    <div class="pa-5">
      <p class="helper-text mb-4">
        Upload a <code>.wav</code> file to test the transcription service directly — mirrors the Swagger UI flow.
        The request goes to <code>POST /api/transcription/transcribe</code> via the API Gateway.
      </p>

      <!-- Drop zone -->
      <div
        class="drop-zone mb-4"
        :class="{ dragging: isDragging, 'has-file': !!selectedFile }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <v-file-input
          v-if="!selectedFile"
          accept=".wav,audio/wav"
          hide-details
          variant="plain"
          class="file-input-hidden"
          @update:model-value="handleFileChange"
        >
          <template #default>
            <div class="drop-content text-center py-4">
              <v-icon size="40" color="indigo" class="mb-3" opacity="0.5">mdi-waveform</v-icon>
              <p class="drop-text">Drag &amp; drop a <strong>.wav</strong> file here</p>
              <p class="drop-sub mt-1">or click to browse</p>
            </div>
          </template>
        </v-file-input>

        <div v-else class="file-selected d-flex align-center ga-3 pa-3">
          <v-avatar color="indigo" size="40" rounded="lg">
            <v-icon color="white" size="20">mdi-waveform</v-icon>
          </v-avatar>
          <div class="flex-grow-1 min-width-0">
            <p class="file-name text-truncate">{{ selectedFile.name }}</p>
            <p class="file-size">{{ formatSize(selectedFile.size) }} · audio/wav</p>
          </div>
          <v-btn
            icon="mdi-close"
            size="x-small"
            variant="tonal"
            color="error"
            @click.stop="clearFile"
          />
        </div>
      </div>

      <!-- Run button -->
      <v-btn
        color="indigo"
        rounded="lg"
        block
        :disabled="!selectedFile || isProcessing"
        :loading="isProcessing"
        size="large"
        @click="runTranscription"
      >
        <v-icon start>mdi-play-circle</v-icon>
        Run Transcription
      </v-btn>

      <!-- Processing indicator -->
      <v-expand-transition>
        <div v-if="isProcessing" class="text-center mt-4">
          <v-progress-linear indeterminate color="indigo" rounded height="3" />
          <p class="processing-text mt-2">Sending to transcription service...</p>
        </div>
      </v-expand-transition>

      <!-- Error -->
      <v-expand-transition>
        <v-alert
          v-if="error"
          type="error"
          variant="tonal"
          rounded="lg"
          density="compact"
          class="mt-4"
        >
          <strong>Error:</strong> {{ error }}
        </v-alert>
      </v-expand-transition>

      <!-- Result -->
      <v-expand-transition>
        <div v-if="result" class="mt-4">
          <div class="d-flex align-center justify-space-between mb-2">
            <span class="result-label">
              <v-icon size="14" color="success" class="mr-1">mdi-check-circle</v-icon>
              Transcription Result
            </span>
            <v-btn
              size="x-small"
              variant="tonal"
              color="success"
              @click="$emit('transcriptReady', result)"
            >
              Use in Prescription
            </v-btn>
          </div>
          <div class="result-box">
            <p class="result-text">{{ result }}</p>
          </div>
        </div>
      </v-expand-transition>
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

.helper-text {
  font-size: 0.8rem;
  line-height: 1.6;
  opacity: 0.65;
}

code {
  background: rgba(var(--v-theme-on-surface), 0.08);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.78rem;
}

.drop-zone {
  border: 2px dashed rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
  min-height: 80px;
}

.drop-zone.dragging {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.05);
}

.drop-zone.has-file {
  border-style: solid;
  border-color: rgba(99, 102, 241, 0.4);
}

.file-input-hidden :deep(.v-field) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.drop-content {
  pointer-events: none;
}

.drop-text {
  font-size: 0.88rem;
  margin: 0;
}

.drop-sub {
  font-size: 0.76rem;
  opacity: 0.5;
  margin: 0;
}

.file-selected {
  border-radius: 10px;
}

.file-name {
  font-size: 0.84rem;
  font-weight: 600;
  margin: 0;
}

.file-size {
  font-size: 0.72rem;
  opacity: 0.55;
  margin: 0;
}

.processing-text {
  font-size: 0.78rem;
  opacity: 0.6;
}

.result-label {
  font-size: 0.75rem;
  font-weight: 600;
  opacity: 0.7;
  display: flex;
  align-items: center;
}

.result-box {
  padding: 14px 16px;
  border-radius: 10px;
  background: rgba(var(--v-theme-success, 76, 175, 80), 0.06);
  border: 1px solid rgba(76, 175, 80, 0.2);
}

.result-text {
  font-size: 0.84rem;
  line-height: 1.7;
  margin: 0;
}
</style>