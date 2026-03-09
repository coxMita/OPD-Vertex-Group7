<script setup lang="ts">
import StepItem from './StepItem.vue'
import type { Step } from '@/composables/useLandingData'
defineProps<{ steps: Step[] }>()
</script>

<template>
  <section class="how-it-works">
    <v-container>
      <div class="text-center mb-12">
        <h2 class="section-title mb-3">How it works</h2>
        <p class="section-subtitle text-medium-emphasis">
          Four steps from booking to prescription
        </p>
      </div>
      <v-row>
        <v-col v-for="(s, i) in steps" :key="s.title" cols="12" md="3">
          <StepItem :index="i + 1" :title="s.title" :description="s.description" />
        </v-col>
      </v-row>
    </v-container>
  </section>
</template>

<style scoped>
.how-it-works {
  padding: 80px 0;
}
:root .how-it-works {
  background: #fafafa;
}
.v-theme--dark .how-it-works {
  background: #212121;
}
.section-title {
  font-size: 2.2rem;
  font-weight: 800;
}
.section-subtitle {
  font-size: 1.1rem;
}
</style>