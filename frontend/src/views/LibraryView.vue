<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import { useCollectionsStore } from '@/stores/collections'
import PreviewModal from '@/components/PreviewModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const documentsStore = useDocumentsStore()
const collectionsStore = useCollectionsStore()

const showUploadModal = ref(false)
const uploadFiles = ref([])
const uploadCollection = ref('')
const isUploading = ref(false)
const uploadProgress = ref(0)
const isDragging = ref(false)

const showPreview = ref(false)
const selectedDocument = ref(null)

// Multi-select state
const isSelectionMode = ref(false)
const selectedIds = ref(new Set())

const toggleSelectionMode = () => {
  isSelectionMode.value = !isSelectionMode.value
  if (!isSelectionMode.value) {
    selectedIds.value = new Set()
  }
}

const toggleSelect = (id) => {
  const newSet = new Set(selectedIds.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  selectedIds.value = newSet
}

const selectAll = () => {
  selectedIds.value = new Set(documents.value.map(d => d.id))
}

const clearSelection = () => {
  selectedIds.value = new Set()
}

const isSelected = (id) => selectedIds.value.has(id)

const selectedCount = computed(() => selectedIds.value.size)

// Delete confirmation dialog
const showDeleteConfirm = ref(false)
const deleteTargetId = ref(null)
const deleteTargetCount = ref(0)
const isBatchDelete = ref(false)

const handleDeleteRequest = (id) => {
  deleteTargetId.value = id
  deleteTargetCount.value = 1
  isBatchDelete.value = false
  showDeleteConfirm.value = true
}

const handleBatchDeleteRequest = () => {
  if (selectedIds.value.size === 0) return
  deleteTargetCount.value = selectedIds.value.size
  isBatchDelete.value = true
  showDeleteConfirm.value = true
}

const confirmDelete = async () => {
  if (isBatchDelete.value) {
    await documentsStore.deleteDocuments(Array.from(selectedIds.value))
    selectedIds.value = new Set()
    isSelectionMode.value = false
  } else if (deleteTargetId.value) {
    await documentsStore.deleteDocument(deleteTargetId.value)
    closePreview()
  }
  await documentsStore.fetchStats()
  showDeleteConfirm.value = false
  deleteTargetId.value = null
  isBatchDelete.value = false
}

const cancelDelete = () => {
  showDeleteConfirm.value = false
  deleteTargetId.value = null
  isBatchDelete.value = false
}

const deleteConfirmMessage = computed(() => {
  if (isBatchDelete.value) {
    return `${deleteTargetCount.value}件のファイルを削除しますか？この操作は取り消せません。`
  }
  return 'このファイルを削除しますか？この操作は取り消せません。'
})

const handleCardClick = (doc) => {
  if (isSelectionMode.value) {
    toggleSelect(doc.id)
  } else {
    openPreview(doc)
  }
}

const openPreview = (doc) => {
  selectedDocument.value = doc
  showPreview.value = true
}

const closePreview = () => {
  showPreview.value = false
  selectedDocument.value = null
}

const documents = computed(() => documentsStore.documents)
const isLoading = computed(() => documentsStore.loading)
const currentPage = computed(() => documentsStore.pagination?.page || 1)
const totalPages = computed(() => documentsStore.pagination?.pages || 1)

onMounted(async () => {
  await documentsStore.fetchDocuments()
})

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files || [])
  addFiles(files)
}

const addFiles = (files) => {
  const validFiles = files.filter(f =>
    f.type.startsWith('image/') ||
    f.type === 'application/pdf' ||
    f.type.includes('document')
  )
  uploadFiles.value.push(...validFiles)
}

const removeFile = (index) => {
  uploadFiles.value.splice(index, 1)
}

const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files || [])
  addFiles(files)
}

const handleUpload = async () => {
  if (uploadFiles.value.length === 0) return

  isUploading.value = true
  uploadProgress.value = 0

  for (let i = 0; i < uploadFiles.value.length; i++) {
    try {
      await documentsStore.uploadFiles([uploadFiles.value[i]], uploadCollection.value || undefined)
      uploadProgress.value = Math.round(((i + 1) / uploadFiles.value.length) * 100)
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  isUploading.value = false
  uploadFiles.value = []
  showUploadModal.value = false
  await documentsStore.fetchDocuments()
  await documentsStore.fetchStats()
}

const getFileUrl = (path) => {
  if (!path) return ''
  const relativePath = path.replace(/^.*\/uploads\//, '')
  return `/files/${relativePath}`
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    documentsStore.fetchDocuments({ page })
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-text-primary">ライブラリ</h1>
      <div class="flex items-center gap-2">
        <button
          v-if="documents.length > 0"
          @click="toggleSelectionMode"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
            isSelectionMode
              ? 'bg-accent text-white'
              : 'bg-bg-tertiary text-text-secondary hover:bg-bg-primary'
          ]"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          {{ isSelectionMode ? '選択中' : '選択' }}
        </button>
        <button
          @click="showUploadModal = true"
          class="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          アップロード
        </button>
      </div>
    </div>

    <!-- Selection Toolbar -->
    <Transition name="slide">
      <div
        v-if="isSelectionMode"
        class="flex items-center justify-between mb-4 p-3 bg-bg-secondary border border-border rounded-lg"
      >
        <div class="flex items-center gap-4">
          <span class="text-text-secondary">
            {{ selectedCount }}件選択中
          </span>
          <button
            @click="selectAll"
            class="text-sm text-accent hover:text-accent-hover transition-colors"
          >
            すべて選択
          </button>
          <button
            v-if="selectedCount > 0"
            @click="clearSelection"
            class="text-sm text-text-muted hover:text-text-secondary transition-colors"
          >
            選択解除
          </button>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleBatchDeleteRequest"
            :disabled="selectedCount === 0"
            class="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            削除
          </button>
          <button
            @click="toggleSelectionMode"
            class="px-4 py-2 bg-bg-tertiary text-text-secondary rounded-lg hover:bg-bg-primary transition-colors"
          >
            キャンセル
          </button>
        </div>
      </div>
    </Transition>

    <!-- Loading State -->
    <div v-if="isLoading && !documents.length" class="text-center py-12">
      <div class="inline-block w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
      <p class="text-text-muted mt-4">読み込み中...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!documents.length" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto mb-4 text-text-muted opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
      <p class="text-text-muted mb-4">ファイルがありません</p>
      <button
        @click="showUploadModal = true"
        class="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors"
      >
        ファイルをアップロード
      </button>
    </div>

    <!-- Documents Grid -->
    <div v-else>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <div
          v-for="doc in documents"
          :key="doc.id"
          :class="[
            'group bg-bg-secondary border rounded-lg overflow-hidden transition-colors cursor-pointer',
            isSelected(doc.id)
              ? 'border-accent ring-2 ring-accent/50'
              : 'border-border hover:border-accent'
          ]"
          @click="handleCardClick(doc)"
        >
          <!-- Thumbnail -->
          <div class="aspect-square bg-bg-tertiary relative overflow-hidden">
            <img
              v-if="doc.thumbnail_path"
              :src="getFileUrl(doc.thumbnail_path)"
              :alt="doc.file_name"
              class="w-full h-full object-contain group-hover:scale-105 transition-transform duration-200"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-text-muted">
              <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>

            <!-- Selection Checkbox -->
            <div
              v-if="isSelectionMode"
              class="absolute top-2 left-2 z-10"
              @click.stop="toggleSelect(doc.id)"
            >
              <div
                :class="[
                  'w-6 h-6 rounded border-2 flex items-center justify-center transition-colors',
                  isSelected(doc.id)
                    ? 'bg-accent border-accent'
                    : 'bg-black/50 border-white/50 hover:border-white'
                ]"
              >
                <svg
                  v-if="isSelected(doc.id)"
                  class="w-4 h-4 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>

            <!-- Actions (hidden in selection mode) -->
            <div
              v-if="!isSelectionMode"
              class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2"
              @click="openPreview(doc)"
            >
              <button
                @click="openPreview(doc)"
                class="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
                title="プレビュー"
              >
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
              <button
                @click.stop="handleDeleteRequest(doc.id)"
                class="p-2 bg-red-500/80 rounded-full hover:bg-red-500 transition-colors"
                title="削除"
              >
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Info -->
          <div class="p-3">
            <p class="text-sm text-text-primary truncate" :title="doc.file_name">{{ doc.file_name }}</p>
            <div class="flex items-center justify-between mt-1">
              <span class="text-xs text-text-muted">{{ formatDate(doc.created_at) }}</span>
              <span class="text-xs text-text-muted">{{ formatFileSize(doc.file_size) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
        <button
          @click="changePage(currentPage - 1)"
          :disabled="currentPage === 1"
          class="px-3 py-1 bg-bg-secondary border border-border rounded hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          前へ
        </button>
        <span class="text-text-secondary">{{ currentPage }} / {{ totalPages }}</span>
        <button
          @click="changePage(currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="px-3 py-1 bg-bg-secondary border border-border rounded hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          次へ
        </button>
      </div>
    </div>

    <!-- Upload Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showUploadModal"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          @click.self="showUploadModal = false"
        >
          <div class="w-full max-w-lg bg-bg-secondary border border-border rounded-xl shadow-2xl">
            <!-- Header -->
            <div class="flex items-center justify-between p-4 border-b border-border">
              <h3 class="text-lg font-medium text-text-primary">ファイルアップロード</h3>
              <button
                @click="showUploadModal = false"
                class="p-1 hover:bg-bg-tertiary rounded transition-colors"
              >
                <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Content -->
            <div class="p-4 space-y-4">
              <!-- Drop Zone -->
              <div
                :class="[
                  'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
                  isDragging ? 'border-accent bg-accent/10' : 'border-border hover:border-accent'
                ]"
                @drop="handleDrop"
                @dragover.prevent="isDragging = true"
                @dragleave="isDragging = false"
              >
                <input
                  type="file"
                  multiple
                  accept="image/*,.pdf"
                  class="hidden"
                  id="file-input"
                  @change="handleFileSelect"
                />
                <label for="file-input" class="cursor-pointer">
                  <svg class="w-12 h-12 mx-auto text-text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p class="text-text-secondary mb-1">ファイルをドラッグ＆ドロップ</p>
                  <p class="text-text-muted text-sm">またはクリックして選択</p>
                </label>
              </div>

              <!-- Collection Select -->
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">コレクション（任意）</label>
                <select
                  v-model="uploadCollection"
                  class="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-secondary focus:outline-none focus:border-accent"
                >
                  <option value="">コレクションなし</option>
                  <option v-for="col in collectionsStore.collections" :key="col.id" :value="col.id">
                    {{ col.name }}
                  </option>
                </select>
              </div>

              <!-- File List -->
              <div v-if="uploadFiles.length > 0" class="space-y-2 max-h-48 overflow-auto">
                <div
                  v-for="(file, index) in uploadFiles"
                  :key="index"
                  class="flex items-center justify-between p-2 bg-bg-tertiary rounded"
                >
                  <div class="flex items-center gap-2 min-w-0">
                    <svg class="w-4 h-4 text-text-muted flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span class="text-sm text-text-secondary truncate">{{ file.name }}</span>
                  </div>
                  <button
                    @click="removeFile(index)"
                    class="p-1 hover:bg-bg-primary rounded text-text-muted hover:text-red-500 transition-colors"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Progress -->
              <div v-if="isUploading" class="space-y-2">
                <div class="h-2 bg-bg-tertiary rounded-full overflow-hidden">
                  <div
                    class="h-full bg-accent transition-all duration-300"
                    :style="{ width: uploadProgress + '%' }"
                  ></div>
                </div>
                <p class="text-sm text-text-muted text-center">{{ uploadProgress }}% 完了</p>
              </div>
            </div>

            <!-- Footer -->
            <div class="flex justify-end gap-2 p-4 border-t border-border">
              <button
                @click="showUploadModal = false"
                class="px-4 py-2 bg-bg-tertiary text-text-secondary rounded-lg hover:bg-bg-primary transition-colors"
              >
                キャンセル
              </button>
              <button
                @click="handleUpload"
                :disabled="uploadFiles.length === 0 || isUploading"
                class="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {{ isUploading ? 'アップロード中...' : 'アップロード' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

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
      :message="deleteConfirmMessage"
      confirm-text="削除"
      cancel-text="キャンセル"
      type="danger"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
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

.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
