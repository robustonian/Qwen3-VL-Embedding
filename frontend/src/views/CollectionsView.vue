<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCollectionsStore } from '@/stores/collections'

const collectionsStore = useCollectionsStore()

const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingCollection = ref(null)
const newCollectionName = ref('')
const newCollectionDescription = ref('')

const collections = computed(() => collectionsStore.collections)
const isLoading = computed(() => collectionsStore.loading)

onMounted(async () => {
  await collectionsStore.fetchCollections()
})

const handleCreate = async () => {
  if (!newCollectionName.value.trim()) return

  await collectionsStore.createCollection(
    newCollectionName.value.trim(),
    newCollectionDescription.value.trim()
  )

  newCollectionName.value = ''
  newCollectionDescription.value = ''
  showCreateModal.value = false
}

const openEditModal = (collection) => {
  editingCollection.value = { ...collection }
  showEditModal.value = true
}

const handleUpdate = async () => {
  if (!editingCollection.value || !editingCollection.value.name.trim()) return

  await collectionsStore.updateCollection(editingCollection.value.id, {
    name: editingCollection.value.name.trim(),
    description: editingCollection.value.description?.trim() || ''
  })

  showEditModal.value = false
  editingCollection.value = null
}

const handleDelete = async (id) => {
  if (confirm('このコレクションを削除しますか？\n（コレクション内のファイルは削除されません）')) {
    await collectionsStore.deleteCollection(id)
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-text-primary">コレクション</h1>
      <button
        @click="showCreateModal = true"
        class="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新規作成
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && !collections.length" class="text-center py-12">
      <div class="inline-block w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
      <p class="text-text-muted mt-4">読み込み中...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!collections.length" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto mb-4 text-text-muted opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <p class="text-text-muted mb-4">コレクションがありません</p>
      <button
        @click="showCreateModal = true"
        class="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors"
      >
        コレクションを作成
      </button>
    </div>

    <!-- Collections List -->
    <div v-else class="space-y-3">
      <div
        v-for="collection in collections"
        :key="collection.id"
        class="bg-bg-secondary border border-border rounded-lg p-4 hover:border-accent transition-colors"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <h3 class="text-lg font-medium text-text-primary">{{ collection.name }}</h3>
            <p v-if="collection.description" class="text-sm text-text-muted mt-1">
              {{ collection.description }}
            </p>
            <div class="flex items-center gap-4 mt-3 text-xs text-text-muted">
              <span class="flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {{ collection.file_count || 0 }} ファイル
              </span>
              <span>作成: {{ formatDate(collection.created_at) }}</span>
            </div>
          </div>

          <div class="flex items-center gap-2 ml-4">
            <button
              @click="openEditModal(collection)"
              class="p-2 hover:bg-bg-tertiary rounded transition-colors text-text-muted hover:text-text-primary"
              title="編集"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              @click="handleDelete(collection.id)"
              class="p-2 hover:bg-red-500/20 rounded transition-colors text-text-muted hover:text-red-500"
              title="削除"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showCreateModal"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          @click.self="showCreateModal = false"
        >
          <div class="w-full max-w-md bg-bg-secondary border border-border rounded-xl shadow-2xl">
            <div class="flex items-center justify-between p-4 border-b border-border">
              <h3 class="text-lg font-medium text-text-primary">新規コレクション</h3>
              <button
                @click="showCreateModal = false"
                class="p-1 hover:bg-bg-tertiary rounded transition-colors"
              >
                <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div class="p-4 space-y-4">
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">名前 *</label>
                <input
                  v-model="newCollectionName"
                  type="text"
                  placeholder="コレクション名"
                  class="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent"
                  @keydown.enter="handleCreate"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">説明（任意）</label>
                <textarea
                  v-model="newCollectionDescription"
                  placeholder="コレクションの説明"
                  rows="3"
                  class="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent resize-none"
                ></textarea>
              </div>
            </div>

            <div class="flex justify-end gap-2 p-4 border-t border-border">
              <button
                @click="showCreateModal = false"
                class="px-4 py-2 bg-bg-tertiary text-text-secondary rounded-lg hover:bg-bg-primary transition-colors"
              >
                キャンセル
              </button>
              <button
                @click="handleCreate"
                :disabled="!newCollectionName.trim()"
                class="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                作成
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Edit Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showEditModal && editingCollection"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          @click.self="showEditModal = false"
        >
          <div class="w-full max-w-md bg-bg-secondary border border-border rounded-xl shadow-2xl">
            <div class="flex items-center justify-between p-4 border-b border-border">
              <h3 class="text-lg font-medium text-text-primary">コレクションを編集</h3>
              <button
                @click="showEditModal = false"
                class="p-1 hover:bg-bg-tertiary rounded transition-colors"
              >
                <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div class="p-4 space-y-4">
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">名前 *</label>
                <input
                  v-model="editingCollection.name"
                  type="text"
                  placeholder="コレクション名"
                  class="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent"
                  @keydown.enter="handleUpdate"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">説明（任意）</label>
                <textarea
                  v-model="editingCollection.description"
                  placeholder="コレクションの説明"
                  rows="3"
                  class="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent resize-none"
                ></textarea>
              </div>
            </div>

            <div class="flex justify-end gap-2 p-4 border-t border-border">
              <button
                @click="showEditModal = false"
                class="px-4 py-2 bg-bg-tertiary text-text-secondary rounded-lg hover:bg-bg-primary transition-colors"
              >
                キャンセル
              </button>
              <button
                @click="handleUpdate"
                :disabled="!editingCollection.name.trim()"
                class="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
