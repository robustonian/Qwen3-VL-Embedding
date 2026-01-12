<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSearchStore } from '@/stores/search'
import { useCollectionsStore } from '@/stores/collections'
import { useDocumentsStore } from '@/stores/documents'
import { useToastStore } from '@/stores/toast'
import PreviewModal from '@/components/PreviewModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ClipboardSearchModal from '@/components/ClipboardSearchModal.vue'

const searchStore = useSearchStore()
const collectionsStore = useCollectionsStore()
const documentsStore = useDocumentsStore()
const toastStore = useToastStore()

const searchQuery = ref('')
const searchImage = ref(null)
const imagePreview = ref(null)
const searchType = ref('text')
const selectedCollection = ref('')
const selectedFileTypes = ref([])  // Multi-select: ['text', 'image', 'pdf']
const isDragging = ref(false)
const searchInputRef = ref(null)

// File type options for multi-select
const fileTypeOptions = [
  { value: 'text', label: 'テキスト', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { value: 'image', label: '画像', icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' },
  { value: 'pdf', label: 'PDF', icon: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z' }
]

const toggleFileType = (type) => {
  const index = selectedFileTypes.value.indexOf(type)
  if (index === -1) {
    selectedFileTypes.value.push(type)
  } else {
    selectedFileTypes.value.splice(index, 1)
  }
}

const showPreview = ref(false)
const selectedDocument = ref(null)
const showClipboardSearchModal = ref(false)

// Clipboard paste handler for image search
const handlePaste = (e) => {
  if (showClipboardSearchModal.value || showPreview.value) return
  if (document.activeElement?.tagName === 'INPUT' ||
      document.activeElement?.tagName === 'TEXTAREA') return

  // Check for image in clipboard
  const items = e.clipboardData?.items
  if (items) {
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault()
        showClipboardSearchModal.value = true
        return
      }
    }
  }
}

const handleClipboardSearch = async (imageFile) => {
  setImageFile(imageFile)
  await handleImageSearch()
}

const openPreview = (result) => {
  selectedDocument.value = result
  showPreview.value = true
}

const closePreview = () => {
  showPreview.value = false
  selectedDocument.value = null
}

// Delete confirmation
const showDeleteConfirm = ref(false)
const deleteTargetId = ref(null)

const handleDeleteRequest = (id) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const confirmDelete = async () => {
  if (deleteTargetId.value) {
    await documentsStore.deleteDocument(deleteTargetId.value)
    searchStore.removeResult(deleteTargetId.value)
    closePreview()
    toastStore.success('ファイルを削除しました')
  }
  showDeleteConfirm.value = false
  deleteTargetId.value = null
}

const cancelDelete = () => {
  showDeleteConfirm.value = false
  deleteTargetId.value = null
}

const isLoading = computed(() => searchStore.loading)
const results = computed(() => searchStore.results)
const hasResults = computed(() => searchStore.hasResults)

const handleTextSearch = async () => {
  if (!searchQuery.value.trim()) return
  await searchStore.searchByText(searchQuery.value, {
    collectionId: selectedCollection.value || undefined,
    fileTypes: selectedFileTypes.value.length > 0 ? selectedFileTypes.value : undefined
  })
}

const handleImageSearch = async () => {
  if (!searchImage.value) return
  await searchStore.searchByImage(searchImage.value, {
    collectionId: selectedCollection.value || undefined,
    fileTypes: selectedFileTypes.value.length > 0 ? selectedFileTypes.value : undefined
  })
}

const handleSearch = () => {
  if (searchType.value === 'text') {
    handleTextSearch()
  } else {
    handleImageSearch()
  }
}

const handleImageSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    setImageFile(file)
  }
}

const setImageFile = (file) => {
  searchImage.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target.result
  }
  reader.readAsDataURL(file)
  searchType.value = 'image'
}

const clearImage = () => {
  searchImage.value = null
  imagePreview.value = null
  searchType.value = 'text'
}

const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file && file.type.startsWith('image/')) {
    setImageFile(file)
  }
}

const handleDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const getSimilarityLevel = (score) => {
  if (score >= 90) return 'high'
  if (score >= 70) return 'medium'
  return 'low'
}

const getFileUrl = (path) => {
  if (!path) return ''
  const relativePath = path.replace(/^.*\/uploads\//, '')
  return `/files/${relativePath}`
}

// Quick search suggestions
const suggestions = ['風景', 'グラフ', '図面', 'テキスト', 'ポートレート']

const handleSuggestionClick = (suggestion) => {
  searchQuery.value = suggestion
  searchType.value = 'text'
  handleTextSearch()
}

// Focus search input on "/" key
const handleFocusSearch = () => {
  searchInputRef.value?.focus()
}

onMounted(() => {
  window.addEventListener('focus-search', handleFocusSearch)
  document.addEventListener('paste', handlePaste)
})

onUnmounted(() => {
  window.removeEventListener('focus-search', handleFocusSearch)
  document.removeEventListener('paste', handlePaste)
})
</script>

<template>
  <div id="main-content" class="max-w-6xl mx-auto">
    <!-- Search Section -->
    <div class="mb-10">
      <!-- Title with gradient -->
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-display font-bold text-text-primary mb-2">
          マルチモーダル<span class="text-gradient">検索</span>
        </h1>
        <p class="text-text-secondary">テキストまたは画像で類似ドキュメントを検索</p>
      </div>

      <!-- Search Box with Glass Effect -->
      <div
        class="search-box relative overflow-hidden rounded-3xl transition-all duration-500"
        :class="{
          'ring-2 ring-accent/50 shadow-glow-strong': isDragging,
          'shadow-glow-subtle': !isDragging
        }"
        @drop="handleDrop"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
      >
        <!-- Animated gradient background -->
        <div class="absolute inset-0 bg-gradient-to-br from-bg-secondary via-bg-tertiary/50 to-bg-secondary"></div>
        <div class="absolute inset-0 bg-gradient-to-tr from-accent/[0.03] via-transparent to-accent-warm/[0.02]"></div>

        <!-- Noise texture -->
        <div class="absolute inset-0 noise-overlay opacity-50"></div>

        <!-- Border glow effect -->
        <div class="absolute inset-0 rounded-3xl border border-white/10"></div>

        <!-- Content -->
        <div class="relative z-10 p-8">
          <!-- Search Type Tabs -->
          <div class="flex justify-center mb-6">
            <div class="relative inline-flex gap-1 p-1.5 bg-bg-primary/50 backdrop-blur-sm rounded-2xl border border-border/30">
              <!-- Sliding Indicator -->
              <div
                class="absolute top-1.5 bottom-1.5 w-[140px] rounded-xl bg-accent/20 border border-accent/30 transition-all duration-300 ease-smooth"
                :style="{
                  left: searchType === 'text' ? '6px' : 'calc(140px + 10px)'
                }"
              ></div>

              <button
                class="relative z-10 w-[140px] flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all duration-200"
                :class="searchType === 'text' ? 'text-accent' : 'text-text-secondary hover:text-text-primary'"
                @click="searchType = 'text'; clearImage()"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                </svg>
                テキスト検索
              </button>
              <button
                class="relative z-10 w-[140px] flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all duration-200"
                :class="searchType === 'image' ? 'text-accent' : 'text-text-secondary hover:text-text-primary'"
                @click="searchType = 'image'"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                画像検索
              </button>
            </div>
          </div>

          <!-- Text Search Input -->
          <div v-if="searchType === 'text'" class="space-y-4">
            <div class="relative">
              <!-- Input glow on focus -->
              <div class="absolute -inset-0.5 bg-gradient-to-r from-accent/20 via-accent/5 to-accent/20 rounded-2xl blur-sm opacity-0 group-focus-within:opacity-100 transition-opacity"></div>

              <div class="relative group">
                <input
                  ref="searchInputRef"
                  v-model="searchQuery"
                  type="text"
                  placeholder="検索キーワードを入力... (/ でフォーカス)"
                  class="w-full px-5 py-4 bg-bg-primary/60 border border-border/50 rounded-2xl
                         text-text-primary text-lg placeholder-text-muted/50
                         focus:outline-none focus:bg-bg-primary/80 focus:border-accent/40 focus:shadow-glow-input
                         transition-all duration-300"
                  @keydown.enter="handleSearch"
                />
                <button
                  @click="handleSearch"
                  :disabled="isLoading || !searchQuery.trim()"
                  class="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5 bg-accent text-bg-primary font-medium rounded-xl
                         hover:bg-accent-hover hover:shadow-glow-accent
                         disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-none
                         active:scale-[0.98] transition-all duration-200"
                >
                  <span v-if="!isLoading">検索</span>
                  <svg v-else class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Image Search Input -->
          <div v-else class="space-y-4">
            <div v-if="imagePreview" class="relative inline-block group">
              <div class="relative rounded-2xl overflow-hidden shadow-card-elevated">
                <img :src="imagePreview" alt="検索画像" class="max-h-56 rounded-2xl" />
                <!-- Overlay gradient -->
                <div class="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              </div>
              <button
                @click="clearImage"
                class="absolute -top-2 -right-2 w-8 h-8 bg-error text-white rounded-full
                       flex items-center justify-center shadow-lg
                       hover:bg-red-600 hover:scale-110 active:scale-95 transition-all duration-200"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div
              v-else
              class="border-2 border-dashed border-border/50 rounded-2xl p-10 text-center
                     hover:border-accent/50 hover:bg-accent/5 transition-all duration-300 cursor-pointer group"
            >
              <input
                type="file"
                accept="image/*"
                class="hidden"
                id="image-input"
                @change="handleImageSelect"
              />
              <label for="image-input" class="cursor-pointer block">
                <!-- Animated icon container -->
                <div class="relative mx-auto w-20 h-20 mb-5">
                  <div class="absolute inset-0 rounded-full bg-accent/10 animate-ping-slow"></div>
                  <div class="absolute inset-2 rounded-full bg-accent/5 animate-ping-slower"></div>
                  <div class="relative flex items-center justify-center w-full h-full rounded-full bg-bg-tertiary/80 border border-border/50 group-hover:border-accent/30 transition-colors">
                    <svg class="w-8 h-8 text-text-muted group-hover:text-accent transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
                <p class="text-text-primary font-medium mb-1">画像をドラッグ&ドロップ</p>
                <p class="text-text-muted text-sm">クリックして選択、または <kbd class="px-1.5 py-0.5 bg-bg-tertiary rounded text-xs font-mono">Ctrl+V</kbd> で貼り付け</p>
              </label>
            </div>

            <button
              v-if="imagePreview"
              @click="handleSearch"
              :disabled="isLoading"
              class="w-full px-6 py-4 bg-accent text-bg-primary font-medium rounded-2xl
                     hover:bg-accent-hover hover:shadow-glow-accent
                     disabled:opacity-50 disabled:cursor-not-allowed
                     active:scale-[0.99] transition-all duration-200"
            >
              <span v-if="!isLoading" class="flex items-center justify-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                画像で検索
              </span>
              <span v-else class="flex items-center justify-center gap-2">
                <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                検索中...
              </span>
            </button>
          </div>

          <!-- Filters -->
          <div class="flex flex-wrap items-center gap-3 mt-6 pt-6 border-t border-border/30">
            <select
              v-model="selectedCollection"
              class="px-4 py-2.5 bg-bg-primary/50 border border-border/50 rounded-xl
                     text-text-secondary text-sm
                     focus:outline-none focus:border-accent/50 focus:shadow-glow-input
                     transition-all duration-200 cursor-pointer"
            >
              <option value="">すべてのコレクション</option>
              <option v-for="col in collectionsStore.collections" :key="col.id" :value="col.id">
                {{ col.name }}
              </option>
            </select>

            <!-- File Type Multi-Select -->
            <div class="flex items-center gap-2">
              <span class="text-text-muted text-sm">タイプ:</span>
              <div class="flex gap-1.5">
                <button
                  v-for="option in fileTypeOptions"
                  :key="option.value"
                  @click="toggleFileType(option.value)"
                  :class="[
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 border',
                    selectedFileTypes.includes(option.value)
                      ? 'bg-accent/20 border-accent/50 text-accent'
                      : 'bg-bg-primary/50 border-border/50 text-text-secondary hover:border-accent/30 hover:text-text-primary'
                  ]"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="option.icon" />
                  </svg>
                  {{ option.label }}
                </button>
              </div>
              <button
                v-if="selectedFileTypes.length > 0"
                @click="selectedFileTypes = []"
                class="text-xs text-text-muted hover:text-text-secondary transition-colors"
              >
                クリア
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Skeleton Loading -->
    <div v-if="isLoading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
      <div
        v-for="n in 8"
        :key="n"
        class="skeleton-card bg-bg-secondary/60 border border-border/30 rounded-2xl overflow-hidden"
        :style="{ animationDelay: `${n * 80}ms` }"
      >
        <div class="aspect-square bg-bg-tertiary/50 skeleton-shimmer"></div>
        <div class="p-4 space-y-3">
          <div class="h-4 bg-bg-tertiary/50 rounded-lg skeleton-shimmer w-3/4"></div>
          <div class="h-3 bg-bg-tertiary/50 rounded-lg skeleton-shimmer w-1/2"></div>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-else-if="hasResults">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-display font-semibold text-text-primary">
          検索結果 <span class="text-accent">({{ results.length }}件)</span>
        </h2>
      </div>

      <TransitionGroup
        tag="div"
        name="stagger-grid"
        class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5"
      >
        <div
          v-for="(result, index) in results"
          :key="result.id"
          :style="{ '--stagger-delay': `${index * 50}ms` }"
          class="result-card group relative rounded-2xl overflow-hidden cursor-pointer card-3d
                 bg-bg-secondary/60 backdrop-blur-sm border border-border/30
                 hover:border-accent/40 hover:shadow-card-hover
                 transition-all duration-300"
          @click="openPreview(result)"
        >
          <!-- Hover gradient overlay -->
          <div class="absolute inset-0 bg-gradient-to-br from-accent/10 via-transparent to-accent-warm/5
                      opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>

          <!-- Shine sweep effect -->
          <div class="shine-effect absolute -inset-1 bg-gradient-to-r from-transparent via-white/10 to-transparent
                      -translate-x-full group-hover:translate-x-full transition-transform duration-700
                      skew-x-12 pointer-events-none"></div>

          <!-- Content -->
          <div class="relative z-10">
            <!-- Thumbnail -->
            <div class="aspect-square bg-bg-tertiary/50 relative overflow-hidden">
              <!-- Blurred background for context -->
              <img
                v-if="result.metadata?.thumbnail_path"
                :src="getFileUrl(result.metadata.thumbnail_path)"
                class="absolute inset-0 w-full h-full object-cover blur-2xl scale-125 opacity-30"
                aria-hidden="true"
              />

              <!-- Main image -->
              <img
                v-if="result.metadata?.thumbnail_path"
                :src="getFileUrl(result.metadata.thumbnail_path)"
                :alt="result.metadata?.file_name"
                class="relative w-full h-full object-contain
                       group-hover:scale-105 transition-transform duration-500 ease-smooth"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-text-muted">
                <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>

              <!-- Hover action hint -->
              <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent
                          opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div class="absolute bottom-3 left-3 right-3 flex items-center justify-center">
                  <span class="px-4 py-2 rounded-xl bg-white/10 backdrop-blur-md text-white text-sm font-medium
                              translate-y-3 opacity-0 group-hover:translate-y-0 group-hover:opacity-100
                              transition-all duration-300 delay-100">
                    プレビューを開く
                  </span>
                </div>
              </div>

              <!-- Similarity Badge - Circular progress style -->
              <div class="absolute top-3 right-3">
                <div
                  :class="[
                    'similarity-ring relative w-12 h-12 rounded-full flex items-center justify-center',
                    `similarity-${getSimilarityLevel(result.similarity)}`
                  ]"
                >
                  <span class="text-xs font-bold text-white">{{ Math.round(result.similarity) }}</span>
                </div>
              </div>
            </div>

            <!-- Info -->
            <div class="p-4">
              <p class="text-sm font-medium text-text-primary truncate mb-1">{{ result.metadata?.file_name }}</p>
              <p class="text-xs text-text-muted">{{ result.metadata?.file_type }}</p>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state text-center py-20">
      <!-- Animated orbital icon -->
      <div class="relative mx-auto w-28 h-28 mb-8">
        <!-- Orbit rings -->
        <div class="absolute inset-0 rounded-full border border-accent/20"></div>
        <div class="absolute inset-3 rounded-full border border-accent/10"></div>

        <!-- Orbiting dot -->
        <div class="absolute inset-0 animate-orbit">
          <div class="w-2 h-2 rounded-full bg-accent shadow-glow-accent"></div>
        </div>

        <!-- Center icon -->
        <div class="absolute inset-4 rounded-full bg-bg-tertiary/80 border border-border/50 flex items-center justify-center">
          <svg class="w-10 h-10 text-text-muted animate-float-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      <h3 class="text-xl font-display font-semibold text-text-primary mb-3">検索を始めましょう</h3>
      <p class="text-text-secondary max-w-md mx-auto mb-8">
        テキストまたは画像で類似ドキュメントを検索できます。<br>
        キーボードショートカット <kbd class="px-2 py-1 bg-bg-tertiary rounded text-xs font-mono text-text-muted">/</kbd> で検索にフォーカス
      </p>

      <!-- Suggestion tags -->
      <div class="flex flex-wrap justify-center gap-2">
        <button
          v-for="suggestion in suggestions"
          :key="suggestion"
          class="px-5 py-2.5 text-sm bg-bg-tertiary/50 backdrop-blur-sm border border-border/30
                 hover:bg-accent/10 hover:border-accent/40 text-text-secondary hover:text-accent
                 rounded-xl transition-all duration-200 hover:shadow-glow-accent/20"
          @click="handleSuggestionClick(suggestion)"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>

    <!-- Preview Modal -->
    <PreviewModal
      :show="showPreview"
      :document="selectedDocument"
      @close="closePreview"
      @delete="handleDeleteRequest"
    />

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog
      :show="showDeleteConfirm"
      title="ファイルを削除"
      message="このファイルを削除しますか？この操作は取り消せません。"
      confirm-text="削除"
      cancel-text="キャンセル"
      type="danger"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />

    <!-- Clipboard Search Modal -->
    <ClipboardSearchModal
      :show="showClipboardSearchModal"
      @close="showClipboardSearchModal = false"
      @search="handleClipboardSearch"
    />
  </div>
</template>

<style scoped>
.search-box {
  background: linear-gradient(145deg, rgba(18, 18, 26, 0.95) 0%, rgba(10, 10, 11, 0.98) 100%);
}

.skeleton-card {
  animation: skeleton-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Similarity ring styles */
.similarity-ring {
  @apply backdrop-blur-sm;
}

.similarity-ring::before {
  content: '';
  @apply absolute inset-0 rounded-full;
}

.similarity-high {
  background: linear-gradient(135deg, rgba(0, 214, 143, 0.9) 0%, rgba(0, 168, 120, 0.9) 100%);
  box-shadow: 0 0 20px rgba(0, 214, 143, 0.4);
}

.similarity-medium {
  background: linear-gradient(135deg, rgba(255, 170, 0, 0.9) 0%, rgba(245, 166, 35, 0.9) 100%);
  box-shadow: 0 0 20px rgba(255, 170, 0, 0.4);
}

.similarity-low {
  background: linear-gradient(135deg, rgba(255, 90, 90, 0.9) 0%, rgba(220, 60, 60, 0.9) 100%);
  box-shadow: 0 0 20px rgba(255, 90, 90, 0.4);
}

/* Shine effect */
.shine-effect {
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
}

/* Select dropdown styling */
select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 1rem;
  padding-right: 2.5rem;
}

select option {
  background-color: #1a1a24;
  color: #e2e8f0;
  padding: 0.5rem;
}

select option:hover,
select option:focus,
select option:checked {
  background-color: #2d2d3d;
  color: #ffffff;
}
</style>
