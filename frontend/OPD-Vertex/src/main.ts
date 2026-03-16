import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { useAuthStore } from './stores/auth'

import App from './App.vue'
import router from './router'

const initApp = async () => {
    const app = createApp(App)
    const pinia = createPinia()

    app.use(pinia)
    app.use(router)

    const authStore = useAuthStore()
    await authStore.init()

    app.mount('#app')
}

initApp()
