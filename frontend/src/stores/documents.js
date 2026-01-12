import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export const useDocumentsStore = defineStore('documents', () => {
  const documents = ref([])
  const total = ref(0)
  const loading = ref(false)
  const uploading = ref(false)
  const uploadProgress = ref(0)
  const stats = ref(null)

  // PDF processing progress
  const pdfProgress = ref({
    isProcessing: false,
    currentPage: 0,
    totalPages: 0,
    message: '',
    fileName: ''
  })

  const isEmpty = computed(() => documents.value.length === 0)

  async function fetchDocuments(params = {}) {
    loading.value = true
    try {
      const response = await api.get('/documents', { params })
      documents.value = response.data.items
      total.value = response.data.total
    } finally {
      loading.value = false
    }
  }

  async function uploadFiles(files, collectionId = null) {
    uploading.value = true
    uploadProgress.value = 0

    try {
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file)
      }
      if (collectionId) {
        formData.append('collection_id', collectionId)
      }

      const response = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          uploadProgress.value = Math.round((e.loaded * 100) / e.total)
        }
      })

      await fetchDocuments()
      return response.data
    } finally {
      uploading.value = false
      uploadProgress.value = 0
    }
  }

  /**
   * Upload files with streaming progress (for PDFs with page-by-page updates).
   * Uses NDJSON streaming to receive real-time progress updates.
   */
  async function uploadFilesWithProgress(files, collectionId = null) {
    uploading.value = true
    uploadProgress.value = 0
    pdfProgress.value = {
      isProcessing: true,
      currentPage: 0,
      totalPages: 0,
      message: 'アップロード準備中...',
      fileName: ''
    }

    try {
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file)
      }
      if (collectionId) {
        formData.append('collection_id', collectionId)
      }

      // Use fetch for streaming response
      const response = await fetch('/api/documents/upload/stream', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let results = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process complete lines (NDJSON format)
        const lines = buffer.split('\n')
        buffer = lines.pop() // Keep incomplete line in buffer

        for (const line of lines) {
          if (!line.trim()) continue

          try {
            const event = JSON.parse(line)

            if (event.type === 'progress') {
              pdfProgress.value.currentPage = event.current_page
              pdfProgress.value.totalPages = event.total_pages
              pdfProgress.value.message = event.message
              pdfProgress.value.fileName = event.file_name

              // Calculate overall progress (HTTP upload is ~20%, processing is 20-100%)
              if (event.total_pages > 0) {
                const pageProgress = (event.current_page / event.total_pages) * 80
                uploadProgress.value = 20 + Math.round(pageProgress)
              } else {
                uploadProgress.value = 20
              }
            } else if (event.type === 'file_complete') {
              results.push(event.result)
            } else if (event.type === 'complete') {
              uploadProgress.value = 100
              results = event.results || results
            } else if (event.type === 'error') {
              console.error('Upload error:', event.message)
            }
          } catch (e) {
            console.warn('Failed to parse progress event:', line, e)
          }
        }
      }

      await fetchDocuments()
      return results
    } finally {
      uploading.value = false
      uploadProgress.value = 0
      pdfProgress.value = {
        isProcessing: false,
        currentPage: 0,
        totalPages: 0,
        message: '',
        fileName: ''
      }
    }
  }

  async function deleteDocument(id) {
    await api.delete(`/documents/${id}`)
    documents.value = documents.value.filter(d => d.id !== id)
    total.value--
  }

  async function deleteDocuments(ids) {
    await api.post('/documents/batch-delete', { ids })
    documents.value = documents.value.filter(d => !ids.includes(d.id))
    total.value -= ids.length
  }

  async function fetchStats() {
    const response = await api.get('/documents/stats')
    stats.value = response.data
    return response.data
  }

  return {
    documents,
    total,
    loading,
    uploading,
    uploadProgress,
    pdfProgress,
    stats,
    isEmpty,
    fetchDocuments,
    uploadFiles,
    uploadFilesWithProgress,
    deleteDocument,
    deleteDocuments,
    fetchStats
  }
})
