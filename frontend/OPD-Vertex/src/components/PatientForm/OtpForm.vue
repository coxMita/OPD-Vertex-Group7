<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  email: string
  cardColor: string
  tealColor: string
  verifying?: boolean
  resending?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  (e: 'verify', code: string): void
  (e: 'resend'): void
}>()

const code = ref('')

function submit() {
  if (code.value.length === 6) {
    emit('verify', code.value)
  }
}

function onFinish(val: string) {
  code.value = val
  emit('verify', val)
}
</script>

<template>
  <v-card rounded="xl" elevation="2" :color="cardColor" class="pa-8">
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar :color="tealColor" size="40">
        <v-icon color="white" size="20">mdi-shield-key-outline</v-icon>
      </v-avatar>
      <div>
        <h2 class="text-h6 font-weight-bold">Verify Your Email</h2>
        <p class="text-medium-emphasis text-caption">
          We sent a 6-digit code to <strong>{{ email }}</strong>
        </p>
      </div>
    </div>

    <v-otp-input
      v-model="code"
      :length="6"
      variant="outlined"
      class="mb-2"
      @finish="onFinish"
    />

    <v-btn
      :color="tealColor"
      :loading="verifying"
      :disabled="code.length !== 6 || verifying"
      size="x-large"
      rounded="lg"
      block
      elevation="0"
      class="mt-4"
      @click="submit"
    >
      <span class="font-weight-bold" style="color: white">Confirm Code</span>
      <v-icon end color="white">mdi-arrow-right</v-icon>
    </v-btn>

    <v-btn
      variant="text"
      :loading="resending"
      :disabled="verifying"
      block
      class="mt-2"
      @click="emit('resend')"
    >
      <v-icon start size="16">mdi-refresh</v-icon>
      Resend code
    </v-btn>

    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      rounded="lg"
      class="mt-4"
    >
      {{ error }}
    </v-alert>
  </v-card>
</template>
