<script setup>
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()

const getIcon = (type) => {
  switch (type) {
    case 'success':
      return 'check'
    case 'error':
      return 'x'
    case 'warning':
      return 'alert'
    case 'info':
    default:
      return 'info'
  }
}

const getTypeClasses = (type) => {
  switch (type) {
    case 'success':
      return 'border-success/30 bg-success/10'
    case 'error':
      return 'border-error/30 bg-error/10'
    case 'warning':
      return 'border-warning/30 bg-warning/10'
    case 'info':
    default:
      return 'border-accent/30 bg-accent/10'
  }
}

const getIconClasses = (type) => {
  switch (type) {
    case 'success':
      return 'bg-success/20 text-success'
    case 'error':
      return 'bg-error/20 text-error'
    case 'warning':
      return 'bg-warning/20 text-warning'
    case 'info':
    default:
      return 'bg-accent/20 text-accent'
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed top-4 right-4 z-[100] flex flex-col gap-3 max-w-sm w-full pointer-events-none"
      aria-live="polite"
      aria-label="Notifications"
    >
      <TransitionGroup name="toast">
        <div
          v-for="toast in toastStore.toasts"
          :key="toast.id"
          :class="[
            'pointer-events-auto relative overflow-hidden',
            'backdrop-blur-xl rounded-2xl border shadow-card-elevated',
            'p-4 pr-10',
            getTypeClasses(toast.type)
          ]"
          role="alert"
        >
          <!-- Gradient accent line -->
          <div
            :class="[
              'absolute top-0 left-0 right-0 h-0.5',
              toast.type === 'success' ? 'bg-gradient-to-r from-success via-success/50 to-transparent' :
              toast.type === 'error' ? 'bg-gradient-to-r from-error via-error/50 to-transparent' :
              toast.type === 'warning' ? 'bg-gradient-to-r from-warning via-warning/50 to-transparent' :
              'bg-gradient-to-r from-accent via-accent/50 to-transparent'
            ]"
          ></div>

          <div class="flex items-start gap-3">
            <!-- Icon -->
            <div
              :class="[
                'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center',
                getIconClasses(toast.type)
              ]"
            >
              <!-- Success icon -->
              <svg v-if="getIcon(toast.type) === 'check'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
              <!-- Error icon -->
              <svg v-else-if="getIcon(toast.type) === 'x'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <!-- Warning icon -->
              <svg v-else-if="getIcon(toast.type) === 'alert'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <!-- Info icon -->
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <p v-if="toast.title" class="font-display font-semibold text-text-primary text-sm mb-0.5">
                {{ toast.title }}
              </p>
              <p class="text-sm text-text-secondary leading-relaxed">
                {{ toast.message }}
              </p>
            </div>
          </div>

          <!-- Dismiss button -->
          <button
            v-if="toast.dismissible"
            @click="toastStore.removeToast(toast.id)"
            class="absolute top-3 right-3 p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-white/10 transition-colors"
            aria-label="Dismiss notification"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Progress bar for auto-dismiss -->
          <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-white/5">
            <div
              class="h-full bg-white/20 animate-toast-progress"
              :style="{ animationDuration: '3s' }"
            ></div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active {
  animation: toast-in 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-leave-active {
  animation: toast-out 0.3s ease-in forwards;
}

.toast-move {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(100%) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateX(100%) scale(0.9);
  }
}

@keyframes toast-progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

.animate-toast-progress {
  animation: toast-progress linear forwards;
}
</style>
