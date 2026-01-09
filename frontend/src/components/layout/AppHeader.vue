<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchStore } from '@/stores/search'

const router = useRouter()
const searchStore = useSearchStore()

const quickSearchQuery = ref('')
const showQuickSearch = ref(false)

const handleQuickSearch = () => {
  if (quickSearchQuery.value.trim()) {
    searchStore.searchByText(quickSearchQuery.value)
    router.push('/')
    showQuickSearch.value = false
    quickSearchQuery.value = ''
  }
}

// Keyboard shortcut (Cmd+K / Ctrl+K)
const handleKeydown = (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    showQuickSearch.value = !showQuickSearch.value
  }
  if (e.key === 'Escape') {
    showQuickSearch.value = false
  }
}

// Register global keyboard listener
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleKeydown)
}
</script>

<template>
  <header class="h-14 bg-bg-secondary border-b border-border flex items-center justify-between px-6">
    <!-- Page Title -->
    <div class="flex items-center gap-4">
      <h2 class="text-lg font-medium text-text-primary">
        <slot name="title">Dashboard</slot>
      </h2>
    </div>

    <!-- Quick Search -->
    <div class="flex items-center gap-4">
      <button
        @click="showQuickSearch = true"
        class="flex items-center gap-2 px-3 py-1.5 bg-bg-tertiary border border-border rounded-lg text-sm text-text-muted hover:border-border-hover transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <span>クイック検索</span>
        <kbd class="px-1.5 py-0.5 text-xs bg-bg-primary rounded border border-border">⌘K</kbd>
      </button>
    </div>

    <!-- Quick Search Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showQuickSearch"
          class="fixed inset-0 bg-black/50 flex items-start justify-center pt-24 z-50"
          @click.self="showQuickSearch = false"
        >
          <div class="w-full max-w-lg bg-bg-secondary border border-border rounded-xl shadow-2xl overflow-hidden">
            <div class="flex items-center gap-3 p-4 border-b border-border">
              <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                v-model="quickSearchQuery"
                type="text"
                placeholder="検索キーワードを入力..."
                class="flex-1 bg-transparent text-text-primary placeholder-text-muted outline-none"
                @keydown.enter="handleQuickSearch"
                autofocus
              />
              <kbd class="px-2 py-1 text-xs bg-bg-tertiary rounded border border-border text-text-muted">ESC</kbd>
            </div>
            <div class="p-3 text-sm text-text-muted">
              Enterで検索、ESCで閉じる
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </header>
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
