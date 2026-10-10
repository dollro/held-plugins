import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api, isUnauthenticated, type User } from '@/api/client'

/**
 * Who is logged in. The server session is the source of truth; this store mirrors
 * it. Logging in happens on Django's login page (/accounts/login/), not in Vue.
 */
export const useSessionStore = defineStore('session', () => {
  const user = ref<User | null>(null)
  const loaded = ref(false)

  const isAuthenticated = computed(() => user.value !== null)

  async function load(): Promise<void> {
    try {
      user.value = await api.me()
    } catch (error) {
      if (!isUnauthenticated(error)) throw error
      user.value = null
    } finally {
      loaded.value = true
    }
  }

  async function logout(): Promise<void> {
    await api.logout()
    user.value = null
  }

  return { user, loaded, isAuthenticated, load, logout }
})
