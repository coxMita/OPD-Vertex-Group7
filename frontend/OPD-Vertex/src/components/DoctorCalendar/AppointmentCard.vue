<script setup lang="ts">
const props = defineProps<{
  statusIcon: string
  assignedTime: string | null | undefined
  patientId: string
  patientName?: string | null
  appointmentId: string
  timePreference?: string
  statusLabel?: string
  apptStyle: Record<string, string>
  compact?: boolean
  pill?: boolean
  editMode?: boolean
  isDragging?: boolean
}>()

const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'dragstart', id: string): void
}>()

function displayName(full: boolean): string {
  if (props.patientName) {
    // In compact/pill mode show shortened name, in full mode show full name
    if (!full) {
      const parts = props.patientName.split(' ')
      return parts.length >= 2 ? `${parts[0]} ${parts[1]!.charAt(0)}.` : props.patientName
    }
    return props.patientName
  }
  return full ? `Patient #${props.patientId.slice(0, 8)}` : `P#${props.patientId.slice(0, 8)}`
}
</script>

<template>
  <!-- Month pill -->
  <div
    v-if="pill"
    class="month-appt-card"
    :style="apptStyle"
    :class="{ 'is-dragging': isDragging, 'edit-mode': editMode }"
    :draggable="editMode"
    @dragstart.stop="emit('dragstart', appointmentId)"
    @click.stop="emit('select', appointmentId)"
  >
    <v-icon size="9" style="color: currentColor; flex-shrink: 0">{{ statusIcon }}</v-icon>
    <span class="month-appt-time">{{ assignedTime ?? '' }}</span>
    <span class="month-appt-name">{{ displayName(false) }}</span>
  </div>

  <!-- Week compact -->
  <div
    v-else-if="compact"
    class="appt-card appt-card--compact"
    :style="apptStyle"
    :class="{ 'is-dragging': isDragging, 'edit-mode': editMode }"
    :draggable="editMode"
    @dragstart.stop="emit('dragstart', appointmentId)"
    @click.stop="emit('select', appointmentId)"
  >
    <v-icon size="10" style="color: currentColor; flex-shrink: 0">{{ statusIcon }}</v-icon>
    <span class="appt-time ml-1">{{ assignedTime }}</span>
    <div class="appt-name">{{ displayName(false) }}</div>
    <v-icon v-if="editMode" size="10" class="drag-handle">mdi-drag</v-icon>
  </div>

  <!-- Day full -->
  <div
    v-else
    class="appt-card"
    :style="apptStyle"
    :class="{ 'is-dragging': isDragging, 'edit-mode': editMode }"
    :draggable="editMode"
    @dragstart.stop="emit('dragstart', appointmentId)"
    @click.stop="emit('select', appointmentId)"
  >
    <div class="appt-header-row">
      <v-icon size="12" style="color: currentColor">{{ statusIcon }}</v-icon>
      <span class="appt-time">{{ assignedTime }}</span>
      <v-icon v-if="editMode" size="12" class="drag-handle ml-auto">mdi-drag</v-icon>
    </div>
    <div class="appt-name">{{ displayName(true) }}</div>
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
  transition: filter 0.15s ease, transform 0.1s ease, opacity 0.15s ease;
}
.appt-card:hover {
  filter: brightness(0.93);
  transform: translateX(1px);
}
.appt-card.edit-mode {
  cursor: grab;
}
.appt-card.edit-mode:active {
  cursor: grabbing;
}
.appt-card.is-dragging {
  opacity: 0.4;
  transform: scale(0.97);
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
.drag-handle {
  opacity: 0.5;
  flex-shrink: 0;
}

/* Month pill */
.month-appt-card {
  border-radius: 4px;
  padding: 2px 5px;
  border-left: 3px solid transparent;
  display: flex;
  align-items: center;
  gap: 3px;
  overflow: hidden;
  cursor: pointer;
  transition: filter 0.15s ease, opacity 0.15s ease;
}
.month-appt-card:hover {
  filter: brightness(0.93);
}
.month-appt-card.edit-mode {
  cursor: grab;
}
.month-appt-card.is-dragging {
  opacity: 0.4;
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