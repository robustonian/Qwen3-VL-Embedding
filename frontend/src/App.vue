<script setup>
import { onMounted } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import { useCollectionsStore } from '@/stores/collections'
import AppLayout from '@/components/layout/AppLayout.vue'

const documentsStore = useDocumentsStore()
const collectionsStore = useCollectionsStore()

onMounted(async () => {
  await Promise.all([
    documentsStore.fetchStats(),
    collectionsStore.fetchCollections()
  ])
})
</script>

<template>
  <AppLayout>
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </AppLayout>
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
