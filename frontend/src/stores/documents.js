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
    stats,
    isEmpty,
    fetchDocuments,
    uploadFiles,
    deleteDocument,
    deleteDocuments,
    fetchStats
  }
})
