import { describe, expect, it } from 'vitest'

import { backoffMs, toStreamEvent } from '../useEventStream'

describe('toStreamEvent', () => {
  it('parses a typed event', () => {
    expect(toStreamEvent('{"type":"test","data":{"message":"hi"}}')).toEqual({
      type: 'test',
      data: { message: 'hi' },
    })
  })

  it('ignores malformed or untyped payloads', () => {
    expect(toStreamEvent('not json')).toBeNull()
    expect(toStreamEvent('{"data":{}}')).toBeNull()
  })
})

describe('backoffMs', () => {
  it('doubles and caps at 30 seconds', () => {
    expect([0, 1, 2].map(backoffMs)).toEqual([1000, 2000, 4000])
    expect(backoffMs(10)).toBe(30_000)
  })
})
