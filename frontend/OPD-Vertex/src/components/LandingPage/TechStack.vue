<script setup lang="ts">
import ServiceProgress from './ServiceProgress.vue'
import type { Feature, Service } from '@/composables/useLandingData'
defineProps<{ benefits: Feature[]; services: Service[] }>()
</script>

<template>
  <section class="tech-stack">
    <v-container>
      <v-row align="center">
        <v-col cols="12" md="6">
          <h2 class="section-title mb-4">Built for privacy and scale</h2>
          <p class="text-h6 text-medium-emphasis mb-6">
            Loosely coupled microservices — swap any component without breaking the rest.
          </p>

          <v-list class="bg-transparent">
            <v-list-item v-for="b in benefits" :key="b.title" class="px-0 mb-3">
              <template #prepend>
                <v-avatar color="primary" size="36" class="mr-3">
                  <v-icon size="20" color="white">mdi-check</v-icon>
                </v-avatar>
              </template>
              <v-list-item-title class="font-weight-bold mb-1">{{ b.title }}</v-list-item-title>
              <v-list-item-subtitle class="text-medium-emphasis">
                {{ b.description }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-col>

        <v-col cols="12" md="6">
          <v-card class="tech-card" elevation="4" rounded="xl">
            <v-card-text class="pa-6">
              <h4 class="text-h6 font-weight-bold mb-4">
                <v-icon start color="primary">mdi-server</v-icon>
                System Services
              </h4>
              <ServiceProgress v-for="s in services" :key="s.name" v-bind="s" />
              <v-alert color="primary" variant="tonal" density="compact" class="mt-4" rounded="lg">
                <div class="d-flex align-center">
                  <v-icon size="small" class="mr-2">mdi-information</v-icon>
                  <span class="text-caption">
                    Docker · FastAPI · PostgreSQL · RabbitMQ · Ollama
                  </span>
                </div>
              </v-alert>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </section>
</template>

<style scoped>
.tech-stack {
  padding: 80px 0;
}
:root .tech-stack {
  background: #fff;
}
.v-theme--dark .tech-stack {
  background: #1a1a1a;
}
.tech-card {
  border-radius: 16px;
}
.section-title {
  font-size: 2.2rem;
  font-weight: 800;
}
</style>