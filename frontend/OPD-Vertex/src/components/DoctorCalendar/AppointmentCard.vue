<script setup lang="ts">
defineProps<{
  statusIcon: string
  assignedTime: string | null | undefined
  patientId: string
  timePreference?: string
  statusLabel?: string
  apptStyle: Record<string, string>
  compact?: boolean
  pill?: boolean
}>()
</script>

<template>
  <!-- Month pill -->
  <div v-if="pill" class="month-appt-card" :style="apptStyle">
    <v-icon size="9" style="color: currentColor; flex-shrink: 0">{{ statusIcon }}</v-icon>
    <span class="month-appt-time">{{ assignedTime ?? '' }}</span>
    <span class="month-appt-name">P#{{ patientId }}</span>
  </div>

  <!-- Week compact -->
  <div v-else-if="compact" class="appt-card appt-card--compact" :style="apptStyle">
    <v-icon size="10" style="color: currentColor; flex-shrink: 0">{{ statusIcon }}</v-icon>
    <span class="appt-time ml-1">{{ assignedTime }}</span>
    <div class="appt-name">P#{{ patientId }}</div>
  </div>

  <!-- Day full -->
  <div v-else class="appt-card" :style="apptStyle">
    <div class="appt-header-row">
      <v-icon size="12" style="color: currentColor">{{ statusIcon }}</v-icon>
      <span class="appt-time">{{ assignedTime }}</span>
    </div>
    <div class="appt-name">Patient #{{ patientId }}</div>
    <div class="appt-type">{{ timePreference }} · {{ statusLabel }}</div>
  </div>
</template>

<style scoped>
.appt-card {
  border-radius: 6px;
  padding: 7px 10px;
  border-left: 3px solid transparent;
  margin-bottom: 3px;
  cursor: pointer;
  transition: filter 0.15s ease, transform 0.1s ease;
}
.appt-card:hover {
  filter: brightness(0.93);
  transform: translateX(1px);
}
.appt-card--compact {
  padding: 4px 6px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
}
.appt-header-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}
.appt-time {
  font-size: 0.68rem;
  font-weight: 700;
  opacity: 0.85;
}
.appt-name {
  font-size: 0.82rem;
  font-weight: 600;
  width: 100%;
}
.appt-type {
  font-size: 0.67rem;
  opacity: 0.68;
  margin-top: 1px;
}
.month-appt-card {
  border-radius: 4px;
  padding: 2px 5px;
  border-left: 3px solid transparent;
  display: flex;
  align-items: center;
  gap: 3px;
  overflow: hidden;
  cursor: pointer;
  transition: filter 0.15s ease;
}
.month-appt-card:hover {
  filter: brightness(0.93);
}
.month-appt-time {
  font-size: 0.65rem;
  font-weight: 700;
  opacity: 0.8;
  flex-shrink: 0;
}
.month-appt-name {
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>