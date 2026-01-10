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
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Search Section -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-text-primary mb-6">マルチモーダル検索</h1>

      <!-- Search Box -->
      <div
        class="bg-bg-secondary border border-border rounded-xl p-6 transition-colors"
        :class="{ 'border-accent': isDragging }"
        @drop="handleDrop"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
      >
        <!-- Search Type Tabs -->
        <div class="flex gap-2 mb-4">
          <button
            :class="['tab-btn', { active: searchType === 'text' }]"
            @click="searchType = 'text'; clearImage()"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
            テキスト検索
          </button>
          <button
            :class="['tab-btn', { active: searchType === 'image' }]"
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
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="検索キーワードを入力..."
              class="w-full px-4 py-3 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent transition-colors"
              @keydown.enter="handleSearch"
            />
            <button
              @click="handleSearch"
              :disabled="isLoading || !searchQuery.trim()"
              class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-accent text-white rounded-md hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              検索
            </button>
          </div>
        </div>

        <!-- Image Search Input -->
        <div v-else class="space-y-4">
          <div v-if="imagePreview" class="relative inline-block">
            <img :src="imagePreview" alt="検索画像" class="max-h-48 rounded-lg" />
            <button
              @click="clearImage"
              class="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div v-else class="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-accent transition-colors">
            <input
              type="file"
              accept="image/*"
              class="hidden"
              id="image-input"
              @change="handleImageSelect"
            />
            <label for="image-input" class="cursor-pointer">
              <svg class="w-12 h-12 mx-auto text-text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p class="text-text-secondary mb-1">画像をドラッグ＆ドロップ</p>
              <p class="text-text-muted text-sm">またはクリックして選択</p>
            </label>
          </div>

          <button
            v-if="imagePreview"
            @click="handleSearch"
            :disabled="isLoading"
            class="w-full px-4 py-3 bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ isLoading ? '検索中...' : '画像で検索' }}
          </button>
        </div>

        <!-- Filters -->
        <div class="flex gap-4 mt-4 pt-4 border-t border-border">
          <select
            v-model="selectedCollection"
            class="px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-secondary text-sm focus:outline-none focus:border-accent"
          >
            <option value="">すべてのコレクション</option>
            <option v-for="col in collectionsStore.collections" :key="col.id" :value="col.id">
              {{ col.name }}
            </option>
          </select>

          <select
            v-model="fileType"
            class="px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-secondary text-sm focus:outline-none focus:border-accent"
          >
            <option value="">すべてのタイプ</option>
            <option value="image">画像のみ</option>
            <option value="document">ドキュメントのみ</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="isLoading" class="text-center py-12">
      <div class="inline-block w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
      <p class="text-text-muted mt-4">検索中...</p>
    </div>

    <div v-else-if="hasResults">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-medium text-text-primary">検索結果 ({{ results.length }}件)</h2>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div
          v-for="result in results"
          :key="result.id"
          class="group bg-bg-secondary border border-border rounded-lg overflow-hidden hover:border-accent transition-colors cursor-pointer"
          @click="openPreview(result)"
        >
          <!-- Thumbnail -->
          <div class="aspect-square bg-bg-tertiary relative overflow-hidden">
            <img
              v-if="result.metadata?.thumbnail_path"
              :src="getFileUrl(result.metadata.thumbnail_path)"
              :alt="result.metadata?.file_name"
              class="w-full h-full object-contain group-hover:scale-105 transition-transform duration-200"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-text-muted">
              <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>

            <!-- Similarity Badge -->
            <div
              :class="['absolute top-2 right-2 px-2 py-1 rounded text-xs font-medium', getSimilarityClass(result.similarity)]"
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
    </div>

    <div v-else class="text-center py-12 text-text-muted">
      <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <p>テキストまたは画像で検索してください</p>
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
.tab-btn {
  @apply flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-text-secondary bg-bg-tertiary hover:bg-bg-primary transition-colors;
}

.tab-btn.active {
  @apply bg-accent text-white;
}

.similarity-high {
  @apply bg-green-500/90 text-white;
}

.similarity-medium {
  @apply bg-yellow-500/90 text-black;
}

.similarity-low {
  @apply bg-red-500/90 text-white;
}
</style>
