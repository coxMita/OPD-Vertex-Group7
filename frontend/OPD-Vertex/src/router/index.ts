import { createRouter, createWebHistory } from 'vue-router'

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
      component: () => import('../views/CalendarView.vue'),
    },
  ],
})

export default router