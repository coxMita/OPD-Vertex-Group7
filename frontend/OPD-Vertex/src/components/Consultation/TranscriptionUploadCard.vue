<script setup lang="ts">
import { ref } from 'vue'
import { transcriptionApi } from '@/services/transcriptionApi'

const emit = defineEmits<{
  (e: 'transcriptReady', text: string): void
}>()

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isProcessing = ref(false)
const uploadProgress = ref(0)
const result = ref('')
const error = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

function pickFile(file: File) {
  if (file.name.endsWith('.wav') || file.type === 'audio/wav') {
    selectedFile.value = file
    result.value = ''
    error.value = ''
    uploadProgress.value = 0
  } else {
    error.value = 'Only .wav files are supported.'
  }
}

function onNativeInput(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files?.[0]) pickFile(files[0])
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer?.files ?? [])
  if (files[0]) pickFile(files[0])
}

function openFilePicker() {
  fileInputRef.value?.click()
}

async function runTranscription() {
  if (!selectedFile.value) return
  isProcessing.value = true
  uploadProgress.value = 0
  result.value = ''
  error.value = ''

  try {
    const { transcript } = await transcriptionApi.transcribeFile(
      selectedFile.value,
      (percent) => { uploadProgress.value = percent },
    )
    result.value = transcript
    emit('transcriptReady', transcript)
  } catch (err) {
    error.value = transcriptionApi.formatError(err, transcriptionApi.gatewayUrl)
  } finally {
    isProcessing.value = false
  }
}

function clearFile() {
  selectedFile.value = null
  result.value = ''
  error.value = ''
  uploadProgress.value = 0
  if (fileInputRef.value) fileInputRef.value.value = ''
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
        Upload a <code>.wav</code> file to invoke the transcription service through the
        API Gateway (<code>POST /api/v1/transcription/</code>). After a successful run,
        check RabbitMQ — the <code>transcription.completed</code> fanout exchange should
        carry the result.
      </p>

      <!-- Hidden native file input -->
      <input
        ref="fileInputRef"
        type="file"
        accept=".wav,audio/wav"
        style="display: none"
        @change="onNativeInput"
      />

      <!-- Drop zone -->
      <div
        class="drop-zone mb-4"
        :class="{ dragging: isDragging, 'has-file': !!selectedFile }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        @click="!selectedFile && openFilePicker()"
      >
        <div v-if="!selectedFile" class="drop-content text-center py-6">
          <v-icon size="40" color="indigo" class="mb-3" opacity="0.5">mdi-waveform</v-icon>
          <p class="drop-text">Drag &amp; drop a <strong>.wav</strong> file here</p>
          <p class="drop-sub mt-1">or click to browse</p>
        </div>

        <div v-else class="file-selected d-flex align-center ga-3 pa-3">
          <v-avatar color="indigo" size="40" rounded="lg">
            <v-icon color="white" size="20">mdi-waveform</v-icon>
          </v-avatar>
          <div class="flex-grow-1 min-width-0">
            <p class="file-name text-truncate">{{ selectedFile.name }}</p>
            <p class="file-size">{{ formatSize(selectedFile.size) }} · audio/wav</p>
          </div>
          <v-btn icon="mdi-close" size="x-small" variant="tonal" color="error" @click.stop="clearFile" />
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

      <!-- Upload progress -->
      <v-expand-transition>
        <div v-if="isProcessing" class="mt-4">
          <div class="d-flex justify-space-between mb-1">
            <span class="processing-text">
              {{ uploadProgress < 100 ? 'Uploading…' : 'Transcribing (may take a moment)…' }}
            </span>
            <span class="processing-text">{{ uploadProgress }}%</span>
          </div>
          <v-progress-linear
            :model-value="uploadProgress"
            :indeterminate="uploadProgress === 100"
            color="indigo"
            rounded
            height="4"
          />
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
            <div class="d-flex ga-2">
              <v-chip color="teal" size="x-small" variant="tonal">
                <v-icon start size="12">mdi-rabbit</v-icon>
                Event published to RabbitMQ
              </v-chip>
              <v-btn size="x-small" variant="tonal" color="success" @click="$emit('transcriptReady', result)">
                Use in Prescription
              </v-btn>
            </div>
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
.helper-text { font-size: 0.8rem; line-height: 1.6; opacity: 0.65; }
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
  min-height: 90px;
}
.drop-zone:hover:not(.has-file) {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.04);
}
.drop-zone.dragging {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
}
.drop-zone.has-file {
  border-style: solid;
  border-color: rgba(99, 102, 241, 0.4);
  cursor: default;
}
.drop-content { pointer-events: none; }
.drop-text { font-size: 0.88rem; margin: 0; }
.drop-sub { font-size: 0.76rem; opacity: 0.5; margin: 0; }
.file-name { font-size: 0.84rem; font-weight: 600; margin: 0; }
.file-size { font-size: 0.72rem; opacity: 0.55; margin: 0; }
.processing-text { font-size: 0.78rem; opacity: 0.6; }
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
  background: rgba(76, 175, 80, 0.06);
  border: 1px solid rgba(76, 175, 80, 0.2);
}
.result-text { font-size: 0.84rem; line-height: 1.7; margin: 0; }
</style>