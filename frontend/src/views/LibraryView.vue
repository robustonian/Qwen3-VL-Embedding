<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import { useCollectionsStore } from '@/stores/collections'
import { useToastStore } from '@/stores/toast'
import PreviewModal from '@/components/PreviewModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ClipboardUploadModal from '@/components/ClipboardUploadModal.vue'

const documentsStore = useDocumentsStore()
const collectionsStore = useCollectionsStore()
const toastStore = useToastStore()

const showUploadModal = ref(false)
const uploadFiles = ref([])
const uploadCollection = ref('')
const isUploading = ref(false)
const uploadProgress = ref(0)
const isDragging = ref(false)

const showPreview = ref(false)
const selectedDocument = ref(null)
const showClipboardModal = ref(false)

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
    toastStore.success(`${deleteTargetCount.value}件のファイルを削除しました`)
    selectedIds.value = new Set()
    isSelectionMode.value = false
  } else if (deleteTargetId.value) {
    await documentsStore.deleteDocument(deleteTargetId.value)
    toastStore.success('ファイルを削除しました')
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

const navigatePreview = (direction) => {
  if (!selectedDocument.value) return
  const docs = documentsStore.documents
  const currentIndex = docs.findIndex(d => d.id === selectedDocument.value.id)
  if (currentIndex === -1) return

  const newIndex = direction === 'prev'
    ? currentIndex - 1
    : currentIndex + 1

  if (newIndex >= 0 && newIndex < docs.length) {
    selectedDocument.value = docs[newIndex]
  }
}

const documents = computed(() => documentsStore.documents)
const isLoading = computed(() => documentsStore.loading)
const currentPage = computed(() => documentsStore.pagination?.page || 1)
const totalPages = computed(() => documentsStore.pagination?.pages || 1)

const handleClipboardUploaded = async () => {
  await documentsStore.fetchDocuments()
  await documentsStore.fetchStats()
}

const handlePaste = (e) => {
  // Only handle if no modal is open and not focused in an input
  if (showUploadModal.value || showClipboardModal.value || showPreview.value) return
  if (document.activeElement?.tagName === 'INPUT' ||
      document.activeElement?.tagName === 'TEXTAREA') return

  // Check if there's clipboard content
  if (e.clipboardData?.items?.length > 0) {
    e.preventDefault()
    showClipboardModal.value = true
  }
}

onMounted(async () => {
  await documentsStore.fetchDocuments()
  document.addEventListener('paste', handlePaste)
})

onUnmounted(() => {
  document.removeEventListener('paste', handlePaste)
})

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files || [])
  addFiles(files)
}

const addFiles = (files) => {
  const validFiles = files.filter(f =>
    f.type.startsWith('image/') ||
    f.type === 'application/pdf' ||
    f.type === 'text/plain' ||
    f.type === 'text/markdown' ||
    f.name.endsWith('.txt') ||
    f.name.endsWith('.md')
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

  // Check if any file is a PDF (needs streaming progress)
  const hasPdf = uploadFiles.value.some(f => f.type === 'application/pdf')

  try {
    if (hasPdf) {
      // Use streaming upload for PDFs to get page-by-page progress
      await documentsStore.uploadFilesWithProgress(uploadFiles.value, uploadCollection.value || undefined)
    } else {
      // Use regular upload for images/text files
      for (let i = 0; i < uploadFiles.value.length; i++) {
        await documentsStore.uploadFiles([uploadFiles.value[i]], uploadCollection.value || undefined)
        uploadProgress.value = Math.round(((i + 1) / uploadFiles.value.length) * 100)
      }
    }
    toastStore.success(`${uploadFiles.value.length}件のファイルをアップロードしました`)
  } catch (error) {
    console.error('Upload failed:', error)
    toastStore.error('アップロードに失敗しました')
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

// Check if document is a PDF file
const isPdf = (doc) => {
  return doc.mime_type === 'application/pdf' ||
         (doc.file_type === 'document' && doc.file_name?.toLowerCase().endsWith('.pdf'))
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
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-display font-bold text-text-primary">ライブラリ</h1>
        <p class="text-text-secondary text-sm mt-1">アップロードされたファイルを管理</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          v-if="documents.length > 0"
          @click="toggleSelectionMode"
          :class="[
            'btn flex items-center gap-2',
            isSelectionMode ? 'btn-primary' : 'btn-secondary'
          ]"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          {{ isSelectionMode ? '選択中' : '選択' }}
        </button>
        <button
          @click="showClipboardModal = true"
          class="btn btn-secondary flex items-center gap-2"
          title="クリップボードから貼り付け (Ctrl+V)"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          貼り付け
        </button>
        <button
          @click="showUploadModal = true"
          class="btn btn-primary flex items-center gap-2"
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
        class="flex items-center justify-between mb-6 p-4 bg-bg-secondary/80 backdrop-blur-sm border border-border/50 rounded-2xl"
      >
        <div class="flex items-center gap-4">
          <span class="text-text-secondary font-medium">
            <span class="text-accent">{{ selectedCount }}</span> 件選択中
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
            class="btn btn-danger flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            削除
          </button>
          <button
            @click="toggleSelectionMode"
            class="btn btn-ghost"
          >
            キャンセル
          </button>
        </div>
      </div>
    </Transition>

    <!-- Loading State -->
    <div v-if="isLoading && !documents.length" class="flex flex-col items-center justify-center py-20">
      <div class="relative w-16 h-16 mb-4">
        <div class="absolute inset-0 rounded-full border-2 border-accent/20"></div>
        <div class="absolute inset-0 rounded-full border-2 border-accent border-t-transparent animate-spin"></div>
      </div>
      <p class="text-text-muted">読み込み中...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!documents.length" class="text-center py-20">
      <div class="relative mx-auto w-24 h-24 mb-6">
        <div class="absolute inset-0 rounded-full bg-accent/5 animate-pulse"></div>
        <div class="relative flex items-center justify-center w-full h-full rounded-full bg-bg-tertiary/80 border border-border/50">
          <svg class="w-10 h-10 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        </div>
      </div>
      <h3 class="text-lg font-display font-semibold text-text-primary mb-2">ファイルがありません</h3>
      <p class="text-text-muted mb-6">最初のファイルをアップロードしましょう</p>
      <button
        @click="showUploadModal = true"
        class="btn btn-primary"
      >
        ファイルをアップロード
      </button>
    </div>

    <!-- Documents Grid -->
    <div v-else>
      <TransitionGroup
        tag="div"
        name="stagger-grid"
        class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5"
      >
        <div
          v-for="(doc, index) in documents"
          :key="doc.id"
          :style="{ '--stagger-delay': `${index * 40}ms` }"
          :class="[
            'group relative rounded-2xl overflow-hidden cursor-pointer',
            'bg-bg-secondary/60 backdrop-blur-sm border transition-all duration-300',
            isSelected(doc.id)
              ? 'border-accent ring-2 ring-accent/30 shadow-glow-accent'
              : 'border-border/30 hover:border-accent/40 hover:shadow-card-hover hover:-translate-y-1'
          ]"
          @click="handleCardClick(doc)"
        >
          <!-- Thumbnail -->
          <div class="aspect-square bg-bg-tertiary/50 relative overflow-hidden">
            <!-- PDF Icon for PDF files -->
            <div v-if="isPdf(doc)" class="w-full h-full flex items-center justify-center">
              <div class="relative">
                <svg class="w-16 h-16 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M14,2H6C4.9,2 4,2.9 4,4V20C4,21.1 4.9,22 6,22H18C19.1,22 20,21.1 20,20V8L14,2M18,20H6V4H13V9H18V20M10.92,12.31C10.68,11.54 10.15,9.08 11.55,9.04C12.95,9 12.03,12.16 12.03,12.16C12.42,13.65 14.05,14.72 14.05,14.72C14.55,14.57 17.4,14.24 17,15.72C16.57,17.2 13.5,15.81 13.5,15.81C11.55,15.95 10.09,16.47 10.09,16.47C8.96,18.58 7.64,19.5 7.1,18.61C6.43,17.5 9.23,16.07 9.23,16.07C10.68,13.72 10.92,12.31 10.92,12.31Z" />
                </svg>
                <span class="absolute -bottom-1 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-red-500 text-white text-xs font-bold rounded">
                  PDF
                </span>
              </div>
            </div>
            <!-- Regular thumbnail for images -->
            <img
              v-else-if="doc.thumbnail_path"
              :src="getFileUrl(doc.thumbnail_path)"
              :alt="doc.file_name"
              class="w-full h-full object-contain group-hover:scale-105 transition-transform duration-500 ease-smooth"
            />
            <!-- Generic icon for other files -->
            <div v-else class="w-full h-full flex items-center justify-center text-text-muted">
              <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>

            <!-- Selection Checkbox -->
            <Transition name="scale">
              <div
                v-if="isSelectionMode"
                class="absolute top-3 left-3 z-10"
                @click.stop="toggleSelect(doc.id)"
              >
                <div
                  :class="[
                    'w-7 h-7 rounded-lg border-2 flex items-center justify-center transition-all duration-200',
                    isSelected(doc.id)
                      ? 'bg-accent border-accent scale-110'
                      : 'bg-black/40 backdrop-blur-sm border-white/40 hover:border-white/60'
                  ]"
                >
                  <Transition name="scale">
                    <svg
                      v-if="isSelected(doc.id)"
                      class="w-4 h-4 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                    </svg>
                  </Transition>
                </div>
              </div>
            </Transition>

          </div>

          <!-- Info -->
          <div class="p-4">
            <p class="text-sm font-medium text-text-primary truncate mb-1" :title="doc.file_name">
              {{ doc.file_name }}
            </p>
            <div class="flex items-center justify-between">
              <span class="text-xs text-text-muted">{{ formatDate(doc.created_at) }}</span>
              <span class="text-xs text-text-muted font-mono">{{ formatFileSize(doc.file_size) }}</span>
            </div>
          </div>
        </div>
      </TransitionGroup>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-3 mt-10">
        <button
          @click="changePage(currentPage - 1)"
          :disabled="currentPage === 1"
          class="btn btn-ghost px-4"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div class="flex items-center gap-2">
          <span class="text-text-secondary">
            <span class="font-medium text-text-primary">{{ currentPage }}</span>
            <span class="text-text-muted mx-1">/</span>
            <span>{{ totalPages }}</span>
          </span>
        </div>

        <button
          @click="changePage(currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="btn btn-ghost px-4"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Upload Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showUploadModal"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          @click.self="showUploadModal = false"
        >
          <div class="modal-content w-full max-w-lg">
            <div class="relative">
              <!-- Glow effect -->
              <div class="absolute -inset-0.5 bg-gradient-to-r from-accent/20 via-accent/5 to-accent/20 rounded-3xl blur-lg opacity-50"></div>

              <div class="relative bg-bg-secondary border border-border/50 rounded-3xl shadow-2xl overflow-hidden">
                <!-- Header -->
                <div class="flex items-center justify-between p-6 border-b border-border/30">
                  <h3 class="text-lg font-display font-semibold text-text-primary">ファイルアップロード</h3>
                  <button
                    @click="showUploadModal = false"
                    class="p-2 hover:bg-bg-tertiary rounded-xl transition-colors"
                  >
                    <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <!-- Content -->
                <div class="p-6 space-y-5">
                  <!-- Drop Zone -->
                  <div
                    :class="[
                      'border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300 cursor-pointer',
                      isDragging
                        ? 'border-accent bg-accent/10 scale-[1.02]'
                        : 'border-border/50 hover:border-accent/50 hover:bg-accent/5'
                    ]"
                    @drop="handleDrop"
                    @dragover.prevent="isDragging = true"
                    @dragleave="isDragging = false"
                  >
                    <input
                      type="file"
                      multiple
                      accept="image/*,.pdf,.txt,.md"
                      class="hidden"
                      id="file-input"
                      @change="handleFileSelect"
                    />
                    <label for="file-input" class="cursor-pointer">
                      <div class="relative mx-auto w-16 h-16 mb-4">
                        <div class="absolute inset-0 rounded-full bg-accent/10 animate-ping-slow"></div>
                        <div class="relative flex items-center justify-center w-full h-full rounded-full bg-bg-tertiary border border-border/50">
                          <svg class="w-7 h-7 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                        </div>
                      </div>
                      <p class="text-text-primary font-medium mb-1">ファイルをドラッグ&ドロップ</p>
                      <p class="text-text-muted text-sm">またはクリックして選択</p>
                    </label>
                  </div>

                  <!-- Collection Select -->
                  <div>
                    <label class="block text-sm font-medium text-text-secondary mb-2">コレクション（任意）</label>
                    <select
                      v-model="uploadCollection"
                      class="input"
                    >
                      <option value="">コレクションなし</option>
                      <option v-for="col in collectionsStore.collections" :key="col.id" :value="col.id">
                        {{ col.name }}
                      </option>
                    </select>
                  </div>

                  <!-- File List -->
                  <div v-if="uploadFiles.length > 0" class="space-y-2 max-h-40 overflow-auto scrollbar-hidden">
                    <TransitionGroup name="list">
                      <div
                        v-for="(file, index) in uploadFiles"
                        :key="file.name + index"
                        class="flex items-center justify-between p-3 bg-bg-tertiary/50 border border-border/30 rounded-xl"
                      >
                        <div class="flex items-center gap-3 min-w-0">
                          <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                            <svg class="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <span class="text-sm text-text-secondary truncate">{{ file.name }}</span>
                        </div>
                        <button
                          @click="removeFile(index)"
                          class="p-1.5 hover:bg-bg-hover rounded-lg text-text-muted hover:text-error transition-colors"
                        >
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </TransitionGroup>
                  </div>

                  <!-- Progress -->
                  <div v-if="isUploading" class="space-y-3">
                    <div class="h-2 bg-bg-tertiary rounded-full overflow-hidden">
                      <div
                        class="h-full bg-gradient-to-r from-accent to-accent-hover transition-all duration-300 ease-smooth"
                        :style="{ width: (documentsStore.pdfProgress.isProcessing ? documentsStore.uploadProgress : uploadProgress) + '%' }"
                      ></div>
                    </div>

                    <div class="text-center">
                      <!-- PDF processing progress with page count -->
                      <template v-if="documentsStore.pdfProgress.isProcessing && documentsStore.pdfProgress.totalPages > 0">
                        <p class="text-sm text-text-secondary">
                          <span class="font-medium text-accent">
                            {{ documentsStore.pdfProgress.currentPage }}/{{ documentsStore.pdfProgress.totalPages }}
                          </span>
                          ページ処理中...
                        </p>
                        <p v-if="documentsStore.pdfProgress.message" class="text-xs text-text-muted mt-1">
                          {{ documentsStore.pdfProgress.message }}
                        </p>
                      </template>
                      <!-- Regular progress -->
                      <p v-else class="text-sm text-text-muted">
                        {{ documentsStore.pdfProgress.isProcessing ? documentsStore.uploadProgress : uploadProgress }}% 完了
                      </p>
                    </div>
                  </div>
                </div>

                <!-- Footer -->
                <div class="flex justify-end gap-3 p-6 border-t border-border/30 bg-bg-tertiary/30">
                  <button
                    @click="showUploadModal = false"
                    class="btn btn-ghost"
                  >
                    キャンセル
                  </button>
                  <button
                    @click="handleUpload"
                    :disabled="uploadFiles.length === 0 || isUploading"
                    class="btn btn-primary"
                  >
                    {{ isUploading ? 'アップロード中...' : 'アップロード' }}
                  </button>
                </div>
              </div>
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
      @prev="navigatePreview('prev')"
      @next="navigatePreview('next')"
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

    <!-- Clipboard Upload Modal -->
    <ClipboardUploadModal
      :show="showClipboardModal"
      @close="showClipboardModal = false"
      @uploaded="handleClipboardUploaded"
    />
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.scale-enter-active,
.scale-leave-active {
  transition: all 0.2s ease;
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

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
  transform: scale(0.95) translateY(10px);
}

.modal-leave-to .modal-content {
  opacity: 0;
  transform: scale(0.98);
}
</style>
