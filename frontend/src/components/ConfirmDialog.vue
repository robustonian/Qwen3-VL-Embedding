<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '確認'
  },
  message: {
    type: String,
    default: 'この操作を実行しますか？'
  },
  confirmText: {
    type: String,
    default: '確認'
  },
  cancelText: {
    type: String,
    default: 'キャンセル'
  },
  type: {
    type: String,
    default: 'danger', // 'danger' | 'warning' | 'info'
    validator: (value) => ['danger', 'warning', 'info'].includes(value)
  }
})

const emit = defineEmits(['confirm', 'cancel'])

const iconColor = computed(() => {
  switch (props.type) {
    case 'danger': return 'text-red-500'
    case 'warning': return 'text-yellow-500'
    case 'info': return 'text-blue-500'
    default: return 'text-red-500'
  }
})

const confirmButtonClass = computed(() => {
  switch (props.type) {
    case 'danger': return 'bg-red-500 hover:bg-red-600'
    case 'warning': return 'bg-yellow-500 hover:bg-yellow-600'
    case 'info': return 'bg-blue-500 hover:bg-blue-600'
    default: return 'bg-red-500 hover:bg-red-600'
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div
        v-if="show"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
        @click.self="emit('cancel')"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>

        <!-- Dialog -->
        <div class="relative w-full max-w-md bg-bg-secondary border border-border rounded-xl shadow-2xl overflow-hidden">
          <!-- Content -->
          <div class="p-6">
            <div class="flex items-start gap-4">
              <!-- Icon -->
              <div :class="['flex-shrink-0 w-10 h-10 rounded-full bg-bg-tertiary flex items-center justify-center', iconColor]">
                <svg v-if="type === 'danger'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <svg v-else-if="type === 'warning'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <!-- Text -->
              <div class="flex-1 min-w-0">
                <h3 class="text-lg font-semibold text-text-primary">{{ title }}</h3>
                <p class="mt-2 text-sm text-text-secondary">{{ message }}</p>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end gap-3 px-6 py-4 bg-bg-tertiary border-t border-border">
            <button
              @click="emit('cancel')"
              class="px-4 py-2 text-sm font-medium text-text-secondary bg-bg-primary hover:bg-bg-secondary rounded-lg transition-colors"
            >
              {{ cancelText }}
            </button>
            <button
              @click="emit('confirm')"
              :class="['px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors', confirmButtonClass]"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.15s ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-active .relative,
.dialog-leave-active .relative {
  transition: transform 0.15s ease;
}

.dialog-enter-from .relative {
  transform: scale(0.95) translateY(-10px);
}

.dialog-leave-to .relative {
  transform: scale(0.95) translateY(-10px);
}
</style>
