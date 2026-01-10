<script setup>
import { computed, watch, onMounted, onUnmounted } from 'vue'

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
    default: 'danger', // 'danger' | 'warning' | 'info' | 'success'
    validator: (value) => ['danger', 'warning', 'info', 'success'].includes(value)
  }
})

const emit = defineEmits(['confirm', 'cancel'])

const typeConfig = computed(() => {
  switch (props.type) {
    case 'danger':
      return {
        iconBg: 'bg-error/10',
        iconColor: 'text-error',
        glowColor: 'from-error/30 via-error/10 to-error/30',
        buttonClass: 'btn-danger'
      }
    case 'warning':
      return {
        iconBg: 'bg-warning/10',
        iconColor: 'text-warning',
        glowColor: 'from-warning/30 via-warning/10 to-warning/30',
        buttonClass: 'bg-warning hover:bg-warning/90 text-bg-primary font-medium'
      }
    case 'success':
      return {
        iconBg: 'bg-success/10',
        iconColor: 'text-success',
        glowColor: 'from-success/30 via-success/10 to-success/30',
        buttonClass: 'bg-success hover:bg-success/90 text-white font-medium'
      }
    case 'info':
    default:
      return {
        iconBg: 'bg-accent/10',
        iconColor: 'text-accent',
        glowColor: 'from-accent/30 via-accent/10 to-accent/30',
        buttonClass: 'btn-primary'
      }
  }
})

// Keyboard handler
const handleKeydown = (e) => {
  if (!props.show) return

  if (e.key === 'Escape') {
    emit('cancel')
  } else if (e.key === 'Enter') {
    emit('confirm')
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
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
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm"></div>

        <!-- Dialog Container -->
        <div class="dialog-content relative w-full max-w-md">
          <!-- Glow effect -->
          <div
            class="absolute -inset-0.5 rounded-2xl blur-lg opacity-60"
            :class="['bg-gradient-to-r', typeConfig.glowColor]"
          ></div>

          <!-- Dialog -->
          <div class="relative bg-bg-secondary border border-border/50 rounded-2xl shadow-2xl overflow-hidden">
            <!-- Content -->
            <div class="p-6">
              <div class="flex flex-col items-center text-center">
                <!-- Animated Icon -->
                <div
                  class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 animate-scale-in"
                  :class="typeConfig.iconBg"
                >
                  <!-- Danger icon (trash) -->
                  <svg v-if="type === 'danger'" :class="['w-8 h-8', typeConfig.iconColor]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  <!-- Warning icon (exclamation) -->
                  <svg v-else-if="type === 'warning'" :class="['w-8 h-8', typeConfig.iconColor]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <!-- Success icon (check) -->
                  <svg v-else-if="type === 'success'" :class="['w-8 h-8', typeConfig.iconColor]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <!-- Info icon -->
                  <svg v-else :class="['w-8 h-8', typeConfig.iconColor]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>

                <!-- Text -->
                <h3 class="text-lg font-display font-semibold text-text-primary mb-2">{{ title }}</h3>
                <p class="text-sm text-text-secondary leading-relaxed">{{ message }}</p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex gap-3 px-6 py-4 bg-bg-tertiary/50 border-t border-border/50">
              <button
                @click="emit('cancel')"
                class="btn-ghost flex-1 justify-center"
              >
                {{ cancelText }}
              </button>
              <button
                @click="emit('confirm')"
                :class="['flex-1 justify-center px-4 py-2.5 rounded-xl text-sm transition-all duration-200 active:scale-[0.98]', typeConfig.buttonClass]"
              >
                {{ confirmText }}
              </button>
            </div>

            <!-- Keyboard hints -->
            <div class="flex items-center justify-center gap-4 px-6 py-2 bg-bg-primary/30 text-xs text-text-muted">
              <span class="flex items-center gap-1.5">
                <kbd class="px-1.5 py-0.5 rounded bg-bg-tertiary border border-border/50 font-mono">Enter</kbd>
                確認
              </span>
              <span class="flex items-center gap-1.5">
                <kbd class="px-1.5 py-0.5 rounded bg-bg-tertiary border border-border/50 font-mono">ESC</kbd>
                キャンセル
              </span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-enter-active {
  transition: opacity 0.2s ease-out;
}

.dialog-leave-active {
  transition: opacity 0.15s ease-in;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-active .dialog-content {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease-out;
}

.dialog-leave-active .dialog-content {
  transition: transform 0.15s ease-in, opacity 0.15s ease-in;
}

.dialog-enter-from .dialog-content {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

.dialog-leave-to .dialog-content {
  opacity: 0;
  transform: scale(0.98) translateY(-5px);
}
</style>
