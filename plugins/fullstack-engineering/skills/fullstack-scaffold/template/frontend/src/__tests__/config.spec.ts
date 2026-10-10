import { describe, expect, it } from 'vitest'

import { readRuntimeConfig } from '../config'

function page(json: string | null): Document {
  const doc = document.implementation.createHTMLDocument()
  if (json !== null) {
    const el = doc.createElement('script')
    el.id = 'runtime-config'
    el.type = 'application/json'
    el.textContent = json
    doc.body.append(el)
  }
  return doc
}

describe('readRuntimeConfig', () => {
  it('reads the values Django rendered', () => {
    const doc = page('{"environment": "staging", "version": "v1.2.3"}')
    expect(readRuntimeConfig(doc)).toEqual({ environment: 'staging', version: 'v1.2.3' })
  })

  it('falls back when the element is missing or broken', () => {
    expect(readRuntimeConfig(page(null)).environment).toBe('local')
    expect(readRuntimeConfig(page('{broken')).environment).toBe('local')
  })
})
