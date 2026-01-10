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

const emit = defineEmits(['close'])

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
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm"></div>

        <!-- Modal Content -->
        <div class="relative w-full max-w-5xl max-h-[90vh] mx-4 flex flex-col bg-bg-secondary rounded-xl shadow-2xl overflow-hidden">
          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-border bg-bg-tertiary">
            <div class="flex items-center gap-3 min-w-0">
              <button
                @click="emit('close')"
                class="p-1.5 rounded-lg hover:bg-bg-primary text-text-muted hover:text-text-primary transition-colors"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <h3 class="text-text-primary font-medium truncate">{{ fileName }}</h3>
            </div>
            <button
              @click="emit('close')"
              class="p-1.5 rounded-lg hover:bg-bg-primary text-text-muted hover:text-text-primary transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-auto p-4">
            <!-- Image Preview -->
            <div v-if="isImage" class="flex items-center justify-center min-h-[400px]">
              <div v-if="!imageLoaded" class="animate-pulse bg-bg-tertiary rounded-lg w-full h-[400px]"></div>
              <img
                :src="filePath"
                :alt="fileName"
                class="max-w-full max-h-[70vh] object-contain rounded-lg shadow-lg"
                :class="{ 'hidden': !imageLoaded }"
                @load="imageLoaded = true"
              />
            </div>

            <!-- Text/Document Preview -->
            <div v-else-if="isText" class="h-full">
              <div v-if="loading" class="flex items-center justify-center h-64">
                <div class="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full"></div>
              </div>
              <div v-else class="relative">
                <pre class="bg-bg-tertiary rounded-lg p-4 overflow-auto max-h-[60vh] text-sm text-text-secondary font-mono whitespace-pre-wrap break-words">{{ textContent }}</pre>
              </div>
            </div>

            <!-- Unsupported Type -->
            <div v-else class="flex flex-col items-center justify-center h-64 text-text-muted">
              <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>このファイル形式はプレビューできません</p>
            </div>
          </div>

          <!-- Footer Actions -->
          <div class="flex items-center justify-end gap-3 px-4 py-3 border-t border-border bg-bg-tertiary">
            <button
              v-if="isText"
              @click="copyContent"
              class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="copied ? 'bg-green-500/20 text-green-400' : 'bg-bg-primary hover:bg-bg-secondary text-text-secondary hover:text-text-primary'"
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
              class="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              ダウンロード
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.2s ease;
}

.modal-enter-from .relative {
  transform: scale(0.95);
}

.modal-leave-to .relative {
  transform: scale(0.95);
}
</style>
