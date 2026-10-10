<script setup lang="ts">
import { config } from '@/config'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()

async function logout() {
  await session.logout()
  window.location.assign('/')
}
</script>

<template>
  <div class="min-h-screen">
    <header class="flex items-center justify-between border-b bg-white px-6 py-3">
      <span class="flex items-center gap-2 font-semibold">
        __PROJECT_TITLE__
        <!-- Visible everywhere except production, so nobody mistakes staging for it. -->
        <span
          v-if="config.environment !== 'production'"
          class="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900"
          data-testid="environment"
        >{{ config.environment }}</span>
      </span>
      <div
        v-if="session.user"
        class="flex items-center gap-4 text-sm"
      >
        <span data-testid="current-user">{{ session.user.email }}</span>
        <button
          class="rounded border px-3 py-1 hover:bg-slate-100"
          @click="logout"
        >
          Log out
        </button>
      </div>
    </header>
    <main class="mx-auto max-w-3xl px-6 py-8">
      <RouterView />
    </main>
  </div>
</template>
