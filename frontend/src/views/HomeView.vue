<script setup>
import { ref, computed } from 'vue'
import { useSearchStore } from '@/stores/search'
import { useCollectionsStore } from '@/stores/collections'
import { useDocumentsStore } from '@/stores/documents'
import PreviewModal from '@/components/PreviewModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const searchStore = useSearchStore()
const collectionsStore = useCollectionsStore()
const documentsStore = useDocumentsStore()

const searchQuery = ref('')
const searchImage = ref(null)
const imagePreview = ref(null)
const searchType = ref('text')
const selectedCollection = ref('')
const fileType = ref('')
const isDragging = ref(false)

const showPreview = ref(false)
const selectedDocument = ref(null)

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
    // Remove from search results
    searchStore.removeResult(deleteTargetId.value)
    closePreview()
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
    fileType: fileType.value || undefined
  })
}

const handleImageSearch = async () => {
  if (!searchImage.value) return
  await searchStore.searchByImage(searchImage.value, {
    collectionId: selectedCollection.value || undefined,
    fileType: fileType.value || undefined
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

const getSimilarityClass = (score) => {
  if (score >= 90) return 'similarity-high'
  if (score >= 70) return 'similarity-medium'
  return 'similarity-low'
}

const getFileUrl = (path) => {
  if (!path) return ''
  const relativePath = path.replace(/^.*\/uploads\//, '')
  return `/files/${relativePath}`
}

// Quick search suggestions
const suggestions = ['風景', 'グラフ', '図面', 'テキスト']

const handleSuggestionClick = (suggestion) => {
  searchQuery.value = suggestion
  searchType.value = 'text'
  handleTextSearch()
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Search Section -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-text-primary mb-6">マルチモーダル検索</h1>

      <!-- Search Box with Glass Effect -->
      <div
        class="search-box relative overflow-hidden rounded-2xl p-6 transition-all duration-300"
        :class="{
          'ring-2 ring-accent/50 shadow-glow-accent': isDragging,
          'shadow-glow-subtle': !isDragging
        }"
        @drop="handleDrop"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
      >
        <!-- Glass background -->
        <div class="absolute inset-0 bg-gradient-to-br from-white/[0.08] via-white/[0.02] to-transparent backdrop-blur-xl"></div>
        <div class="absolute inset-0 border border-white/10 rounded-2xl"></div>

        <!-- Content -->
        <div class="relative z-10">
          <!-- Search Type Tabs with Sliding Indicator -->
          <div class="relative inline-flex gap-1 p-1 bg-bg-tertiary/50 rounded-xl mb-4">
            <!-- Sliding Indicator -->
            <div
              class="absolute top-1 bottom-1 w-[130px] rounded-lg bg-accent transition-all duration-300 ease-smooth"
              :style="{
                left: searchType === 'text' ? '4px' : 'calc(130px + 8px)'
              }"
            ></div>

            <button
              class="relative z-10 w-[130px] flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200"
              :class="searchType === 'text' ? 'text-white' : 'text-text-secondary hover:text-text-primary'"
              @click="searchType = 'text'; clearImage()"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
              テキスト検索
            </button>
            <button
              class="relative z-10 w-[130px] flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200"
              :class="searchType === 'image' ? 'text-white' : 'text-text-secondary hover:text-text-primary'"
              @click="searchType = 'image'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              画像検索
            </button>
          </div>

          <!-- Text Search Input -->
          <div v-if="searchType === 'text'" class="space-y-4">
            <div class="relative group">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="検索キーワードを入力..."
                class="w-full px-4 py-3.5 bg-bg-tertiary/50 border border-white/10 rounded-xl
                       text-text-primary placeholder-text-muted/60
                       focus:outline-none focus:bg-bg-tertiary/80 focus:border-accent/50
                       focus:shadow-glow-input transition-all duration-300"
                @keydown.enter="handleSearch"
              />
              <button
                @click="handleSearch"
                :disabled="isLoading || !searchQuery.trim()"
                class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-accent text-white rounded-lg
                       hover:bg-accent-hover hover:shadow-lg hover:shadow-accent/25
                       disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
                       active:scale-[0.98] transition-all duration-200"
              >
                検索
              </button>
            </div>
          </div>

          <!-- Image Search Input -->
          <div v-else class="space-y-4">
            <div v-if="imagePreview" class="relative inline-block group">
              <img :src="imagePreview" alt="検索画像" class="max-h-48 rounded-xl shadow-lg" />
              <button
                @click="clearImage"
                class="absolute -top-2 -right-2 w-7 h-7 bg-red-500 text-white rounded-full
                       flex items-center justify-center shadow-lg
                       hover:bg-red-600 hover:scale-110 active:scale-95 transition-all duration-200"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div v-else class="border-2 border-dashed border-white/10 rounded-xl p-8 text-center
                            hover:border-accent/50 hover:bg-accent/5 transition-all duration-300 cursor-pointer">
              <input
                type="file"
                accept="image/*"
                class="hidden"
                id="image-input"
                @change="handleImageSelect"
              />
              <label for="image-input" class="cursor-pointer block">
                <div class="relative mx-auto w-16 h-16 mb-4">
                  <div class="absolute inset-0 rounded-full bg-accent/10 animate-ping-slow"></div>
                  <div class="relative flex items-center justify-center w-full h-full rounded-full bg-bg-tertiary border border-white/10">
                    <svg class="w-8 h-8 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
                <p class="text-text-secondary mb-1">画像をドラッグ&ドロップ</p>
                <p class="text-text-muted text-sm">またはクリックして選択</p>
              </label>
            </div>

            <button
              v-if="imagePreview"
              @click="handleSearch"
              :disabled="isLoading"
              class="w-full px-4 py-3.5 bg-accent text-white rounded-xl font-medium
                     hover:bg-accent-hover hover:shadow-lg hover:shadow-accent/25
                     disabled:opacity-50 disabled:cursor-not-allowed
                     active:scale-[0.99] transition-all duration-200"
            >
              {{ isLoading ? '検索中...' : '画像で検索' }}
            </button>
          </div>

          <!-- Filters -->
          <div class="flex gap-4 mt-4 pt-4 border-t border-white/10">
            <select
              v-model="selectedCollection"
              class="px-3 py-2.5 bg-bg-tertiary/50 border border-white/10 rounded-xl
                     text-text-secondary text-sm
                     focus:outline-none focus:border-accent/50 focus:shadow-glow-input
                     transition-all duration-200 cursor-pointer"
            >
              <option value="">すべてのコレクション</option>
              <option v-for="col in collectionsStore.collections" :key="col.id" :value="col.id">
                {{ col.name }}
              </option>
            </select>

            <select
              v-model="fileType"
              class="px-3 py-2.5 bg-bg-tertiary/50 border border-white/10 rounded-xl
                     text-text-secondary text-sm
                     focus:outline-none focus:border-accent/50 focus:shadow-glow-input
                     transition-all duration-200 cursor-pointer"
            >
              <option value="">すべてのタイプ</option>
              <option value="image">画像のみ</option>
              <option value="document">ドキュメントのみ</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Skeleton Loading -->
    <div v-if="isLoading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div
        v-for="n in 8"
        :key="n"
        class="skeleton-card bg-bg-secondary/80 border border-white/5 rounded-xl overflow-hidden"
        :style="{ animationDelay: `${n * 100}ms` }"
      >
        <div class="aspect-square bg-bg-tertiary skeleton-shimmer"></div>
        <div class="p-3 space-y-2">
          <div class="h-4 bg-bg-tertiary rounded skeleton-shimmer w-3/4"></div>
          <div class="h-3 bg-bg-tertiary rounded skeleton-shimmer w-1/2"></div>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-else-if="hasResults">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-medium text-text-primary">検索結果 ({{ results.length }}件)</h2>
      </div>

      <TransitionGroup
        tag="div"
        name="stagger-grid"
        class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
      >
        <div
          v-for="(result, index) in results"
          :key="result.id"
          :style="{ '--stagger-delay': `${index * 50}ms` }"
          class="result-card group relative rounded-xl overflow-hidden cursor-pointer
                 bg-bg-secondary/80 backdrop-blur-sm border border-white/5
                 hover:border-accent/30 hover:shadow-card-hover hover:-translate-y-1
                 transition-all duration-300 ease-out"
          @click="openPreview(result)"
        >
          <!-- Hover glow background -->
          <div class="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-transparent
                      opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>

          <!-- Shine sweep effect -->
          <div class="absolute -inset-1 bg-gradient-to-r from-transparent via-white/5 to-transparent
                      -translate-x-full group-hover:translate-x-full transition-transform duration-700
                      skew-x-12 pointer-events-none"></div>

          <!-- Content -->
          <div class="relative z-10">
            <!-- Thumbnail -->
            <div class="aspect-square bg-bg-tertiary relative overflow-hidden">
              <!-- Background blur for small images -->
              <img
                v-if="result.metadata?.thumbnail_path"
                :src="getFileUrl(result.metadata.thumbnail_path)"
                class="absolute inset-0 w-full h-full object-cover blur-xl scale-110 opacity-30"
              />

              <!-- Main image -->
              <img
                v-if="result.metadata?.thumbnail_path"
                :src="getFileUrl(result.metadata.thumbnail_path)"
                :alt="result.metadata?.file_name"
                class="relative w-full h-full object-contain
                       group-hover:scale-105 transition-transform duration-500 ease-out"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-text-muted">
                <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>

              <!-- Hover overlay with action -->
              <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent
                          opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div class="absolute bottom-2 left-2 right-2 flex items-center justify-center">
                  <span class="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm text-white text-xs font-medium
                              translate-y-2 opacity-0 group-hover:translate-y-0 group-hover:opacity-100
                              transition-all duration-300 delay-100">
                    クリックでプレビュー
                  </span>
                </div>
              </div>

              <!-- Similarity Badge -->
              <div
                :class="['similarity-badge absolute top-2 right-2', getSimilarityClass(result.similarity)]"
              >
                {{ result.similarity.toFixed(1) }}%
              </div>
            </div>

            <!-- Info -->
            <div class="p-3">
              <p class="text-sm text-text-primary truncate">{{ result.metadata?.file_name }}</p>
              <p class="text-xs text-text-muted">{{ result.metadata?.file_type }}</p>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state text-center py-16">
      <!-- Animated icon -->
      <div class="relative mx-auto w-24 h-24 mb-6">
        <div class="absolute inset-0 rounded-full bg-accent/10 animate-ping-slow"></div>
        <div class="absolute inset-2 rounded-full bg-accent/5 animate-ping-slower"></div>
        <div class="relative flex items-center justify-center w-full h-full rounded-full bg-bg-tertiary border border-white/10">
          <svg class="w-10 h-10 text-text-muted animate-float" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      <h3 class="text-lg font-medium text-text-primary mb-2">検索を始めましょう</h3>
      <p class="text-text-muted max-w-sm mx-auto mb-6">
        テキストまたは画像で類似ドキュメントを検索できます
      </p>

      <!-- Suggestion tags -->
      <div class="flex flex-wrap justify-center gap-2">
        <button
          v-for="suggestion in suggestions"
          :key="suggestion"
          class="px-4 py-2 text-sm bg-bg-tertiary/50 backdrop-blur-sm border border-white/10
                 hover:bg-accent/20 hover:border-accent/30 text-text-secondary hover:text-accent
                 rounded-full transition-all duration-200"
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
  </div>
</template>

<style scoped>
.search-box {
  background: linear-gradient(135deg, rgba(26, 26, 26, 0.9) 0%, rgba(15, 15, 15, 0.95) 100%);
}

.skeleton-card {
  animation: skeleton-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.similarity-badge {
  @apply px-2.5 py-1 rounded-lg text-xs font-semibold backdrop-blur-sm;
}

.similarity-high {
  @apply bg-gradient-to-r from-emerald-500/90 to-green-500/90 text-white shadow-lg shadow-green-500/20;
}

.similarity-medium {
  @apply bg-gradient-to-r from-amber-500/90 to-yellow-500/90 text-black shadow-lg shadow-yellow-500/20;
}

.similarity-low {
  @apply bg-gradient-to-r from-red-500/90 to-rose-500/90 text-white shadow-lg shadow-red-500/20;
}
</style>
