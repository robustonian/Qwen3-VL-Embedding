<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '@/api/client'

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

const textContent = ref('')
const loading = ref(false)
const copied = ref(false)
const imageLoaded = ref(false)

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
  } finally {
    loading.value = false
  }
}

const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(textContent.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

const downloadFile = () => {
  const link = document.createElement('a')
  link.href = filePath.value
  link.download = fileName.value
  link.click()
}

const handleKeydown = (e) => {
  if (e.key === 'Escape' && props.show) {
    emit('close')
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
        @click.self="emit('close')"
      >
        <!-- Multi-layer Backdrop -->
        <div class="absolute inset-0">
          <div class="absolute inset-0 bg-black/70 backdrop-blur-md"></div>
          <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent"></div>
        </div>

        <!-- Modal Content with Glass Effect -->
        <div class="modal-content relative w-full max-w-5xl max-h-[90vh] mx-4 flex flex-col
                    rounded-2xl shadow-2xl overflow-hidden
                    bg-bg-secondary/95 backdrop-blur-xl border border-white/10">
          <!-- Subtle gradient overlay -->
          <div class="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none"></div>

          <!-- Header -->
          <div class="relative z-10 flex items-center justify-between px-5 py-4 border-b border-white/10 bg-bg-tertiary/50">
            <div class="flex items-center gap-3 min-w-0">
              <button
                @click="emit('close')"
                class="p-2 rounded-xl hover:bg-white/10 text-text-muted hover:text-text-primary
                       active:scale-95 transition-all duration-200"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <h3 class="text-text-primary font-medium truncate">{{ fileName }}</h3>
            </div>
            <button
              @click="emit('close')"
              class="p-2 rounded-xl hover:bg-white/10 text-text-muted hover:text-text-primary
                     active:scale-95 transition-all duration-200"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Content -->
          <div class="relative z-10 flex-1 overflow-auto p-6">
            <!-- Image Preview -->
            <div v-if="isImage" class="flex items-center justify-center min-h-[400px]">
              <div v-if="!imageLoaded" class="skeleton-shimmer bg-bg-tertiary rounded-xl w-full h-[400px]"></div>
              <img
                :src="filePath"
                :alt="fileName"
                class="max-w-full max-h-[70vh] object-contain rounded-xl shadow-2xl
                       transition-all duration-500"
                :class="{ 'opacity-0 scale-95': !imageLoaded, 'opacity-100 scale-100': imageLoaded }"
                @load="imageLoaded = true"
              />
            </div>

            <!-- Text/Document Preview -->
            <div v-else-if="isText" class="h-full">
              <div v-if="loading" class="flex items-center justify-center h-64">
                <div class="relative">
                  <div class="w-10 h-10 border-2 border-accent/30 rounded-full"></div>
                  <div class="absolute inset-0 w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
                </div>
              </div>
              <div v-else class="relative">
                <pre class="bg-bg-tertiary/50 backdrop-blur-sm border border-white/5 rounded-xl p-5 overflow-auto max-h-[60vh] text-sm text-text-secondary font-mono whitespace-pre-wrap break-words">{{ textContent }}</pre>
              </div>
            </div>

            <!-- Unsupported Type -->
            <div v-else class="flex flex-col items-center justify-center h-64 text-text-muted">
              <div class="relative mb-6">
                <div class="absolute inset-0 rounded-full bg-accent/10 animate-ping-slow"></div>
                <div class="relative w-20 h-20 flex items-center justify-center rounded-full bg-bg-tertiary border border-white/10">
                  <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
              <p class="text-lg font-medium text-text-primary mb-1">プレビュー不可</p>
              <p class="text-text-muted">このファイル形式はプレビューできません</p>
            </div>
          </div>

          <!-- Footer Actions -->
          <div class="relative z-10 flex items-center justify-between px-5 py-4 border-t border-white/10 bg-bg-tertiary/50">
            <!-- Delete Button -->
            <button
              @click="emit('delete', documentId)"
              class="btn-delete flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                     text-red-400 hover:text-red-300 hover:bg-red-500/10
                     active:scale-[0.98] transition-all duration-200"
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
                class="btn-action relative overflow-hidden flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                       active:scale-[0.98] transition-all duration-200"
                :class="copied
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'bg-bg-primary/50 hover:bg-white/10 text-text-secondary hover:text-text-primary border border-white/10'"
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
                class="btn-primary relative overflow-hidden flex items-center gap-2 px-5 py-2.5
                       bg-accent text-white rounded-xl text-sm font-medium
                       hover:bg-accent-hover hover:shadow-lg hover:shadow-accent/25
                       active:scale-[0.98] transition-all duration-200"
              >
                <!-- Shine effect -->
                <span class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent
                            -translate-x-full hover:translate-x-full transition-transform duration-700"></span>
                <svg class="relative z-10 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span class="relative z-10">ダウンロード</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Use global modal transitions from main.css */

/* Fallback scoped transitions */
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
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.3s ease-out;
}

.modal-leave-active .modal-content {
  transition: transform 0.25s ease-in,
              opacity 0.2s ease-in;
}

.modal-enter-from .modal-content {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}

.modal-leave-to .modal-content {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

/* Button shine on hover */
.btn-primary:hover span:first-child {
  transform: translateX(100%);
}
</style>
