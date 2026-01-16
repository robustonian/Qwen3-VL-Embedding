<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'uploaded'])

const documentsStore = useDocumentsStore()
const toastStore = useToastStore()

const clipboardType = ref(null) // 'text' | 'image'
const textContent = ref('')
const imageData = ref(null)
const imagePreview = ref(null)
const fileName = ref('')
const isUploading = ref(false)
const isLoading = ref(false)
const needsManualPaste = ref(false)
const pasteAreaRef = ref(null)

const canUpload = computed(() => {
  if (clipboardType.value === 'text') {
    return textContent.value.trim().length > 0 && fileName.value.trim().length > 0
  }
  if (clipboardType.value === 'image') {
    return imageData.value !== null && fileName.value.trim().length > 0
  }
  return false
})

// Handle paste event (works on HTTP without clipboard API)
const handlePaste = (e) => {
  const items = e.clipboardData?.items
  if (!items) return

  for (const item of items) {
    // Check for image
    if (item.type.startsWith('image/')) {
      const blob = item.getAsFile()
      if (blob) {
        imageData.value = blob
        clipboardType.value = 'image'
        needsManualPaste.value = false

        // Create preview URL
        if (imagePreview.value) {
          URL.revokeObjectURL(imagePreview.value)
        }
        imagePreview.value = URL.createObjectURL(blob)

        // Generate default filename
        const ext = item.type.split('/')[1] || 'png'
        fileName.value = `clipboard_${Date.now()}.${ext}`
        return
      }
    }

    // Check for text
    if (item.type === 'text/plain') {
      item.getAsString((text) => {
        if (text) {
          textContent.value = text
          clipboardType.value = 'text'
          needsManualPaste.value = false
          fileName.value = `clipboard_${Date.now()}.txt`
        }
      })
      return
    }
  }
}

const readClipboard = async () => {
  isLoading.value = true
  clipboardType.value = null
  textContent.value = ''
  imageData.value = null
  needsManualPaste.value = false

  // Check if clipboard API is available (requires HTTPS or localhost)
  if (!navigator.clipboard || typeof navigator.clipboard.read !== 'function') {
    // Clipboard API not available, show manual paste prompt
    needsManualPaste.value = true
    isLoading.value = false
    return
  }

  try {
    const items = await navigator.clipboard.read()

    for (const item of items) {
      // Check for image types
      const imageType = item.types.find(t => t.startsWith('image/'))
      if (imageType) {
        const blob = await item.getType(imageType)
        imageData.value = blob
        clipboardType.value = 'image'

        // Create preview URL
        if (imagePreview.value) {
          URL.revokeObjectURL(imagePreview.value)
        }
        imagePreview.value = URL.createObjectURL(blob)

        // Generate default filename
        const ext = imageType.split('/')[1] || 'png'
        fileName.value = `clipboard_${Date.now()}.${ext}`
        isLoading.value = false
        return
      }

      // Check for text
      if (item.types.includes('text/plain')) {
        const blob = await item.getType('text/plain')
        textContent.value = await blob.text()
        clipboardType.value = 'text'
        fileName.value = `clipboard_${Date.now()}.txt`
        isLoading.value = false
        return
      }
    }

    // Fallback to readText for simple text
    const text = await navigator.clipboard.readText()
    if (text) {
      textContent.value = text
      clipboardType.value = 'text'
      fileName.value = `clipboard_${Date.now()}.txt`
    }
  } catch (error) {
    console.error('Failed to read clipboard:', error)
    // Show manual paste prompt as fallback
    needsManualPaste.value = true
  }

  isLoading.value = false
}

const handleUpload = async () => {
  if (!canUpload.value) return

  isUploading.value = true

  try {
    let file
    if (clipboardType.value === 'text') {
      file = new File([textContent.value], fileName.value, { type: 'text/plain' })
    } else if (clipboardType.value === 'image') {
      file = new File([imageData.value], fileName.value, { type: imageData.value.type })
    }

    await documentsStore.uploadFiles([file])
    toastStore.success('クリップボードからアップロードしました')
    emit('uploaded')
    handleClose()
  } catch (error) {
    console.error('Upload failed:', error)
    toastStore.error('アップロードに失敗しました')
  } finally {
    isUploading.value = false
  }
}

const handleClose = () => {
  clipboardType.value = null
  textContent.value = ''
  imageData.value = null
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value)
  }
  imagePreview.value = null
  fileName.value = ''
  isLoading.value = false
  needsManualPaste.value = false
  emit('close')
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    readClipboard()
  }
})

// Keyboard handler
const handleKeydown = (e) => {
  if (!props.show) return
  if (e.key === 'Escape') {
    handleClose()
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
                  クリップボードからアップロード
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
              <div class="p-6 space-y-5">
                <!-- Loading state -->
                <div v-if="isLoading" class="flex flex-col items-center py-8">
                  <div class="w-12 h-12 border-2 border-accent/30 border-t-accent rounded-full animate-spin mb-4"></div>
                  <p class="text-text-muted">クリップボードを読み取り中...</p>
                </div>

                <!-- Manual paste prompt (for HTTP/non-secure context) -->
                <div v-else-if="needsManualPaste" class="space-y-4">
                  <div
                    ref="pasteAreaRef"
                    class="flex flex-col items-center py-12 px-6 rounded-xl border-2 border-dashed border-accent/30 bg-accent/5 cursor-text focus:outline-none focus:border-accent focus:bg-accent/10 transition-colors"
                    tabindex="0"
                    @paste="handlePaste"
                    @click="pasteAreaRef?.focus()"
                  >
                    <svg class="w-12 h-12 text-accent/60 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p class="text-text-primary font-medium mb-2">ここをクリックしてから</p>
                    <div class="flex items-center gap-2 text-accent">
                      <kbd class="px-2 py-1 rounded bg-bg-tertiary border border-border/50 text-sm font-mono">Ctrl</kbd>
                      <span>+</span>
                      <kbd class="px-2 py-1 rounded bg-bg-tertiary border border-border/50 text-sm font-mono">V</kbd>
                    </div>
                    <p class="text-text-muted text-sm mt-2">で貼り付けてください</p>
                  </div>
                  <p class="text-xs text-text-muted text-center">
                    HTTPアクセスのため、自動読み取りは利用できません
                  </p>
                </div>

                <!-- Text preview -->
                <div v-else-if="clipboardType === 'text'" class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-text-secondary mb-2">ファイル名</label>
                    <input
                      v-model="fileName"
                      type="text"
                      class="input"
                      placeholder="ファイル名を入力"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-text-secondary mb-2">
                      テキスト内容 (編集可能)
                    </label>
                    <textarea
                      v-model="textContent"
                      rows="8"
                      class="input font-mono text-sm resize-none"
                      placeholder="テキスト内容"
                    ></textarea>
                  </div>
                  <p class="text-xs text-text-muted">
                    {{ textContent.length }} 文字
                  </p>
                </div>

                <!-- Image preview -->
                <div v-else-if="clipboardType === 'image'" class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-text-secondary mb-2">ファイル名</label>
                    <input
                      v-model="fileName"
                      type="text"
                      class="input"
                      placeholder="ファイル名を入力"
                    />
                  </div>
                  <div class="relative rounded-xl overflow-hidden bg-bg-tertiary/50 border border-border/30">
                    <img
                      v-if="imagePreview"
                      :src="imagePreview"
                      alt="Clipboard image"
                      class="max-h-64 mx-auto object-contain"
                    />
                  </div>
                </div>

                <!-- Empty clipboard state -->
                <div v-else class="flex flex-col items-center py-8">
                  <svg class="w-16 h-16 text-text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <p class="text-text-secondary">クリップボードにデータがありません</p>
                  <p class="text-text-muted text-sm mt-1">テキストまたは画像をコピーしてください</p>
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
                  @click="handleUpload"
                  :disabled="!canUpload || isUploading"
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
