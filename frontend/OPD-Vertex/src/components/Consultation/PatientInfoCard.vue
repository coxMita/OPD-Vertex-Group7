<script setup lang="ts">
import type { ConsultationPatient } from '@/composables/useConsultationData'

defineProps<{
  patient: ConsultationPatient
}>()

const infoFields = (p: ConsultationPatient) => [
  { label: 'DOB', value: p.dob },
  { label: 'Age', value: `${p.age} years` },
  { label: 'Gender', value: p.gender },
]
</script>

<template>
  <v-card rounded="lg" elevation="1" class="mb-4">
    <div class="patient-header px-5 pt-4 pb-3">
      <div class="d-flex align-center justify-space-between flex-wrap ga-2">
        <div>
          <h2 class="patient-name">{{ patient.name }}</h2>
          <div class="meta-row d-flex flex-wrap ga-4 mt-1">
            <span class="meta-item">
              <v-icon size="14" class="mr-1">mdi-phone</v-icon>{{ patient.phone }}
            </span>
            <span class="meta-item">
              <v-icon size="14" class="mr-1">mdi-email-outline</v-icon>{{ patient.email }}
            </span>
            <span class="meta-item">
              <v-icon size="14" class="mr-1">mdi-clock-outline</v-icon>{{ patient.time }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <v-divider />

    <div class="info-grid pa-5">
      <div class="section-label mb-3">
        <v-icon size="14" color="primary" class="mr-1">mdi-circle</v-icon>
        PATIENT INFORMATION
      </div>
      <div class="grid-cells">
        <div v-for="field in infoFields(patient)" :key="field.label" class="info-cell">
          <p class="cell-label">{{ field.label }}</p>
          <p class="cell-value">{{ field.value }}</p>
        </div>
      </div>
      <div class="reason-row mt-3" v-if="patient.reason">
        <p class="cell-label">Reason for Visit</p>
        <p class="cell-value reason-text">{{ patient.reason }}</p>
      </div>
    </div>
  </v-card>
</template>

<style scoped>
.patient-name {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.meta-item {
  font-size: 0.78rem;
  opacity: 0.65;
  display: flex;
  align-items: center;
}
.section-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  opacity: 0.5;
  display: flex;
  align-items: center;
}
.grid-cells {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px 16px;
}
.cell-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.45;
  margin: 0 0 2px;
}
.cell-value {
  font-size: 0.88rem;
  font-weight: 600;
  margin: 0;
}
.reason-text {
  font-style: italic;
  font-weight: 400;
  opacity: 0.8;
}
</style>