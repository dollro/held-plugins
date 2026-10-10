import { onBeforeUnmount, ref } from 'vue'

export interface StreamEvent {
  type: string
  data: Record<string, unknown>
}

/** Parse one SSE `data:` payload; ignore anything that is not a typed event. */
export function toStreamEvent(raw: string): StreamEvent | null {
  try {
    const value = JSON.parse(raw) as Partial<StreamEvent>
    return typeof value.type === 'string' && value.data && typeof value.data === 'object'
      ? (value as StreamEvent)
      : null
  } catch {
    return null
  }
}

/** Delay before the next reconnect attempt: 1s, 2s, 4s … capped at 30s. */
export function backoffMs(attempt: number): number {
  return Math.min(30_000, 1_000 * 2 ** attempt)
}

/**
 * Subscribe to the current user's event stream (Server-Sent Events, same origin).
 * The session cookie authenticates. EventSource retries network errors itself,
 * but gives up for good on an HTTP error (401 after the session expired, 502
 * while the service restarts); those are retried here with backoff.
 */
export function useEventStream(url = '/v1/events') {
  const events = ref<StreamEvent[]>([])
  const connected = ref(false)
  let source: EventSource | null = null
  let retry: ReturnType<typeof setTimeout> | null = null
  let attempt = 0

  function connect(): void {
    disconnect()
    source = new EventSource(url)
    source.addEventListener('ready', () => {
      connected.value = true
      attempt = 0
    })
    source.onmessage = (message: MessageEvent<string>) => {
      const event = toStreamEvent(message.data)
      if (event) events.value = [event, ...events.value].slice(0, 50)
    }
    source.onerror = () => {
      connected.value = false
      if (source?.readyState === EventSource.CLOSED) {
        retry = setTimeout(connect, backoffMs(attempt++))
      }
    }
  }

  function disconnect(): void {
    if (retry) clearTimeout(retry)
    retry = null
    source?.close()
    source = null
    connected.value = false
  }

  onBeforeUnmount(disconnect)

  return { events, connected, connect, disconnect }
}
