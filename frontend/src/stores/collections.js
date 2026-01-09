import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export const useCollectionsStore = defineStore('collections', () => {
  const collections = ref([])
  const loading = ref(false)

  const isEmpty = computed(() => collections.value.length === 0)

  async function fetchCollections() {
    loading.value = true
    try {
      const response = await api.get('/collections')
      collections.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function createCollection(name, description = '') {
    const response = await api.post('/collections', { name, description })
    collections.value.unshift(response.data)
    return response.data
  }

  async function updateCollection(id, data) {
    const response = await api.put(`/collections/${id}`, data)
    const index = collections.value.findIndex(c => c.id === id)
    if (index !== -1) {
      collections.value[index] = response.data
    }
    return response.data
  }

  async function deleteCollection(id) {
    await api.delete(`/collections/${id}`)
    collections.value = collections.value.filter(c => c.id !== id)
  }

  async function addDocumentsToCollection(collectionId, documentIds) {
    await api.post(`/collections/${collectionId}/documents`, {
      document_ids: documentIds
    })
  }

  return {
    collections,
    loading,
    isEmpty,
    fetchCollections,
    createCollection,
    updateCollection,
    deleteCollection,
    addDocumentsToCollection
  }
})
