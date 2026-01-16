<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCollectionsStore } from '@/stores/collections'
import { useToastStore } from '@/stores/toast'

const collectionsStore = useCollectionsStore()
const toast = useToastStore()

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const editingCollection = ref(null)
const deletingCollection = ref(null)
const newCollectionName = ref('')
const newCollectionDescription = ref('')
const createNameInput = ref(null)
const editNameInput = ref(null)

const collections = computed(() => collectionsStore.collections)
const isLoading = computed(() => collectionsStore.loading)

onMounted(async () => {
  await collectionsStore.fetchCollections()
})

const openCreateModal = () => {
  showCreateModal.value = true
  setTimeout(() => createNameInput.value?.focus(), 100)
}

const handleCreate = async () => {
  if (!newCollectionName.value.trim()) return

  try {
    await collectionsStore.createCollection(
      newCollectionName.value.trim(),
      newCollectionDescription.value.trim()
    )
    toast.success('コレクションを作成しました')
    newCollectionName.value = ''
    newCollectionDescription.value = ''
    showCreateModal.value = false
  } catch (error) {
    toast.error('コレクションの作成に失敗しました')
  }
}

const openEditModal = (collection) => {
  editingCollection.value = { ...collection }
  showEditModal.value = true
  setTimeout(() => editNameInput.value?.focus(), 100)
}

const handleUpdate = async () => {
  if (!editingCollection.value || !editingCollection.value.name.trim()) return

  try {
    await collectionsStore.updateCollection(editingCollection.value.id, {
      name: editingCollection.value.name.trim(),
      description: editingCollection.value.description?.trim() || ''
    })
    toast.success('コレクションを更新しました')
    showEditModal.value = false
    editingCollection.value = null
  } catch (error) {
    toast.error('コレクションの更新に失敗しました')
  }
}

const openDeleteModal = (collection) => {
  deletingCollection.value = collection
  showDeleteModal.value = true
}

const handleDelete = async () => {
  if (!deletingCollection.value) return

  try {
    await collectionsStore.deleteCollection(deletingCollection.value.id)
    toast.success('コレクションを削除しました')
    showDeleteModal.value = false
    deletingCollection.value = null
  } catch (error) {
    toast.error('コレクションの削除に失敗しました')
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
  <div class="max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-display font-bold text-text-primary">コレクション</h1>
        <p class="text-sm text-text-muted mt-1">画像をグループ化して整理</p>
      </div>
      <button
        @click="openCreateModal"
        class="btn btn-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新規作成
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && !collections.length" class="text-center py-20">
      <div class="relative inline-block">
        <div class="w-12 h-12 border-2 border-accent/30 rounded-full"></div>
        <div class="absolute inset-0 w-12 h-12 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
      </div>
      <p class="text-text-muted mt-4">読み込み中...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!collections.length" class="text-center py-20">
      <div class="relative inline-block mb-6">
        <!-- Orbital rings -->
        <div class="w-24 h-24 relative">
          <div class="absolute inset-0 border-2 border-dashed border-accent/20 rounded-full animate-orbit"></div>
          <div class="absolute inset-2 border border-dashed border-accent/10 rounded-full animate-orbit-reverse"></div>
          <!-- Center icon -->
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center">
              <svg class="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
          </div>
        </div>
      </div>
      <h3 class="text-lg font-display font-semibold text-text-primary mb-2">コレクションがありません</h3>
      <p class="text-text-muted mb-6 max-w-sm mx-auto">
        コレクションを作成して、関連する画像をグループ化しましょう
      </p>
      <button
        @click="openCreateModal"
        class="btn btn-primary inline-flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        最初のコレクションを作成
      </button>
    </div>

    <!-- Collections Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="(collection, index) in collections"
        :key="collection.id"
        class="group card-interactive p-5 animate-slide-up"
        :style="{ animationDelay: `${index * 50}ms` }"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <!-- Collection icon -->
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center group-hover:from-accent/30 group-hover:to-accent/10 transition-all duration-300">
                <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-lg font-display font-semibold text-text-primary truncate group-hover:text-accent transition-colors">
                  {{ collection.name }}
                </h3>
              </div>
            </div>

            <!-- Description -->
            <p v-if="collection.description" class="text-sm text-text-secondary mb-4 line-clamp-2">
              {{ collection.description }}
            </p>
            <p v-else class="text-sm text-text-muted/50 italic mb-4">
              説明なし
            </p>

            <!-- Stats -->
            <div class="flex items-center gap-4 text-xs text-text-muted">
              <span class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-bg-tertiary/50">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {{ collection.file_count || 0 }} ファイル
              </span>
              <span class="flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {{ formatDate(collection.created_at) }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1 ml-4 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              @click.stop="openEditModal(collection)"
              class="p-2 rounded-lg hover:bg-bg-tertiary text-text-muted hover:text-accent transition-all hover:scale-105"
              title="編集"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              @click.stop="openDeleteModal(collection)"
              class="p-2 rounded-lg hover:bg-error/10 text-text-muted hover:text-error transition-all hover:scale-105"
              title="削除"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showCreateModal"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          @click.self="showCreateModal = false"
        >
          <div class="modal-content w-full max-w-md">
            <!-- Glow effect -->
            <div class="absolute -inset-0.5 bg-gradient-to-r from-accent/30 via-accent/10 to-accent/30 rounded-2xl blur-lg opacity-50"></div>

            <div class="relative bg-bg-secondary border border-border/50 rounded-2xl shadow-2xl overflow-hidden">
              <!-- Header -->
              <div class="flex items-center justify-between p-5 border-b border-border/50">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
                    <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                  <h3 class="text-lg font-display font-semibold text-text-primary">新規コレクション</h3>
                </div>
                <button
                  @click="showCreateModal = false"
                  class="p-2 rounded-lg hover:bg-bg-tertiary text-text-muted hover:text-text-primary transition-colors"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <!-- Body -->
              <div class="p-5 space-y-4">
                <div>
                  <label class="block text-sm font-medium text-text-secondary mb-2">名前 <span class="text-error">*</span></label>
                  <input
                    ref="createNameInput"
                    v-model="newCollectionName"
                    type="text"
                    placeholder="コレクション名を入力"
                    class="input w-full"
                    @keydown.enter="handleCreate"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-text-secondary mb-2">説明（任意）</label>
                  <textarea
                    v-model="newCollectionDescription"
                    placeholder="コレクションの説明を入力"
                    rows="3"
                    class="input w-full resize-none"
                  ></textarea>
                </div>
              </div>

              <!-- Footer -->
              <div class="flex justify-end gap-3 p-5 pt-0">
                <button
                  @click="showCreateModal = false"
                  class="btn btn-ghost"
                >
                  キャンセル
                </button>
                <button
                  @click="handleCreate"
                  :disabled="!newCollectionName.trim()"
                  class="btn btn-primary"
                >
                  作成
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Edit Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showEditModal && editingCollection"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          @click.self="showEditModal = false"
        >
          <div class="modal-content w-full max-w-md">
            <!-- Glow effect -->
            <div class="absolute -inset-0.5 bg-gradient-to-r from-accent/30 via-accent/10 to-accent/30 rounded-2xl blur-lg opacity-50"></div>

            <div class="relative bg-bg-secondary border border-border/50 rounded-2xl shadow-2xl overflow-hidden">
              <!-- Header -->
              <div class="flex items-center justify-between p-5 border-b border-border/50">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
                    <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </div>
                  <h3 class="text-lg font-display font-semibold text-text-primary">コレクションを編集</h3>
                </div>
                <button
                  @click="showEditModal = false"
                  class="p-2 rounded-lg hover:bg-bg-tertiary text-text-muted hover:text-text-primary transition-colors"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <!-- Body -->
              <div class="p-5 space-y-4">
                <div>
                  <label class="block text-sm font-medium text-text-secondary mb-2">名前 <span class="text-error">*</span></label>
                  <input
                    ref="editNameInput"
                    v-model="editingCollection.name"
                    type="text"
                    placeholder="コレクション名を入力"
                    class="input w-full"
                    @keydown.enter="handleUpdate"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-text-secondary mb-2">説明（任意）</label>
                  <textarea
                    v-model="editingCollection.description"
                    placeholder="コレクションの説明を入力"
                    rows="3"
                    class="input w-full resize-none"
                  ></textarea>
                </div>
              </div>

              <!-- Footer -->
              <div class="flex justify-end gap-3 p-5 pt-0">
                <button
                  @click="showEditModal = false"
                  class="btn btn-ghost"
                >
                  キャンセル
                </button>
                <button
                  @click="handleUpdate"
                  :disabled="!editingCollection.name.trim()"
                  class="btn btn-primary"
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showDeleteModal && deletingCollection"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          @click.self="showDeleteModal = false"
        >
          <div class="modal-content w-full max-w-sm">
            <!-- Glow effect (red for delete) -->
            <div class="absolute -inset-0.5 bg-gradient-to-r from-error/30 via-error/10 to-error/30 rounded-2xl blur-lg opacity-50"></div>

            <div class="relative bg-bg-secondary border border-border/50 rounded-2xl shadow-2xl overflow-hidden">
              <!-- Header -->
              <div class="p-6 text-center">
                <!-- Warning icon -->
                <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-error/10 flex items-center justify-center">
                  <svg class="w-8 h-8 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>

                <h3 class="text-lg font-display font-semibold text-text-primary mb-2">
                  コレクションを削除
                </h3>
                <p class="text-sm text-text-secondary mb-2">
                  「<span class="font-medium text-text-primary">{{ deletingCollection.name }}</span>」を削除しますか？
                </p>
                <p class="text-xs text-text-muted">
                  コレクション内のファイルは削除されません
                </p>
              </div>

              <!-- Footer -->
              <div class="flex gap-3 p-4 border-t border-border/50 bg-bg-tertiary/30">
                <button
                  @click="showDeleteModal = false"
                  class="btn btn-ghost flex-1"
                >
                  キャンセル
                </button>
                <button
                  @click="handleDelete"
                  class="btn btn-danger flex-1"
                >
                  削除する
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
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
  transform: scale(0.95) translateY(-10px);
}

.modal-leave-to .modal-content {
  opacity: 0;
  transform: scale(0.98) translateY(-5px);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
