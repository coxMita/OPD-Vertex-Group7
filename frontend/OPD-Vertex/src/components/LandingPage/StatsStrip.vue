<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import type { Stat } from '@/composables/useLandingData'

defineProps<{ stats: Stat[] }>()

const vuetifyTheme = useTheme()
const statColor = computed(() =>
  vuetifyTheme.current.value.dark ? '#29b6f6' : '#c0687a'
)
</script>

<template>
  <section class="stats">
    <v-container>
      <v-row class="text-center">
        <v-col v-for="s in stats" :key="s.label" cols="12" md="4">
          <h2 class="stat-value mb-2" :style="{ color: statColor, fontSize: '3rem' }">{{ s.value }}</h2>
          <p class="stat-label text-medium-emphasis">{{ s.label }}</p>
        </v-col>
      </v-row>
    </v-container>
  </section>
</template>

<style scoped>
.stats {
  padding: 80px 0;
}
:root .stats {
  background: linear-gradient(135deg, #fcf9ea 0%, #badfdb 50%, #ffa4a4 100%);
}
.v-theme--dark .stats {
  background: linear-gradient(135deg, #292b75 20%, #543076 50%, #4a7da1 100%);
}
.stat-label {
  font-size: 1.1rem;
}
</style>