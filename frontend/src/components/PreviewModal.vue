<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import markedKatex from 'marked-katex-extension'
import 'katex/dist/katex.min.css'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'

// Configure marked with GFM line breaks and KaTeX math support
marked.use(markedKatex({
  throwOnError: false
}))
marked.setOptions({
  breaks: true  // Enable GFM line breaks (single newline = <br>)
})

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  document: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'delete'])

const toast = useToastStore()
const textContent = ref('')
const loading = ref(false)
const copied = ref(false)
const imageLoaded = ref(false)
const imageZoomed = ref(false)
const parentDocument = ref(null)
const showRenderedMarkdown = ref(true)

const isImage = computed(() => props.document?.file_type === 'image' || props.document?.metadata?.file_type === 'image')

const isPdf = computed(() => {
  const mimeType = props.document?.mime_type || props.document?.metadata?.mime_type
  const fileName = props.document?.file_name || props.document?.metadata?.file_name || ''
  return mimeType === 'application/pdf' || fileName.toLowerCase().endsWith('.pdf')
})

const isText = computed(() => {
  const type = props.document?.file_type || props.document?.metadata?.file_type
  // PDFs should not be treated as text
  if (isPdf.value) return false
  return type === 'text' || type === 'document'
})

const isMarkdown = computed(() => {
  const name = props.document?.file_name || props.document?.metadata?.file_name || ''
  return name.endsWith('.md') || name.endsWith('.markdown')
})

const isPdfPage = computed(() => {
  const parentId = props.document?.parent_document_id || props.document?.metadata?.parent_document_id
  return !!parentId
})

const fileName = computed(() => props.document?.file_name || props.document?.metadata?.file_name || 'Unknown')
const filePath = computed(() => {
  const path = props.document?.file_path || props.document?.metadata?.file_path
  if (!path) return ''
  const relativePath = path.replace(/^.*\/uploads\//, '')
  return `/files/${relativePath}`
})

const documentId = computed(() => props.document?.id)

const renderedMarkdown = computed(() => {
  if (!isMarkdown.value || !textContent.value) return ''
  return marked(textContent.value)
})

const parentFilePath = computed(() => {
  if (!parentDocument.value?.file_path) return ''
  const relativePath = parentDocument.value.file_path.replace(/^.*\/uploads\//, '')
  return `/files/${relativePath}`
})

watch(() => props.show, async (newVal) => {
  if (newVal) {
    // Reset state FIRST before loading data
    imageLoaded.value = false
    imageZoomed.value = false
    parentDocument.value = null
    showRenderedMarkdown.value = true

    // Then load data
    if (isText.value && documentId.value) {
      await loadTextContent()
    }
    if (isPdfPage.value) {
      await loadParentDocument()
    }
  }
})

const loadTextContent = async () => {
  loading.value = true
  try {
    const response = await api.get(`/documents/${documentId.value}/content`)
    textContent.value = response.data.content
  } catch (error) {
    console.error('Failed to load content:', error)
    textContent.value = 'Failed to load content'
    toast.error('コンテンツの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

const loadParentDocument = async () => {
  const parentId = props.document?.parent_document_id || props.document?.metadata?.parent_document_id
  if (!parentId) return

  try {
    const response = await api.get(`/documents/${parentId}`)
    parentDocument.value = response.data
  } catch (error) {
    console.error('Failed to load parent document:', error)
  }
}

const openOriginalPDF = () => {
  if (parentFilePath.value) {
    window.open(parentFilePath.value, '_blank')
  }
}

const openPdfFile = () => {
  if (filePath.value) {
    window.open(filePath.value, '_blank')
  }
}

const toggleMarkdownView = () => {
  showRenderedMarkdown.value = !showRenderedMarkdown.value
}

const copyContent = async () => {
  try {
    // Check if clipboard API is available (requires HTTPS or localhost)
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      await navigator.clipboard.writeText(textContent.value)
    } else {
      // Fallback for HTTP/non-secure contexts using execCommand
      const textarea = document.createElement('textarea')
      textarea.value = textContent.value
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      textarea.style.pointerEvents = 'none'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    copied.value = true
    toast.success('クリップボードにコピーしました')
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
    toast.error('コピーに失敗しました')
  }
}

const downloadFile = () => {
  const link = document.createElement('a')
  link.href = filePath.value
  link.download = fileName.value
  link.click()
  toast.success('ダウンロードを開始しました')
}

const toggleZoom = () => {
  imageZoomed.value = !imageZoomed.value
}

const handleKeydown = (e) => {
  if (!props.show) return

  if (e.key === 'Escape') {
    if (imageZoomed.value) {
      imageZoomed.value = false
    } else {
      emit('close')
    }
  }
  // Zoom with Z key
  if (e.key === 'z' && isImage.value && imageLoaded.value) {
    toggleZoom()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="imageZoomed ? (imageZoomed = false) : emit('close')"
      >
        <!-- Multi-layer Backdrop (clickable to close) -->
        <div
          class="absolute inset-0 cursor-pointer"
          @click="imageZoomed ? (imageZoomed = false) : emit('close')"
        >
          <div class="absolute inset-0 bg-black/80 backdrop-blur-md"></div>
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
        </div>

        <!-- Zoomed Image Overlay -->
        <Transition name="zoom">
          <div
            v-if="imageZoomed && isImage"
            class="absolute inset-0 z-[60] flex items-center justify-center cursor-zoom-out p-4"
            @click="imageZoomed = false"
          >
            <img
              :src="filePath"
              :alt="fileName"
              class="max-w-[95vw] max-h-[95vh] object-contain rounded-lg shadow-2xl"
            />
            <!-- Close hint -->
            <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-full bg-black/60 backdrop-blur-sm text-white/80 text-sm">
              <kbd class="px-1.5 py-0.5 rounded bg-white/20 text-xs font-mono">ESC</kbd>
              <span>または クリックで閉じる</span>
            </div>
          </div>
        </Transition>

        <!-- Modal Content -->
        <div
          class="modal-content relative w-full max-w-5xl max-h-[90vh] mx-4 flex flex-col rounded-2xl shadow-2xl overflow-hidden"
          :class="{ 'opacity-0 pointer-events-none': imageZoomed }"
          @click.stop
        >
          <!-- Glow effect -->
          <div class="absolute -inset-1 bg-gradient-to-r from-accent/20 via-accent/5 to-accent/20 rounded-3xl blur-xl opacity-50"></div>

          <!-- Main container -->
          <div class="relative bg-bg-secondary/95 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <!-- Subtle gradient overlay -->
            <div class="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none"></div>

            <!-- Header -->
            <div class="relative z-10 flex items-center justify-between px-5 py-4 border-b border-white/10 bg-bg-tertiary/50">
              <div class="flex items-center gap-3 min-w-0">
                <button
                  @click="emit('close')"
                  class="p-2 rounded-xl hover:bg-white/10 text-text-muted hover:text-text-primary active:scale-95 transition-all duration-200"
                  title="戻る (ESC)"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                </button>
                <div class="min-w-0">
                  <h3 class="text-text-primary font-display font-semibold truncate">{{ fileName }}</h3>
                  <p class="text-xs text-text-muted flex items-center gap-2">
                    <span>{{ isImage ? '画像' : isMarkdown ? 'Markdown' : isText ? 'テキスト' : 'ファイル' }}</span>
                    <span v-if="isPdfPage && parentDocument" class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-accent/10 text-accent text-xs">
                      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {{ parentDocument.file_name }}
                    </span>
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <!-- Keyboard hints -->
                <div class="hidden sm:flex items-center gap-2 mr-2 text-xs text-text-muted">
                  <kbd class="px-1.5 py-0.5 rounded bg-bg-tertiary border border-border/50 font-mono">ESC</kbd>
                  <span>閉じる</span>
                </div>
                <button
                  @click="emit('close')"
                  class="p-2 rounded-xl hover:bg-white/10 text-text-muted hover:text-text-primary active:scale-95 transition-all duration-200"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Content -->
            <div class="relative z-10 flex-1 overflow-auto p-6">
              <!-- Image Preview -->
              <div v-if="isImage" class="flex flex-col items-center justify-center min-h-[400px]">
                <!-- PDF Page Banner -->
                <div
                  v-if="isPdfPage && parentDocument"
                  class="w-full max-w-2xl mb-4 px-4 py-3 rounded-xl bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/20 backdrop-blur-sm"
                >
                  <div class="flex items-center justify-between gap-4">
                    <div class="flex items-center gap-3 min-w-0">
                      <div class="flex-shrink-0 w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                        <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M14,2H6C4.9,2 4,2.9 4,4V20C4,21.1 4.9,22 6,22H18C19.1,22 20,21.1 20,20V8L14,2M18,20H6V4H13V9H18V20M10.92,12.31C10.68,11.54 10.15,9.08 11.55,9.04C12.95,9 12.03,12.16 12.03,12.16C12.42,13.65 14.05,14.72 14.05,14.72C14.55,14.57 17.4,14.24 17,15.72C16.57,17.2 13.5,15.81 13.5,15.81C11.55,15.95 10.09,16.47 10.09,16.47C8.96,18.58 7.64,19.5 7.1,18.61C6.43,17.5 9.23,16.07 9.23,16.07C10.68,13.72 10.92,12.31 10.92,12.31Z" />
                        </svg>
                      </div>
                      <div class="min-w-0">
                        <p class="text-sm text-text-primary font-medium truncate">{{ parentDocument.file_name }}</p>
                        <p class="text-xs text-text-muted">PDFから抽出されたページ</p>
                      </div>
                    </div>
                    <button
                      @click="openOriginalPDF"
                      class="flex-shrink-0 px-4 py-2 rounded-lg bg-red-500/20 text-red-400 text-sm font-medium
                             hover:bg-red-500/30 hover:text-red-300 active:scale-95
                             transition-all duration-200 flex items-center gap-2"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      PDFを開く
                    </button>
                  </div>
                </div>

                <!-- Loading skeleton -->
                <div v-if="!imageLoaded" class="skeleton-shimmer bg-bg-tertiary rounded-xl w-full max-w-2xl h-[400px]"></div>

                <!-- Image with zoom capability -->
                <div
                  class="relative group cursor-zoom-in"
                  @click="toggleZoom"
                >
                  <img
                    :src="filePath"
                    :alt="fileName"
                    class="max-w-full max-h-[60vh] object-contain rounded-xl shadow-2xl transition-all duration-500"
                    :class="{ 'opacity-0 scale-95': !imageLoaded, 'opacity-100 scale-100': imageLoaded }"
                    @load="imageLoaded = true"
                  />
                  <!-- Zoom overlay hint -->
                  <div
                    v-if="imageLoaded"
                    class="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/30 rounded-xl transition-all duration-200"
                  >
                    <div class="opacity-0 group-hover:opacity-100 flex items-center gap-2 px-4 py-2 rounded-full bg-black/60 text-white text-sm transition-opacity">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                      </svg>
                      <span>クリックで拡大</span>
                      <kbd class="px-1.5 py-0.5 rounded bg-white/20 text-xs font-mono">Z</kbd>
                    </div>
                  </div>
                </div>
              </div>

              <!-- PDF Preview -->
              <div v-else-if="isPdf" class="flex flex-col items-center justify-center min-h-[400px]">
                <div class="text-center">
                  <div class="relative mx-auto w-24 h-24 mb-6">
                    <svg class="w-full h-full text-red-500" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M14,2H6C4.9,2 4,2.9 4,4V20C4,21.1 4.9,22 6,22H18C19.1,22 20,21.1 20,20V8L14,2M18,20H6V4H13V9H18V20M10.92,12.31C10.68,11.54 10.15,9.08 11.55,9.04C12.95,9 12.03,12.16 12.03,12.16C12.42,13.65 14.05,14.72 14.05,14.72C14.55,14.57 17.4,14.24 17,15.72C16.57,17.2 13.5,15.81 13.5,15.81C11.55,15.95 10.09,16.47 10.09,16.47C8.96,18.58 7.64,19.5 7.1,18.61C6.43,17.5 9.23,16.07 9.23,16.07C10.68,13.72 10.92,12.31 10.92,12.31Z" />
                    </svg>
                  </div>
                  <h4 class="text-lg font-display font-semibold text-text-primary mb-2">
                    {{ fileName }}
                  </h4>
                  <p class="text-text-muted mb-6">PDFファイル</p>
                  <button
                    @click="openPdfFile"
                    class="px-6 py-3 bg-accent text-bg-primary font-medium rounded-xl
                           hover:bg-accent-hover hover:shadow-glow-accent
                           active:scale-[0.98] transition-all duration-200
                           inline-flex items-center gap-2"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    PDFを新しいタブで開く
                  </button>
                </div>
              </div>

              <!-- Text/Document Preview -->
              <div v-else-if="isText" class="h-full">
                <div v-if="loading" class="flex items-center justify-center h-64">
                  <div class="relative">
                    <div class="w-12 h-12 border-2 border-accent/30 rounded-full"></div>
                    <div class="absolute inset-0 w-12 h-12 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
                  </div>
                </div>
                <div v-else class="relative">
                  <!-- Markdown toggle button -->
                  <div v-if="isMarkdown" class="flex justify-end mb-2">
                    <button
                      @click="toggleMarkdownView"
                      class="px-3 py-1.5 text-xs rounded-lg bg-bg-tertiary/80 border border-white/10 text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
                    >
                      {{ showRenderedMarkdown ? 'ソースを表示' : 'レンダリング表示' }}
                    </button>
                  </div>

                  <!-- Markdown Rendered View -->
                  <div
                    v-if="isMarkdown && showRenderedMarkdown"
                    class="markdown-content bg-bg-tertiary/50 backdrop-blur-sm border border-white/5 rounded-xl p-5 overflow-auto max-h-[60vh] text-sm text-text-secondary prose prose-invert prose-sm max-w-none"
                    v-html="renderedMarkdown"
                  ></div>

                  <!-- Plain Text View -->
                  <pre
                    v-else
                    class="bg-bg-tertiary/50 backdrop-blur-sm border border-white/5 rounded-xl p-5 overflow-auto max-h-[60vh] text-sm text-text-secondary font-mono whitespace-pre-wrap break-words leading-relaxed"
                  >{{ textContent }}</pre>

                  <!-- Line count -->
                  <div class="absolute bottom-2 right-2 px-2 py-1 rounded-lg bg-bg-primary/80 text-xs text-text-muted">
                    {{ textContent.split('\n').length }} 行
                  </div>
                </div>
              </div>

              <!-- Unsupported Type -->
              <div v-else class="flex flex-col items-center justify-center h-64 text-text-muted">
                <div class="relative mb-6">
                  <div class="absolute inset-0 rounded-full bg-accent/10 animate-ping-slow"></div>
                  <div class="relative w-20 h-20 flex items-center justify-center rounded-2xl bg-gradient-to-br from-bg-tertiary to-bg-secondary border border-white/10">
                    <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
                <p class="text-lg font-display font-semibold text-text-primary mb-1">プレビュー不可</p>
                <p class="text-text-muted text-sm">このファイル形式はプレビューできません</p>
              </div>
            </div>

            <!-- Footer Actions -->
            <div class="relative z-10 flex items-center justify-between px-5 py-4 border-t border-white/10 bg-bg-tertiary/50">
              <!-- Delete Button -->
              <button
                @click="emit('delete', documentId)"
                class="action-btn action-btn-danger group"
                title="削除"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span class="action-btn-tooltip">削除</span>
              </button>

              <!-- Right Actions -->
              <div class="flex items-center gap-2">
                <!-- Open Original PDF Button -->
                <button
                  v-if="isPdfPage && parentDocument"
                  @click="openOriginalPDF"
                  class="action-btn action-btn-accent group"
                  title="元のPDFを開く"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span class="action-btn-tooltip">元のPDFを開く</span>
                </button>
                <!-- Copy Button -->
                <button
                  v-if="isText"
                  @click="copyContent"
                  class="action-btn group"
                  :class="copied ? 'action-btn-success' : ''"
                  title="コピー"
                >
                  <svg v-if="!copied" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span class="action-btn-tooltip">{{ copied ? 'コピーしました' : 'コピー' }}</span>
                </button>
                <!-- Download Button -->
                <button
                  @click="downloadFile"
                  class="action-btn action-btn-accent group"
                  title="ダウンロード"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span class="action-btn-tooltip">ダウンロード</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active {
  transition: opacity 0.3s ease-out;
}

.modal-leave-active {
  transition: opacity 0.2s ease-in;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease-out;
}

.modal-leave-active .modal-content {
  transition: transform 0.25s ease-in, opacity 0.2s ease-in;
}

.modal-enter-from .modal-content {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}

.modal-leave-to .modal-content {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

/* Zoom transitions */
.zoom-enter-active {
  transition: opacity 0.3s ease-out;
}

.zoom-leave-active {
  transition: opacity 0.2s ease-in;
}

.zoom-enter-from,
.zoom-leave-to {
  opacity: 0;
}

.zoom-enter-active img {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.zoom-leave-active img {
  transition: transform 0.25s ease-in;
}

.zoom-enter-from img {
  transform: scale(0.8);
}

.zoom-leave-to img {
  transform: scale(0.9);
}

/* Action Button Base */
.action-btn {
  @apply relative p-3 rounded-xl text-text-muted bg-white/5 backdrop-blur-sm border border-white/10
         hover:text-text-primary hover:bg-white/10 hover:border-white/20
         active:scale-95 transition-all duration-200;
}

.action-btn-danger {
  @apply text-error/70 hover:text-error hover:bg-error/10 hover:border-error/30;
}

.action-btn-accent {
  @apply text-accent/80 hover:text-accent hover:bg-accent/10 hover:border-accent/30;
}

.action-btn-success {
  @apply text-success bg-success/10 border-success/30;
}

/* Tooltip */
.action-btn-tooltip {
  @apply absolute -top-10 left-1/2 -translate-x-1/2 px-2.5 py-1.5 rounded-lg
         bg-bg-primary/95 backdrop-blur-sm border border-white/10
         text-xs text-text-primary font-medium whitespace-nowrap
         opacity-0 invisible group-hover:opacity-100 group-hover:visible
         transition-all duration-200 pointer-events-none
         shadow-lg;
}

.action-btn-tooltip::after {
  content: '';
  @apply absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2
         bg-bg-primary/95 border-r border-b border-white/10
         rotate-45;
}

/* Markdown Content Styles - use :deep() for v-html content */
.markdown-content {
  line-height: 1.7;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  @apply text-text-primary font-display font-semibold mt-6 mb-3;
}

.markdown-content :deep(h1) { @apply text-2xl; }
.markdown-content :deep(h2) { @apply text-xl; }
.markdown-content :deep(h3) { @apply text-lg; }

.markdown-content :deep(p) {
  @apply mb-4;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  @apply ml-6 mb-4;
}

.markdown-content :deep(ul) { @apply list-disc; }
.markdown-content :deep(ol) { @apply list-decimal; }

.markdown-content :deep(li) {
  @apply mb-1;
}

.markdown-content :deep(code) {
  @apply px-1.5 py-0.5 rounded bg-bg-primary/50 font-mono text-xs text-accent;
}

.markdown-content :deep(pre) {
  @apply p-4 rounded-lg bg-bg-primary/50 overflow-auto mb-4;
}

.markdown-content :deep(pre) code {
  @apply p-0 bg-transparent;
}

.markdown-content :deep(blockquote) {
  @apply pl-4 border-l-2 border-accent/50 italic text-text-muted mb-4;
}

.markdown-content :deep(a) {
  @apply text-accent hover:underline;
}

.markdown-content :deep(table) {
  @apply w-full border-collapse mb-4;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  @apply border border-border/30 px-3 py-2 text-left;
}

.markdown-content :deep(th) {
  @apply bg-bg-tertiary/50 font-semibold;
}

.markdown-content :deep(hr) {
  @apply border-border/30 my-6;
}
</style>
