<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { transcriptionApi } from '@/services/transcriptionApi'

const emit = defineEmits<{
  (e: 'transcriptReady', text: string): void
  (e: 'statusChange', status: 'idle' | 'recording' | 'processing' | 'done' | 'error'): void
}>()

// ── State ─────────────────────────────────────────────────────────────────────
const isRecording = ref(false)
const isProcessing = ref(false)
const uploadProgress = ref(0)
const transcript = ref('')
const errorMsg = ref('')
const waveHeights = ref<number[]>(Array.from({ length: 48 }, () => 4))
const recordingSeconds = ref(0)

// ── Internal refs ─────────────────────────────────────────────────────────────
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let audioStream: MediaStream | null = null
let audioContext: AudioContext | null = null
let analyser: AnalyserNode | null = null
let animFrame: number | null = null
let clockTimer: ReturnType<typeof setInterval> | null = null

// ── Waveform (real AnalyserNode data when recording, idle bars otherwise) ─────
function startWaveform(stream: MediaStream) {
  audioContext = new AudioContext()
  analyser = audioContext.createAnalyser()
  analyser.fftSize = 128
  const source = audioContext.createMediaStreamSource(stream)
  source.connect(analyser)

  const data = new Uint8Array(analyser.frequencyBinCount)

  function tick() {
    analyser!.getByteFrequencyData(data)
    waveHeights.value = Array.from({ length: 48 }, (_, i) => {
      const idx = Math.floor((i / 48) * data.length)
      return Math.max(4, Math.floor((data[idx] / 255) * 36))
    })
    animFrame = requestAnimationFrame(tick)
  }
  animFrame = requestAnimationFrame(tick)
}

function stopWaveform() {
  if (animFrame !== null) {
    cancelAnimationFrame(animFrame)
    animFrame = null
  }
  if (audioContext) {
    audioContext.close()
    audioContext = null
    analyser = null
  }
  waveHeights.value = Array.from({ length: 48 }, () => 4)
}

// ── Recording clock ───────────────────────────────────────────────────────────
function startClock() {
  recordingSeconds.value = 0
  clockTimer = setInterval(() => { recordingSeconds.value++ }, 1000)
}

function stopClock() {
  if (clockTimer) { clearInterval(clockTimer); clockTimer = null }
}

function formatTime(s: number) {
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const sec = (s % 60).toString().padStart(2, '0')
  return `${m}:${sec}`
}

// ── WAV encoding ──────────────────────────────────────────────────────────────
/**
 * Decode the browser's native container (webm/ogg), resample to 16 kHz mono,
 * then encode as a standard PCM WAV — exactly what Faster-Whisper expects.
 */
async function blobToWav(chunks: Blob[]): Promise<File> {
  const raw = new Blob(chunks)
  const arrayBuf = await raw.arrayBuffer()

  const decoded = await new AudioContext().decodeAudioData(arrayBuf)

  const targetSampleRate = 16000
  const offlineCtx = new OfflineAudioContext(
    1,
    Math.ceil(decoded.duration * targetSampleRate),
    targetSampleRate,
  )
  const src = offlineCtx.createBufferSource()
  src.buffer = decoded
  src.connect(offlineCtx.destination)
  src.start(0)
  const resampled = await offlineCtx.startRendering()

  const pcm = resampled.getChannelData(0)
  const wavBuf = pcmToWav(pcm, targetSampleRate)
  return new File([wavBuf], `recording_${Date.now()}.wav`, { type: 'audio/wav' })
}

function pcmToWav(pcm: Float32Array, sampleRate: number): ArrayBuffer {
  const numSamples = pcm.length
  const bytesPerSample = 2
  const blockAlign = bytesPerSample
  const byteRate = sampleRate * blockAlign
  const dataSize = numSamples * bytesPerSample
  const buf = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buf)

  const writeStr = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
  }
  const clamp = (v: number) => Math.max(-1, Math.min(1, v))

  writeStr(0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeStr(8, 'WAVE')
  writeStr(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)           // PCM
  view.setUint16(22, 1, true)           // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, byteRate, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, 16, true)          // 16-bit
  writeStr(36, 'data')
  view.setUint32(40, dataSize, true)

  let offset = 44
  for (let i = 0; i < numSamples; i++) {
    view.setInt16(offset, Math.round(clamp(pcm[i]) * 0x7fff), true)
    offset += 2
  }
  return buf
}

// ── Controls ──────────────────────────────────────────────────────────────────
async function startRecording() {
  errorMsg.value = ''
  transcript.value = ''
  uploadProgress.value = 0

  let stream: MediaStream
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
  } catch {
    errorMsg.value = 'Microphone access denied. Please allow microphone permission and try again.'
    emit('statusChange', 'error')
    return
  }

  audioStream = stream
  audioChunks = []

  const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg', ''].find(
    (m) => !m || MediaRecorder.isTypeSupported(m),
  ) ?? ''

  mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
  mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data) }
  mediaRecorder.onstop = handleRecordingStop

  mediaRecorder.start(200)
  isRecording.value = true
  startWaveform(stream)
  startClock()
  emit('statusChange', 'recording')
}

async function stopRecording() {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') return
  mediaRecorder.stop()
  audioStream?.getTracks().forEach((t) => t.stop())
  stopWaveform()
  stopClock()
  isRecording.value = false
}

async function handleRecordingStop() {
  isProcessing.value = true
  uploadProgress.value = 0
  emit('statusChange', 'processing')

  let wavFile: File
  try {
    wavFile = await blobToWav(audioChunks)
  } catch (err) {
    errorMsg.value = `Failed to encode audio: ${(err as Error).message}`
    isProcessing.value = false
    emit('statusChange', 'error')
    return
  }

  try {
    const { transcript: text } = await transcriptionApi.transcribeFile(
      wavFile,
      (percent) => { uploadProgress.value = percent },
    )
    transcript.value = text
    emit('transcriptReady', text)
    emit('statusChange', 'done')
  } catch (err) {
    errorMsg.value = transcriptionApi.formatError(err, transcriptionApi.gatewayUrl)
    emit('statusChange', 'error')
  } finally {
    isProcessing.value = false
    uploadProgress.value = 0
  }
}

// ── Cleanup ───────────────────────────────────────────────────────────────────
onUnmounted(() => {
  stopWaveform()
  stopClock()
  audioStream?.getTracks().forEach((t) => t.stop())
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
        <span class="rec-status-text">
          <template v-if="isRecording">Recording — {{ formatTime(recordingSeconds) }}</template>
          <template v-else-if="isProcessing">Transcribing…</template>
          <template v-else>Not recording</template>
        </span>
      </div>
    </div>

    <v-divider />

    <div class="pa-5">
      <!-- Controls -->
      <div class="d-flex justify-center ga-3 mb-4">
        <v-btn
          color="teal"
          rounded="pill"
          :disabled="isRecording || isProcessing"
          prepend-icon="mdi-record-circle"
          @click="startRecording"
        >
          Start Recording
        </v-btn>
        <v-btn
          color="error"
          rounded="pill"
          variant="tonal"
          :disabled="!isRecording"
          prepend-icon="mdi-stop-circle"
          @click="stopRecording"
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

      <!-- Upload / transcription progress -->
      <v-expand-transition>
        <div v-if="isProcessing" class="mb-4">
          <div class="d-flex justify-space-between mb-1">
            <span class="processing-text">
              {{ uploadProgress < 100 ? 'Uploading…' : 'Transcribing (may take a moment)…' }}
            </span>
            <span class="processing-text">{{ uploadProgress > 0 ? `${uploadProgress}%` : '' }}</span>
          </div>
          <v-progress-linear
            :model-value="uploadProgress"
            :indeterminate="uploadProgress === 100 || uploadProgress === 0"
            color="teal"
            rounded
            height="4"
          />
        </div>
      </v-expand-transition>

      <!-- Error -->
      <v-expand-transition>
        <v-alert
          v-if="errorMsg"
          type="error"
          variant="tonal"
          rounded="lg"
          density="compact"
          class="mb-4"
        >
          <strong>Error:</strong> {{ errorMsg }}
        </v-alert>
      </v-expand-transition>

      <!-- Transcript -->
      <div class="transcript-box">
        <p v-if="!transcript && !isProcessing" class="transcript-placeholder">
          Transcript will appear here after recording stops…
        </p>
        <p v-else-if="isProcessing" class="transcript-placeholder">Processing audio…</p>
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
.rec-status-text { font-size: 0.75rem; opacity: 0.65; }
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
.wbar.active { background: #0d9488; }
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
.transcript-text { font-size: 0.84rem; line-height: 1.7; margin: 0; opacity: 0.85; }
.processing-text { font-size: 0.78rem; opacity: 0.6; }
</style>