<script setup lang="ts">
import { api } from '@/api/client'
// >>> realtime
import { onMounted } from 'vue'

import { useEventStream } from '@/composables/useEventStream'

const { events, connected, connect } = useEventStream()
onMounted(connect)
// <<< realtime

async function sendTestEvent() {
  await api.sendTestEvent()
}
</script>

<template>
  <section class="space-y-6">
    <h1 class="text-xl font-semibold">
      Dashboard
    </h1>
    <p class="text-sm text-slate-600">
      The button runs the async path: Django enqueues a Celery task after commit,
      and the task publishes an event to Redis.
      <!-- >>> realtime -->
      The realtime service streams it to this page (Server-Sent Events).
      <!-- <<< realtime -->
    </p>
    <button
      class="rounded bg-slate-900 px-4 py-2 text-white"
      data-testid="send-test-event"
      @click="sendTestEvent"
    >
      Send test event
    </button>
    <!-- >>> realtime -->
    <p
      class="text-sm"
      data-testid="stream-status"
    >
      Event stream: {{ connected ? 'connected' : 'disconnected' }}
    </p>
    <ul
      class="space-y-2"
      data-testid="events"
    >
      <li
        v-for="(event, index) in events"
        :key="index"
        class="rounded border bg-white px-3 py-2 text-sm"
      >
        <strong>{{ event.type }}</strong>: {{ event.data.message }}
      </li>
    </ul>
    <!-- <<< realtime -->
  </section>
</template>
