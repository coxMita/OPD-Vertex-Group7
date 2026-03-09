import { ref } from 'vue'

export type Feature = { icon: string; color: string; title: string; description: string }
export type Step = { title: string; description: string }
export type Stat = { value: string; label: string }
export type Service = { name: string; value: number; status: 'Active' | 'Degraded' | 'Down' }

export function useLandingData() {
  const features = ref<Feature[]>([
    {
      icon: 'mdi-calendar-clock',
      color: 'teal',
      title: 'Appointment Portal',
      description: 'Intelligent patient queue management with priority scheduling and real-time status updates.',
    },
    {
      icon: 'mdi-microphone',
      color: 'cyan',
      title: 'Privacy-First Transcription',
      description: 'Real-time speech-to-text via Faster-Whisper — fully local, zero data ever leaves the clinic.',
    },
    {
      icon: 'mdi-brain',
      color: 'indigo',
      title: 'AI Summarization',
      description: 'Local LLM converts consultation dialogue into structured clinical notes and OPD prescriptions.',
    },
    {
      icon: 'mdi-shield-check',
      color: 'green',
      title: 'Suggestive Mode',
      description: 'AI flags potential omissions and standard-of-care suggestions to assist doctors in real time.',
    },
    {
      icon: 'mdi-file-sign',
      color: 'blue',
      title: 'Verified Prescriptions',
      description: 'Doctors review, edit and approve AI-generated prescriptions before secure email delivery.',
    },
    {
      icon: 'mdi-lock-outline',
      color: 'purple',
      title: 'Fully Local AI',
      description: 'All models run on-premise via Ollama. No cloud, no third-party APIs, no data leaks.',
    },
  ])

  const steps = ref<Step[]>([
    {
      title: 'Patient Books Appointment',
      description: 'Patient schedules a visit. Data is stored in the priority queue.',
    },
    {
      title: 'Doctor Starts Consultation',
      description: 'Faster-Whisper records and transcribes the session locally in real time.',
    },
    {
      title: 'AI Processes Transcript',
      description: 'Local LLM generates a structured clinical note and OPD prescription draft.',
    },
    {
      title: 'Doctor Reviews & Approves',
      description: 'Doctor edits if needed, approves, and a PDF is emailed instantly to the patient.',
    },
  ])

  const stats = ref<Stat[]>([
    { value: '100%', label: 'Local & Private' },
    { value: '0ms', label: 'Cloud Latency' },
    { value: 'Open', label: 'Source Models Only' },
  ])

  const benefits = ref<Feature[]>([
    {
      title: 'Microservices Architecture',
      description: 'Loosely coupled components — swap any model or service without touching the rest.',
      icon: 'mdi-check',
      color: 'success',
    },
    {
      title: 'Event-Driven with RabbitMQ',
      description: 'Async messaging between transcription, AI, and prescription services.',
      icon: 'mdi-check',
      color: 'success',
    },
    {
      title: 'Local AI via Ollama',
      description: 'Llama 3.2 and Faster-Whisper run entirely on the clinic\'s hardware.',
      icon: 'mdi-check',
      color: 'success',
    },
    {
      title: 'Containerized Deployment',
      description: 'Docker Compose orchestrates all 14 services consistently across environments.',
      icon: 'mdi-check',
      color: 'success',
    },
  ])

  const services = ref<Service[]>([
    { name: 'Transcription Service', value: 100, status: 'Active' },
    { name: 'AI Service', value: 100, status: 'Active' },
    { name: 'User Service', value: 100, status: 'Active' },
    { name: 'Consultation Service', value: 100, status: 'Active' },
    { name: 'Appointment Service', value: 100, status: 'Active' },
    { name: 'Prescription Engine', value: 100, status: 'Active' },
    { name: 'Email Delivery', value: 100, status: 'Active' },
  ])

  return { features, steps, stats, benefits, services }
}