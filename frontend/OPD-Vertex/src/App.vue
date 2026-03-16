<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from './stores/auth'
import PatientPortal from './components/PatientPortal.vue'
import DoctorDashboard from './components/DoctorDashboard.vue'
import './assets/peer-styles.css'

const authStore = useAuthStore()
const activeView = ref('patient')

const switchView = (view: string) => {
  activeView.value = view
}
</script>

<template>
  <div v-if="!authStore.isAuthenticated" class="login-wrapper">
    <div class="login-card">
      <div class="logo"><div class="logo-dot"></div>OPD-Vertex</div>
      <h1>Welcome to OPD-Vertex</h1>
      <p>Please log in to access the Patient Portal and Doctor Dashboard.</p>
      <button @click="authStore.login()" class="btn-login-big">Login with Keycloak</button>
    </div>
  </div>

  <template v-else>
    <nav class="top-nav">
      <div class="logo"><div class="logo-dot"></div>OPD-Vertex</div>
      <div class="nav-tabs">
        <button 
          class="nav-tab" 
          :class="{ active: activeView === 'patient' }" 
          @click="switchView('patient')"
        >
          Patient Portal
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: activeView === 'doctor' }" 
          @click="switchView('doctor')"
        >
          Doctor Dashboard
        </button>
      </div>
      <div class="user-control">
        <span class="welcome-text">Hi, {{ authStore.userProfile?.firstName || 'User' }}</span>
        <button @click="authStore.logout()" class="btn-mini-logout">Logout</button>
      </div>
    </nav>

    <PatientPortal v-if="activeView === 'patient'" />
    <DoctorDashboard v-if="activeView === 'doctor'" />
  </template>
</template>

<style>
/* Additional integration styles */
.login-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #0f1e38 0%, #1a3a6c 100%);
}

.login-card {
  background: white;
  padding: 40px;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
  max-width: 400px;
  width: 90%;
}

.login-card .logo {
  justify-content: center;
  color: var(--navy);
  margin-bottom: 20px;
  font-size: 1.8rem;
}

.login-card h1 {
  font-size: 1.5rem;
  margin-bottom: 15px;
  color: #2d3748;
}

.login-card p {
  color: #718096;
  margin-bottom: 30px;
  line-height: 1.5;
}

.btn-login-big {
  width: 100%;
  padding: 14px;
  background: var(--blue);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-login-big:hover {
  background: #2b6cb0;
}

.user-control {
  margin-left: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.welcome-text {
  color: rgba(255,255,255,0.8);
  font-size: 0.85rem;
  font-weight: 500;
}

.btn-mini-logout {
  padding: 4px 12px;
  background: rgba(255,255,255,0.1);
  color: white;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
}

.btn-mini-logout:hover {
  background: rgba(255,b255,255,0.2);
}
</style>
