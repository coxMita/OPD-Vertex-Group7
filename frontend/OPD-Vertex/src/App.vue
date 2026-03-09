<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from 'vuetify'

const vuetifyTheme = useTheme()

const titleColor = computed(() =>
  vuetifyTheme.current.value.dark ? '#29b6f6' : '#c0687a'
)

const toggleTheme = () => {
  vuetifyTheme.global.name.value = vuetifyTheme.current.value.dark ? 'light' : 'dark'
}
</script>

<template>
  <v-app>
    <v-app-bar elevation="0">
      <v-app-bar-title>
        <span class="font-weight-bold" :style="{ color: titleColor, fontSize: '2rem' }">OPD</span>
        <span :style="{ fontSize: '2rem' }">-Vertex</span>
      </v-app-bar-title>
      <v-btn
        :icon="vuetifyTheme.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
        slim
        @click="toggleTheme"
      />
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>