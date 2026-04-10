<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'

const vuetifyTheme = useTheme()
const authStore = useAuthStore()

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

      <!-- Profil utilizator autentificat -->
      <template v-if="authStore.authenticated">
        <v-chip color="primary" variant="tonal" size="small" class="mr-2">
          <v-icon start size="14">mdi-account</v-icon>
          {{ authStore.userProfile?.firstName ?? authStore.userProfile?.username }}
        </v-chip>
        <v-chip
          v-if="authStore.isDoctor"
          color="teal"
          variant="tonal"
          size="small"
          class="mr-3"
        >
          Doctor
        </v-chip>
        <v-btn
          variant="tonal"
          color="error"
          size="small"
          class="mr-2"
          @click="authStore.logout"
        >
          <v-icon start size="14">mdi-logout</v-icon>
          Logout
        </v-btn>
      </template>

      <!-- Buton login dacă nu e autentificat -->
      <template v-else>
        <v-btn
          variant="tonal"
          color="primary"
          size="small"
          class="mr-2"
          @click="authStore.login"
        >
          <v-icon start size="14">mdi-login</v-icon>
          Doctor Login
        </v-btn>
      </template>

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