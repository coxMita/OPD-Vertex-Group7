import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'landing-page',
      component: () => import('../views/LandingPageView.vue'),
    },
    {
      path: '/patient',
      name: 'patient',
      component: () => import('../views/PatientFormView.vue'),
    },
    {
      path: '/doctor',
      name: 'doctor-calendar',
      component: () => import('../views/DoctorCalendarView.vue'),
      meta: { requiresAuth: true, roles: ['doctor'] },
    },
  ],
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true

  const authStore = useAuthStore()

  // Așteaptă ca init() să termine — init() returnează același promise dacă rulează deja
  await authStore.init()

  if (!authStore.authenticated) {
    await authStore.login()
    return false
  }

  const requiredRoles = to.meta.roles as string[] | undefined
  if (requiredRoles?.length) {
    const hasRole = requiredRoles.some((r) => authStore.roles.includes(r))
    if (!hasRole) {
      return { name: 'landing-page' }
    }
  }

  return true
})

export default router