// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)

const vuetify = createVuetify({
  components,
  directives,
  icons: { defaultSet: 'mdi', aliases, sets: { mdi } },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#c0687a',
          'on-primary': '#5a2a2a',
          secondary: '#fefdf5',
          'on-secondary': '#5a2a2a',
        },
      },
    },
  },
})

app.use(vuetify)
app.use(router)

const authStore = useAuthStore()
authStore.init().then(() => {
  app.mount('#app')
})