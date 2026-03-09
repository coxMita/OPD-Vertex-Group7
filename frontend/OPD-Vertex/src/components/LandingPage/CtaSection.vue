<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>


<template>
  <section class="cta">
    <v-container class="text-center">
      <h2 class="section-title mb-4">Ready to transform your clinic?</h2>
      <p class="text-h6 text-medium-emphasis mb-6">
        Deploy a fully local, AI-powered OPD system in minutes
      </p>
      <v-btn size="x-large" color="primary" rounded elevation="4">
        Get Started Now
        <v-icon end>mdi-arrow-right</v-icon>
      </v-btn>
    </v-container>
  </section>
</template>

<style scoped>
.cta {
  padding: 80px 0;
}
:root .cta {
  background: #fefdf5;
}
.v-theme--dark .cta {
  background: #1a1a1a;
}
.section-title {
  font-size: 2.5rem;
  font-weight: 800;
}
</style>