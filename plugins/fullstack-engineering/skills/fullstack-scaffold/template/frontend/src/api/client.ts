/**
 * The only module that talks HTTP. Components and stores import `api`, never fetch.
 *
 * Auth is the Django session cookie (sent automatically, same origin). Unsafe
 * requests echo Django's CSRF cookie in the X-CSRFToken header. Nothing
 * auth-related is stored in localStorage.
 */

const BASE = '/api/v1'
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail?: string,
  ) {
    super(detail ?? `HTTP ${status}`)
  }
}

export interface User {
  id: number
  email: string
  username: string
}

function csrfToken(): string {
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)
  return match?.[1] ? decodeURIComponent(match[1]) : ''
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (!SAFE_METHODS.has(method)) headers['X-CSRFToken'] = csrfToken()

  const response = await fetch(`${BASE}${path}`, {
    method,
    headers,
    credentials: 'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  // Error pages from the proxy or Django (HTML 403/502) are not JSON: never let
  // them surface as a parse error instead of an ApiError.
  const isJson = response.headers.get('content-type')?.includes('application/json') ?? false
  let data: unknown
  if (isJson) {
    try {
      data = await response.json()
    } catch {
      data = undefined
    }
  }
  if (!response.ok) {
    const detail = (data as { detail?: string } | undefined)?.detail
    throw new ApiError(response.status, typeof detail === 'string' ? detail : undefined)
  }
  return data as T
}

export function isUnauthenticated(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.status === 403)
}

export function errorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  return error instanceof ApiError && error.detail ? error.detail : fallback
}

export const api = {
  logout: () => request<void>('POST', '/auth/logout/'),
  me: () => request<User>('GET', '/auth/me/'),
  sendTestEvent: () => request<void>('POST', '/events/test/'),
}
