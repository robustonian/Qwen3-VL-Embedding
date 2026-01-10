<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import { useSearchStore } from '@/stores/search'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle'])

const route = useRoute()
const router = useRouter()
const documentsStore = useDocumentsStore()
const searchStore = useSearchStore()

const navItems = [
  { name: 'home', path: '/', label: '検索', icon: 'search' },
  { name: 'library', path: '/library', label: 'ライブラリ', icon: 'folder' },
  { name: 'collections', path: '/collections', label: 'コレクション', icon: 'collection' }
]

const isActive = (name) => route.name === name

const stats = computed(() => documentsStore.stats)

const handleRecentSearchClick = (search) => {
  if (search.query_text) {
    searchStore.searchByText(search.query_text)
    router.push('/')
  }
}
</script>

<template>
  <aside
    class="fixed left-0 top-0 bottom-0 flex flex-col transition-all duration-300 ease-smooth z-40"
    :class="collapsed ? 'w-[72px]' : 'w-64'"
  >
    <!-- Background with gradient -->
    <div class="absolute inset-0 bg-bg-secondary border-r border-border/50">
      <!-- Subtle gradient overlay -->
      <div class="absolute inset-0 bg-gradient-to-b from-accent/[0.02] via-transparent to-transparent"></div>
    </div>

    <!-- Content -->
    <div class="relative z-10 flex flex-col h-full">
      <!-- Logo & Toggle -->
      <div class="p-4 border-b border-border/50">
        <div v-if="!collapsed" class="space-y-1">
          <!-- Logo with gradient text -->
          <h1 class="text-lg font-display font-bold text-gradient">
            Qwen3-VL-Embedding
          </h1>
          <div class="flex items-center justify-between">
            <p class="text-xs text-text-muted tracking-wide uppercase">Embedding Search</p>
            <button
              @click="emit('toggle')"
              class="p-1.5 rounded-lg hover:bg-bg-tertiary text-text-muted hover:text-text-primary transition-all duration-200 hover:scale-105"
              title="Collapse sidebar"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Collapsed state - just toggle button -->
        <button
          v-else
          @click="emit('toggle')"
          class="w-full flex items-center justify-center p-2 rounded-xl hover:bg-bg-tertiary text-text-muted hover:text-accent transition-all duration-200"
          title="Expand sidebar"
        >
          <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-3 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="item.path"
          :class="[
            'sidebar-item group',
            { 'active': isActive(item.name) }
          ]"
          :title="collapsed ? item.label : ''"
        >
          <!-- Icons with subtle animation -->
          <div :class="[
            'flex-shrink-0 transition-transform duration-200',
            isActive(item.name) ? '' : 'group-hover:scale-110'
          ]">
            <svg v-if="item.icon === 'search'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <svg v-else-if="item.icon === 'folder'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <svg v-else-if="item.icon === 'collection'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>

          <!-- Label with slide animation -->
          <span
            v-if="!collapsed"
            class="whitespace-nowrap overflow-hidden transition-all duration-200"
          >
            {{ item.label }}
          </span>

          <!-- Keyboard hint -->
          <span
            v-if="!collapsed && item.name === 'home'"
            class="ml-auto text-[10px] text-text-muted bg-bg-tertiary px-1.5 py-0.5 rounded font-mono opacity-0 group-hover:opacity-100 transition-opacity"
          >
            /
          </span>
        </router-link>
      </nav>

      <!-- Recent Searches (hidden when collapsed) -->
      <div
        v-if="!collapsed && searchStore.recentSearches.length > 0"
        class="p-3 border-t border-border/50"
      >
        <h3 class="text-[10px] font-medium text-text-muted uppercase tracking-wider mb-2 px-3">
          最近の検索
        </h3>
        <div class="space-y-0.5 max-h-28 overflow-auto scrollbar-hidden">
          <button
            v-for="search in searchStore.recentSearches.slice(0, 5)"
            :key="search.id"
            @click="handleRecentSearchClick(search)"
            class="w-full text-left text-sm text-text-secondary truncate px-3 py-1.5 hover:bg-bg-tertiary hover:text-text-primary rounded-lg cursor-pointer transition-all duration-150 group"
          >
            <span class="flex items-center gap-2">
              <svg class="w-3 h-3 text-text-muted group-hover:text-accent transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="truncate">{{ search.query_text || '画像検索' }}</span>
            </span>
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div v-if="stats" class="p-3 border-t border-border/50">
        <div v-if="!collapsed" class="grid grid-cols-2 gap-2">
          <!-- Files stat card -->
          <div class="stat-card">
            <div class="stat-icon bg-accent/10 text-accent">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <p class="text-lg font-display font-semibold text-text-primary">{{ stats.total_files }}</p>
              <p class="text-[10px] text-text-muted uppercase tracking-wide">ファイル</p>
            </div>
          </div>

          <!-- Collections stat card -->
          <div class="stat-card">
            <div class="stat-icon bg-accent-warm/10 text-accent-warm">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div>
              <p class="text-lg font-display font-semibold text-text-primary">{{ stats.total_collections }}</p>
              <p class="text-[10px] text-text-muted uppercase tracking-wide">コレクション</p>
            </div>
          </div>
        </div>

        <!-- Collapsed Stats (icons only with tooltip) -->
        <div v-else class="flex flex-col items-center gap-3">
          <div
            class="flex items-center justify-center w-10 h-10 rounded-xl bg-bg-tertiary text-text-secondary"
            :title="`${stats.total_files} ファイル`"
          >
            <span class="text-sm font-medium">{{ stats.total_files }}</span>
          </div>
          <div
            class="flex items-center justify-center w-10 h-10 rounded-xl bg-bg-tertiary text-text-secondary"
            :title="`${stats.total_collections} コレクション`"
          >
            <span class="text-sm font-medium">{{ stats.total_collections }}</span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.stat-card {
  @apply flex items-center gap-2 p-2 rounded-xl bg-bg-tertiary/50 border border-border/30;
}

.stat-icon {
  @apply flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center;
}
</style>
