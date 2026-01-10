<script setup>
import { onMounted } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import { useCollectionsStore } from '@/stores/collections'
import AppLayout from '@/components/layout/AppLayout.vue'
import ToastNotification from '@/components/ToastNotification.vue'

const documentsStore = useDocumentsStore()
const collectionsStore = useCollectionsStore()

onMounted(async () => {
  await Promise.all([
    documentsStore.fetchStats(),
    collectionsStore.fetchCollections()
  ])
})

// Keyboard shortcuts
const handleKeydown = (e) => {
  // Global search shortcut: / or Cmd+K
  if ((e.key === '/' && !e.ctrlKey && !e.metaKey) || (e.key === 'k' && (e.ctrlKey || e.metaKey))) {
    const activeElement = document.activeElement
    const isInput = activeElement?.tagName === 'INPUT' || activeElement?.tagName === 'TEXTAREA'
    if (!isInput) {
      e.preventDefault()
      // Dispatch custom event for search focus
      window.dispatchEvent(new CustomEvent('focus-search'))
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})
</script>

<template>
  <!-- Skip link for accessibility -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <AppLayout>
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </AppLayout>

  <!-- Global Toast Notifications -->
  <ToastNotification />
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
