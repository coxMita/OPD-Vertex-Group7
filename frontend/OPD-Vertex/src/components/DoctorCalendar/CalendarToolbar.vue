<script setup lang="ts">
import type { CalendarView } from '@/composables/useCalendarNavigation'

defineProps<{
  currentDateDisplay: string
  currentView: CalendarView
  editMode: boolean
}>()

const emit = defineEmits<{
  (e: 'navigate', direction: number): void
  (e: 'go-to-today'): void
  (e: 'update:currentView', view: CalendarView): void
  (e: 'toggle-edit-mode'): void
}>()
</script>

<template>
  <div class="calendar-toolbar">
    <div class="toolbar-left">
      <div class="date-nav">
        <v-btn icon variant="outlined" size="small" @click="emit('navigate', -1)">
          <v-icon>mdi-chevron-left</v-icon>
        </v-btn>
        <v-btn icon variant="outlined" size="small" @click="emit('navigate', 1)">
          <v-icon>mdi-chevron-right</v-icon>
        </v-btn>
        <span class="current-date">{{ currentDateDisplay }}</span>
      </div>
      <v-btn variant="tonal" color="primary" size="small" @click="emit('go-to-today')">
        Today
      </v-btn>
    </div>

    <div class="toolbar-right">
      <!-- Edit Mode toggle -->
      <v-btn
        :color="editMode ? 'warning' : 'default'"
        :variant="editMode ? 'flat' : 'outlined'"
        size="small"
        :prepend-icon="editMode ? 'mdi-pencil-off' : 'mdi-pencil'"
        @click="emit('toggle-edit-mode')"
      >
        {{ editMode ? 'Done Editing' : 'Edit' }}
        <v-tooltip activator="parent" location="bottom">
          {{ editMode ? 'Exit edit mode' : 'Enable drag & drop to reschedule appointments' }}
        </v-tooltip>
      </v-btn>

      <v-btn-toggle
        :model-value="currentView"
        mandatory
        variant="outlined"
        density="compact"
        divided
        @update:model-value="emit('update:currentView', $event)"
      >
        <v-btn value="day" size="small">Day</v-btn>
        <v-btn value="week" size="small">Week</v-btn>
        <v-btn value="month" size="small">Month</v-btn>
      </v-btn-toggle>
    </div>
  </div>
</template>

<style scoped>
.calendar-toolbar {
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
  transition: background 0.2s ease;
}
.calendar-toolbar.edit-active {
  background: rgba(var(--v-theme-warning), 0.04);
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.date-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}
.current-date {
  font-family: 'DM Serif Display', serif;
  font-size: 1.15rem;
  color: rgb(var(--v-theme-on-surface));
  min-width: 240px;
}
.toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
</style>