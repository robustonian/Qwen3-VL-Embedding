<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchStore } from '@/stores/search'

const router = useRouter()
const searchStore = useSearchStore()

const quickSearchQuery = ref('')
const showQuickSearch = ref(false)
const searchInput = ref(null)

const handleQuickSearch = () => {
  if (quickSearchQuery.value.trim()) {
    searchStore.searchByText(quickSearchQuery.value)
    router.push('/')
    showQuickSearch.value = false
    quickSearchQuery.value = ''
  }
}

const openQuickSearch = () => {
  showQuickSearch.value = true
  // Focus input after modal opens
  setTimeout(() => {
    searchInput.value?.focus()
  }, 100)
}

const closeQuickSearch = () => {
  showQuickSearch.value = false
  quickSearchQuery.value = ''
}

// Keyboard shortcut (Cmd+K / Ctrl+K)
const handleKeydown = (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    if (showQuickSearch.value) {
      closeQuickSearch()
    } else {
      openQuickSearch()
    }
  }
  if (e.key === 'Escape' && showQuickSearch.value) {
    closeQuickSearch()
  }
}

// Listen for global focus-search event
const handleFocusSearch = () => {
  openQuickSearch()
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('focus-search', handleFocusSearch)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('focus-search', handleFocusSearch)
})
</script>

<template>
  <header class="h-14 bg-bg-secondary/80 backdrop-blur-xl border-b border-border/50 flex items-center justify-between px-6 sticky top-0 z-30">
    <!-- Page Title -->
    <div class="flex items-center gap-4">
      <h2 class="text-lg font-display font-semibold text-text-primary">
        <slot name="title">Dashboard</slot>
      </h2>
    </div>

    <!-- Quick Search Button -->
    <div class="flex items-center gap-4">
      <button
        @click="openQuickSearch"
        class="group flex items-center gap-3 px-4 py-2 bg-bg-tertiary/50 border border-border/50 rounded-xl text-sm text-text-muted
               hover:bg-bg-tertiary hover:border-accent/30 hover:text-text-secondary
               focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-secondary
               transition-all duration-200"
      >
        <svg class="w-4 h-4 group-hover:text-accent transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <span class="hidden sm:inline">クイック検索</span>
        <div class="hidden sm:flex items-center gap-1">
          <kbd class="px-1.5 py-0.5 text-[10px] font-mono bg-bg-primary/50 rounded border border-border/50 text-text-muted">⌘</kbd>
          <kbd class="px-1.5 py-0.5 text-[10px] font-mono bg-bg-primary/50 rounded border border-border/50 text-text-muted">K</kbd>
        </div>
      </button>
    </div>

    <!-- Quick Search Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showQuickSearch"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-start justify-center pt-[15vh] z-50 p-4"
          @click.self="closeQuickSearch"
        >
          <div class="modal-content w-full max-w-xl">
            <!-- Search box with glow effect -->
            <div class="relative">
              <!-- Glow background -->
              <div class="absolute -inset-0.5 bg-gradient-to-r from-accent/30 via-accent/10 to-accent/30 rounded-2xl blur-lg opacity-50"></div>

              <!-- Main container -->
              <div class="relative bg-bg-secondary border border-border/50 rounded-2xl shadow-2xl overflow-hidden">
                <!-- Search input row -->
                <div class="flex items-center gap-3 p-4 border-b border-border/50">
                  <div class="flex-shrink-0 w-8 h-8 rounded-xl bg-accent/10 flex items-center justify-center">
                    <svg class="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <input
                    ref="searchInput"
                    v-model="quickSearchQuery"
                    type="text"
                    placeholder="検索キーワードを入力..."
                    class="flex-1 bg-transparent text-text-primary text-lg placeholder-text-muted/60 outline-none"
                    @keydown.enter="handleQuickSearch"
                    @keydown.esc="closeQuickSearch"
                  />
                  <button
                    @click="closeQuickSearch"
                    class="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-tertiary transition-colors"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <!-- Hints -->
                <div class="flex items-center justify-between px-4 py-3 bg-bg-tertiary/30">
                  <div class="flex items-center gap-4 text-xs text-text-muted">
                    <span class="flex items-center gap-1.5">
                      <kbd class="px-1.5 py-0.5 bg-bg-tertiary rounded border border-border/50 font-mono">Enter</kbd>
                      で検索
                    </span>
                    <span class="flex items-center gap-1.5">
                      <kbd class="px-1.5 py-0.5 bg-bg-tertiary rounded border border-border/50 font-mono">ESC</kbd>
                      で閉じる
                    </span>
                  </div>
                  <span class="text-xs text-text-muted">
                    テキストで類似画像を検索
                  </span>
                </div>

                <!-- Recent searches -->
                <div v-if="searchStore.recentSearches.length > 0" class="p-2 border-t border-border/30">
                  <p class="text-[10px] uppercase tracking-wider text-text-muted px-2 py-1">最近の検索</p>
                  <div class="space-y-0.5">
                    <button
                      v-for="search in searchStore.recentSearches.slice(0, 3)"
                      :key="search.id"
                      @click="quickSearchQuery = search.query_text || ''; handleQuickSearch()"
                      class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-text-secondary hover:bg-bg-tertiary hover:text-text-primary transition-colors text-left"
                    >
                      <svg class="w-4 h-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span class="truncate">{{ search.query_text || '画像検索' }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </header>
</template>

<style scoped>
.modal-enter-active {
  transition: opacity 0.2s ease-out;
}

.modal-leave-active {
  transition: opacity 0.15s ease-in;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease-out;
}

.modal-leave-active .modal-content {
  transition: transform 0.15s ease-in, opacity 0.15s ease-in;
}

.modal-enter-from .modal-content {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

.modal-leave-to .modal-content {
  opacity: 0;
  transform: scale(0.98) translateY(-5px);
}
</style>
