/**
 * Runtime configuration, rendered by Django into every page
 * (`<script id="runtime-config" type="application/json">`, see backend/api/context.py).
 *
 * Environment-specific values come from here, never from `import.meta.env`:
 * Vite compiles VITE_* variables into the bundle at build time, and the same
 * bundle runs in staging and production. Only public values belong here.
 */
export interface RuntimeConfig {
  environment: string
  version: string
}

const FALLBACK: RuntimeConfig = { environment: 'local', version: 'development' }

export function readRuntimeConfig(doc: Document = document): RuntimeConfig {
  const el = doc.getElementById('runtime-config')
  if (!el?.textContent) return FALLBACK
  try {
    return { ...FALLBACK, ...(JSON.parse(el.textContent) as Partial<RuntimeConfig>) }
  } catch {
    return FALLBACK
  }
}

export const config = readRuntimeConfig()
