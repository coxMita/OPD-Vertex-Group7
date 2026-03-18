# Consultation View — Drop-in files for OPD-Vertex

## File placement

Copy every file from this package into your Vue project at `frontend/OPD-Vertex/`:

```
src/
├── composables/
│   └── useConsultationData.ts          ← NEW (mock appointment + rx data)
│
├── components/
│   └── Consultation/                   ← NEW FOLDER
│       ├── AppointmentSidebar.vue      ← Left panel — appointment list
│       ├── PatientInfoCard.vue         ← Patient demographics card
│       ├── RecordingCard.vue           ← Start/stop recording + waveform
│       ├── TranscriptionUploadCard.vue ← WAV file upload → POST to gateway
│       └── PrescriptionCard.vue        ← AI-draft prescription editor
│
├── views/
│   └── ConsultationView.vue            ← NEW main view
│
└── router/
    └── index.ts                        ← UPDATED — adds /doctor route
```

## Changes needed in existing files

### `src/components/LandingPage/HeroSection.vue`
The "I'm a Doctor" button already calls `router.push('/doctor')` — no change needed.
The new route `/doctor` will now render `ConsultationView`.

## Transcription endpoint
`TranscriptionUploadCard.vue` sends `POST http://localhost:8000/api/transcription/transcribe`
with `multipart/form-data` (field name: `file`).

Change `TRANSCRIPTION_ENDPOINT` in that component once your gateway prefix is confirmed.
Expected response shape: `{ "text": "..." }` or `{ "transcript": "..." }`.