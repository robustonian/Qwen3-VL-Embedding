import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  let nextId = 0

  /**
   * Add a new toast notification
   * @param {string} type - 'success' | 'error' | 'warning' | 'info'
   * @param {string} message - The message to display
   * @param {Object} options - Optional settings
   * @param {number} options.duration - Duration in ms (default: 3000, 0 for persistent)
   * @param {boolean} options.dismissible - Whether user can dismiss (default: true)
   * @param {string} options.title - Optional title
   */
  const addToast = (type, message, options = {}) => {
    const id = nextId++
    const duration = options.duration ?? 3000
    const dismissible = options.dismissible ?? true
    const title = options.title ?? null

    const toast = {
      id,
      type,
      message,
      title,
      dismissible,
      createdAt: Date.now()
    }

    toasts.value.push(toast)

    // Auto-remove after duration (if not persistent)
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }

    return id
  }

  /**
   * Remove a toast by ID
   * @param {number} id - Toast ID to remove
   */
  const removeToast = (id) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  /**
   * Clear all toasts
   */
  const clearAll = () => {
    toasts.value = []
  }

  // Convenience methods
  const success = (message, options = {}) => addToast('success', message, options)
  const error = (message, options = {}) => addToast('error', message, { duration: 5000, ...options })
  const warning = (message, options = {}) => addToast('warning', message, options)
  const info = (message, options = {}) => addToast('info', message, options)

  return {
    toasts,
    addToast,
    removeToast,
    clearAll,
    success,
    error,
    warning,
    info
  }
})
