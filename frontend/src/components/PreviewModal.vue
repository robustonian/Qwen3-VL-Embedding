<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '@/api/client'
import { useToastStore } from '@/stores/toast'

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

const isImage = computed(() => props.document?.file_type === 'image' || props.document?.metadata?.file_type === 'image')
const isText = computed(() => {
  const type = props.document?.file_type || props.document?.metadata?.file_type
  return type === 'text' || type === 'document'
})

const fileName = computed(() => props.document?.file_name || props.document?.metadata?.file_name || 'Unknown')
const filePath = computed(() => {
  const path = props.document?.file_path || props.document?.metadata?.file_path
  if (!path) return ''
  const relativePath = path.replace(/^.*\/uploads\//, '')
  return `/files/${relativePath}`
})

const documentId = computed(() => props.document?.id)

watch(() => props.show, async (newVal) => {
  if (newVal && isText.value && documentId.value) {
    await loadTextContent()
  }
  if (newVal) {
    imageLoaded.value = false
    imageZoomed.value = false
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

const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(textContent.value)
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
        <!-- Multi-layer Backdrop -->
        <div class="absolute inset-0">
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
                  <p class="text-xs text-text-muted">
                    {{ isImage ? '画像' : isText ? 'テキスト' : 'ファイル' }}
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

              <!-- Text/Document Preview -->
              <div v-else-if="isText" class="h-full">
                <div v-if="loading" class="flex items-center justify-center h-64">
                  <div class="relative">
                    <div class="w-12 h-12 border-2 border-accent/30 rounded-full"></div>
                    <div class="absolute inset-0 w-12 h-12 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
                  </div>
                </div>
                <div v-else class="relative">
                  <pre class="bg-bg-tertiary/50 backdrop-blur-sm border border-white/5 rounded-xl p-5 overflow-auto max-h-[60vh] text-sm text-text-secondary font-mono whitespace-pre-wrap break-words leading-relaxed">{{ textContent }}</pre>
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
                class="btn-danger-ghost flex items-center gap-2"
                title="削除"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                削除
              </button>

              <!-- Right Actions -->
              <div class="flex items-center gap-3">
                <button
                  v-if="isText"
                  @click="copyContent"
                  class="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 active:scale-[0.98]"
                  :class="copied
                    ? 'bg-success/20 text-success border border-success/30'
                    : 'btn-secondary'"
                >
                  <svg v-if="!copied" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  {{ copied ? 'コピーしました' : 'コピー' }}
                </button>
                <button
                  @click="downloadFile"
                  class="btn-primary flex items-center gap-2"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  ダウンロード
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

/* Button variant for ghost danger */
.btn-danger-ghost {
  @apply px-4 py-2.5 rounded-xl text-sm font-medium text-error/80 hover:text-error hover:bg-error/10 active:scale-[0.98] transition-all duration-200;
}
</style>
