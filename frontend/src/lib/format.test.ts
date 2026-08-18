import { describe, expect, it } from 'vitest'

import { currency, percent, titleCase } from './format'

describe('dashboard formatters', () => {
  it('formats USD values for executive summaries', () => {
    expect(currency(1200)).toBe('$1,200')
  })

  it('includes a plus sign for rising spend', () => {
    expect(percent(4.2)).toBe('+4.2%')
  })

  it('turns machine categories into readable labels', () => {
    expect(titleCase('idle_storage')).toBe('Idle Storage')
  })
})
