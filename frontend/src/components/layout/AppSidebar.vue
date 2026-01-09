<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import { useSearchStore } from '@/stores/search'

const route = useRoute()
const documentsStore = useDocumentsStore()
const searchStore = useSearchStore()

const navItems = [
  { name: 'home', path: '/', label: '検索', icon: 'search' },
  { name: 'library', path: '/library', label: 'ライブラリ', icon: 'folder' },
  { name: 'collections', path: '/collections', label: 'コレクション', icon: 'collection' }
]

const isActive = (name) => route.name === name

const stats = computed(() => documentsStore.stats)
</script>

<template>
  <aside class="fixed left-0 top-0 bottom-0 w-64 bg-bg-secondary border-r border-border flex flex-col">
    <!-- Logo -->
    <div class="p-4 border-b border-border">
      <h1 class="text-xl font-bold text-accent">Qwen3-VL</h1>
      <p class="text-sm text-text-muted">Multimodal Search</p>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 p-3 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        :class="['sidebar-item', { active: isActive(item.name) }]"
      >
        <!-- Icons -->
        <svg v-if="item.icon === 'search'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <svg v-else-if="item.icon === 'folder'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <svg v-else-if="item.icon === 'collection'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Recent Searches -->
    <div v-if="searchStore.recentSearches.length > 0" class="p-3 border-t border-border">
      <h3 class="text-xs font-medium text-text-muted uppercase tracking-wider mb-2 px-3">最近の検索</h3>
      <div class="space-y-1 max-h-32 overflow-auto">
        <div
          v-for="search in searchStore.recentSearches.slice(0, 5)"
          :key="search.id"
          class="text-sm text-text-secondary truncate px-3 py-1 hover:bg-bg-tertiary rounded cursor-pointer"
        >
          {{ search.query_text || '画像検索' }}
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div v-if="stats" class="p-4 border-t border-border">
      <div class="text-sm text-text-muted space-y-1">
        <div class="flex justify-between">
          <span>ファイル数</span>
          <span class="text-text-secondary">{{ stats.total_files }}</span>
        </div>
        <div class="flex justify-between">
          <span>コレクション</span>
          <span class="text-text-secondary">{{ stats.total_collections }}</span>
        </div>
      </div>
    </div>
  </aside>
</template>
