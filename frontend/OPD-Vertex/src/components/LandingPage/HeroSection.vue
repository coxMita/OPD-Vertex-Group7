<script setup lang="ts">
import { useTheme } from 'vuetify'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const theme = useTheme()
const cardColor = computed(() =>
  theme.current.value.dark ? '#121212' : '#fefdf5'
)
</script>

<template>
  <section class="hero">
    <v-container>
      <v-row align="center">
        <v-col cols="12" md="6">
          <v-chip color="primary" class="mb-4" variant="tonal">
            <v-icon start>mdi-shield-lock</v-icon>
            Privacy-Preserving AI
          </v-chip>

          <h1 class="hero-title mb-4">
            AI-powered clinical assistant for the
            <span class="text-primary">modern OPD</span>
          </h1>

          <p class="hero-subtitle mb-6 text-medium-emphasis">
            From patient booking to signed prescription — fully automated, fully local.
            No cloud. No data leaks. Just medicine.
          </p>

          <div class="d-flex flex-wrap ga-3 mb-8">
            <v-btn size="large" color="primary" rounded variant="flat" @click="router.push('/patient')">
              <v-icon start>mdi-account</v-icon>
              I'm a Patient
            </v-btn>
            <v-btn size="large" rounded variant="outlined" @click="router.push('/doctor')">
              <v-icon start>mdi-stethoscope</v-icon>
              I'm a Doctor
            </v-btn>
          </div>

          <div class="d-flex align-center ga-3 flex-wrap">
            <v-chip size="small" variant="tonal" color="primary">
              <v-icon start size="small">mdi-check</v-icon>
              Faster-Whisper
            </v-chip>
            <v-chip size="small" variant="tonal" color="cyan">
              <v-icon start size="small">mdi-check</v-icon>
              Llama 3.2 via Ollama
            </v-chip>
            <v-chip size="small" variant="tonal" color="indigo">
              <v-icon start size="small">mdi-check</v-icon>
              FastAPI + RabbitMQ
            </v-chip>
          </div>
        </v-col>

        <v-col cols="12" md="6">
          <v-card class="preview-card" elevation="8" rounded="xl" :color="cardColor">
            <v-card-text class="pa-6">
              <div class="d-flex align-center mb-4">
                <v-avatar color="primary" size="40" class="mr-3">
                  <v-icon color="white">mdi-microphone</v-icon>
                </v-avatar>
                <div>
                  <h3 class="text-h6 font-weight-bold">Live Consultation</h3>
                  <p class="text-caption text-medium-emphasis">Transcribing locally...</p>
                </div>
                <v-spacer />
                <v-chip color="success" size="small" variant="tonal">
                  <v-icon start size="small">mdi-circle</v-icon>
                  Live
                </v-chip>
              </div>

              <v-card color="grey-lighten-4" class="pa-4 mb-4" rounded="lg">
                <p class="text-body-2 mb-2" style="color: #888888 !important;">Transcript</p>
                <p class="text-body-2">
                  "Patient reports chronic cough for 3 weeks, no fever..."
                </p>
              </v-card>

              <v-card color="primary" class="pa-4 mb-4" rounded="lg" variant="tonal">
                <p class="text-body-2 font-weight-bold mb-2">
                  <v-icon start size="small">mdi-brain</v-icon>
                  AI Clinical Note
                </p>
                <p class="text-body-2">
                  Chief complaint: Chronic cough (3 weeks duration). Suggest: Chest X-Ray.
                </p>
              </v-card>

              <v-alert type="warning" variant="tonal" density="compact" rounded="lg">
                <v-icon start>mdi-lightbulb</v-icon>
                <strong>Suggestion:</strong> Chest X-Ray not yet mentioned — consider ordering.
              </v-alert>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </section>
</template>

<style scoped>
.hero {
  padding: 80px 0;
  min-height: 600px;
  display: flex;
  align-items: center;
}
.hero-title {
  font-size: 2.8rem;
  font-weight: 800;
  line-height: 1.2;
}
.hero-subtitle {
  font-size: 1.15rem;
  max-width: 90%;
}
.preview-card {
  border-radius: 16px;
  transition: transform 0.3s ease;
}
.preview-card:hover {
  transform: translateY(-6px);
}
:root .hero {
  background: linear-gradient(135deg, #fcf9ea 0%, #badfdb 50%, #ffa4a4 100%);
}
.v-theme--dark .hero {
  background: linear-gradient(135deg, #292b75 20%, #543076 50%, #4a7da1 100%);
}
</style>