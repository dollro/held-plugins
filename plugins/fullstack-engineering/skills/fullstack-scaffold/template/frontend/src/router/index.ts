import { createRouter, createWebHistory } from 'vue-router'

import { useSessionStore } from '@/stores/session'

export function createAppRouter() {
  const router = createRouter({
    // Django routes /app/* to the SPA shell; paths below are relative to it.
    history: createWebHistory('/app/'),
    routes: [
      { path: '/', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
      { path: '/:pathMatch(.*)*', redirect: '/' },
    ],
  })

  router.beforeEach(async (to) => {
    const session = useSessionStore()
    if (!session.loaded) await session.load()
    if (!session.isAuthenticated) {
      // Hard navigation: Django serves the login page (allauth), then returns here.
      const next = router.resolve(to).href
      window.location.assign(`/accounts/login/?next=${encodeURIComponent(next)}`)
      return false
    }
    return true
  })

  return router
}
