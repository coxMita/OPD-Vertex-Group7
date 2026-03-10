<script setup lang="ts">
import FeatureCard from './FeatureCard.vue'
import type { Feature } from '@/composables/useLandingData'
defineProps<{ features: Feature[] }>()
</script>

<template>
  <section class="features">
    <v-container>
      <div class="text-center mb-12">
        <h2 class="section-title mb-3">Everything you need for modern OPD management</h2>
        <p class="section-subtitle text-medium-emphasis">Powered by local AI and open-source models</p>
      </div>
      <v-row>
        <v-col v-for="f in features" :key="f.title" cols="12" md="4" class="mb-4">
          <FeatureCard v-bind="f" />
        </v-col>
      </v-row>
    </v-container>
  </section>
</template>

<style scoped>
.features {
  padding: 80px 0;
}
:root .features {
  background: #fefdf5;
}
.v-theme--dark .features {
  background: #1a1a1a;
}
.section-title {
  font-size: 2.2rem;
  font-weight: 800;
}
.section-subtitle {
  font-size: 1.1rem;
}
</style>