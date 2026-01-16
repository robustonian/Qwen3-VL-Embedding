import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export const useSearchStore = defineStore('search', () => {
  const results = ref([])
  const query = ref('')
  const queryType = ref('text')
  const loading = ref(false)
  const recentSearches = ref([])

  const hasResults = computed(() => results.value.length > 0)

  async function searchByText(text, options = {}) {
    loading.value = true
    query.value = text
    queryType.value = 'text'

    try {
      const response = await api.post('/search/text', {
        query: text,
        limit: options.limit || 20,
        file_types: options.fileTypes,  // Array of types: ['text', 'image', 'pdf']
        collection_id: options.collectionId
      })
      results.value = response.data.results
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function searchByImage(imageFile, options = {}) {
    loading.value = true
    queryType.value = 'image'

    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('limit', options.limit || 20)
      // Send file_types as JSON string for form data
      if (options.fileTypes && options.fileTypes.length > 0) {
        formData.append('file_types', JSON.stringify(options.fileTypes))
      }
      if (options.collectionId) formData.append('collection_id', options.collectionId)

      const response = await api.post('/search/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      results.value = response.data.results
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchRecentSearches() {
    const response = await api.get('/search/history')
    recentSearches.value = response.data
    return response.data
  }

  function clearResults() {
    results.value = []
    query.value = ''
  }

  function removeResult(id) {
    results.value = results.value.filter(r => r.id !== id)
  }

  return {
    results,
    query,
    queryType,
    loading,
    recentSearches,
    hasResults,
    searchByText,
    searchByImage,
    fetchRecentSearches,
    clearResults,
    removeResult
  }
})
