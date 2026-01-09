<script setup>
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <AppSidebar />

    <!-- Main Content -->
    <div class="flex-1 flex flex-col ml-64">
      <AppHeader />
      <main class="flex-1 p-6 overflow-auto">
        <slot />
      </main>
    </div>
  </div>
</template>
