<script setup>
import { ref, onMounted, provide } from 'vue'
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'

const sidebarCollapsed = ref(false)

onMounted(() => {
  const saved = localStorage.getItem('sidebarCollapsed')
  if (saved !== null) {
    sidebarCollapsed.value = saved === 'true'
  }
})

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value)
}

provide('sidebarCollapsed', sidebarCollapsed)
provide('toggleSidebar', toggleSidebar)
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <AppSidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />

    <!-- Main Content -->
    <div class="flex-1 flex flex-col transition-all duration-300" :class="sidebarCollapsed ? 'ml-16' : 'ml-64'">
      <AppHeader :sidebarCollapsed="sidebarCollapsed" @toggleSidebar="toggleSidebar" />
      <main class="flex-1 p-6 overflow-auto">
        <slot />
      </main>
    </div>
  </div>
</template>
