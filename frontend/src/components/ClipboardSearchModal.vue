<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'search'])

const toastStore = useToastStore()

const imageData = ref(null)
const imagePreview = ref(null)
const isLoading = ref(false)
const needsManualPaste = ref(false)
const pasteAreaRef = ref(null)

const canSearch = computed(() => imageData.value !== null)

// Handle paste event (works on HTTP without clipboard API)
const handlePaste = (e) => {
  const items = e.clipboardData?.items
  if (!items) return

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const blob = item.getAsFile()
      if (blob) {
        imageData.value = blob
        needsManualPaste.value = false

        if (imagePreview.value) {
          URL.revokeObjectURL(imagePreview.value)
        }
        imagePreview.value = URL.createObjectURL(blob)
        return
      }
    }
  }

  // No image found in paste
  toastStore.info('クリップボードに画像がありません')
}

const readClipboard = async () => {
  isLoading.value = true
  imageData.value = null
  needsManualPaste.value = false

  // Check if clipboard API is available (requires HTTPS or localhost)
  if (!navigator.clipboard || typeof navigator.clipboard.read !== 'function') {
    needsManualPaste.value = true
    isLoading.value = false
    return
  }

  try {
    const items = await navigator.clipboard.read()

    for (const item of items) {
      const imageType = item.types.find(t => t.startsWith('image/'))
      if (imageType) {
        const blob = await item.getType(imageType)
        imageData.value = blob

        if (imagePreview.value) {
          URL.revokeObjectURL(imagePreview.value)
        }
        imagePreview.value = URL.createObjectURL(blob)
        isLoading.value = false
        return
      }
    }

    // No image found
    toastStore.info('クリップボードに画像がありません')
  } catch (error) {
    console.error('Failed to read clipboard:', error)
    // Show manual paste prompt as fallback
    needsManualPaste.value = true
  }

  isLoading.value = false
}

const handleSearch = async () => {
  if (!canSearch.value) return

  // Convert blob to File for the search API
  const ext = imageData.value.type.split('/')[1] || 'png'
  const file = new File([imageData.value], `clipboard_search.${ext}`, { type: imageData.value.type })
  emit('search', file)
  handleClose()
}

const handleClose = () => {
  imageData.value = null
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value)
  }
  imagePreview.value = null
  isLoading.value = false
  needsManualPaste.value = false
  emit('close')
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    readClipboard()
  }
})

const handleKeydown = (e) => {
  if (!props.show) return
  if (e.key === 'Escape') {
    handleClose()
  }
  if (e.key === 'Enter' && canSearch.value) {
    handleSearch()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="handleClose"
      >
        <div class="modal-content w-full max-w-lg">
          <div class="relative">
            <!-- Glow effect -->
            <div class="absolute -inset-0.5 bg-gradient-to-r from-accent/20 via-accent/5 to-accent/20 rounded-3xl blur-lg opacity-50"></div>

            <div class="relative bg-bg-secondary border border-border/50 rounded-3xl shadow-2xl overflow-hidden">
              <!-- Header -->
              <div class="flex items-center justify-between p-6 border-b border-border/30">
                <h3 class="text-lg font-display font-semibold text-text-primary">
                  クリップボード画像で検索
                </h3>
                <button
                  @click="handleClose"
                  class="p-2 hover:bg-bg-tertiary rounded-xl transition-colors"
                >
                  <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <!-- Content -->
              <div class="p-6">
                <!-- Loading state -->
                <div v-if="isLoading" class="flex flex-col items-center py-8">
                  <div class="w-12 h-12 border-2 border-accent/30 border-t-accent rounded-full animate-spin mb-4"></div>
                  <p class="text-text-muted">クリップボードを読み取り中...</p>
                </div>

                <!-- Manual paste prompt (for HTTP/non-secure context) -->
                <div v-else-if="needsManualPaste && !imagePreview" class="space-y-4">
                  <div
                    ref="pasteAreaRef"
                    class="flex flex-col items-center py-12 px-6 rounded-xl border-2 border-dashed border-accent/30 bg-accent/5 cursor-text focus:outline-none focus:border-accent focus:bg-accent/10 transition-colors"
                    tabindex="0"
                    @paste="handlePaste"
                    @click="pasteAreaRef?.focus()"
                  >
                    <svg class="w-12 h-12 text-accent/60 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p class="text-text-primary font-medium mb-2">ここをクリックしてから</p>
                    <div class="flex items-center gap-2 text-accent">
                      <kbd class="px-2 py-1 rounded bg-bg-tertiary border border-border/50 text-sm font-mono">Ctrl</kbd>
                      <span>+</span>
                      <kbd class="px-2 py-1 rounded bg-bg-tertiary border border-border/50 text-sm font-mono">V</kbd>
                    </div>
                    <p class="text-text-muted text-sm mt-2">で画像を貼り付けてください</p>
                  </div>
                  <p class="text-xs text-text-muted text-center">
                    HTTPアクセスのため、自動読み取りは利用できません
                  </p>
                </div>

                <!-- Image preview -->
                <div v-else-if="imagePreview" class="space-y-4">
                  <div class="relative rounded-xl overflow-hidden bg-bg-tertiary/50 border border-border/30">
                    <img
                      :src="imagePreview"
                      alt="Clipboard image"
                      class="max-h-64 mx-auto object-contain"
                    />
                  </div>
                  <p class="text-sm text-text-muted text-center">
                    この画像で類似ドキュメントを検索します
                  </p>
                </div>

                <!-- No image state -->
                <div v-else class="flex flex-col items-center py-8">
                  <svg class="w-16 h-16 text-text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p class="text-text-secondary">クリップボードに画像がありません</p>
                  <p class="text-text-muted text-sm mt-1">画像をコピーしてから再度お試しください</p>
                </div>
              </div>

              <!-- Footer -->
              <div class="flex justify-end gap-3 p-6 border-t border-border/30 bg-bg-tertiary/30">
                <button
                  @click="handleClose"
                  class="btn btn-ghost"
                >
                  キャンセル
                </button>
                <button
                  @click="handleSearch"
                  :disabled="!canSearch"
                  class="btn btn-primary flex items-center gap-2"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  検索
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
