<script setup lang="ts"></script>

<template>
  <footer class="footer">
    <v-container>
      <v-row>
        <v-col cols="12" md="4">
          <div class="d-flex align-center mb-3">
            <v-avatar color="primary" size="32" class="mr-2">
              <v-icon size="18" color="white">mdi-hospital-box</v-icon>
            </v-avatar>
            <span class="text-h6 font-weight-bold">OPD-Vertex</span>
          </div>
          <p class="text-medium-emphasis">
            A privacy-preserving AI clinical assistant for outpatient departments.
          </p>
        </v-col>

        <v-col cols="6" md="2">
          <h4 class="font-weight-bold mb-3">Product</h4>
          <div class="footer-links">
            <a href="#">Features</a>
            <a href="#">How it works</a>
            <a href="#">Technology</a>
          </div>
        </v-col>

        <v-col cols="6" md="2">
          <h4 class="font-weight-bold mb-3">Project</h4>
          <div class="footer-links">
            <a href="#">About</a>
            <a href="#">Documentation</a>
            <a href="#">GitHub</a>
          </div>
        </v-col>

        <v-col cols="12" md="4">
          <h4 class="font-weight-bold mb-3">Tech Stack</h4>
          <div class="d-flex flex-wrap ga-2">
            <v-chip size="small" variant="tonal" color="teal">Faster-Whisper</v-chip>
            <v-chip size="small" variant="tonal" color="cyan">Llama 3.2</v-chip>
            <v-chip size="small" variant="tonal" color="indigo">Ollama</v-chip>
            <v-chip size="small" variant="tonal" color="blue">FastAPI</v-chip>
            <v-chip size="small" variant="tonal" color="green">RabbitMQ</v-chip>
            <v-chip size="small" variant="tonal" color="purple">PostgreSQL</v-chip>
          </div>
        </v-col>
      </v-row>

      <v-divider class="my-6" />
      <div class="text-center text-medium-emphasis">
        <p>&copy; 2025 OPD-Vertex — SDU Group 7</p>
      </div>
    </v-container>
  </footer>
</template>

<style scoped>
.footer {
  padding: 60px 0 20px;
}
:root .footer {
  background: #ffdada ;
}
.v-theme--dark .footer {
  background: #212121;
}
.footer-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.footer a {
  text-decoration: none;
  transition: color 0.2s;
}
</style>