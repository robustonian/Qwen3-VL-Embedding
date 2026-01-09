import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/library',
    name: 'library',
    component: () => import('@/views/LibraryView.vue')
  },
  {
    path: '/collections',
    name: 'collections',
    component: () => import('@/views/CollectionsView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
