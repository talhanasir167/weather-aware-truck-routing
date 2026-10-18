import { describe, expect, it } from 'vitest'
import { colorForBand, RISK_COLORS } from './riskColors'

describe('riskColors', () => {
  it('maps every band', () => {
    expect(colorForBand('Low')).toBe(RISK_COLORS.Low)
    expect(colorForBand('Severe')).toBe(RISK_COLORS.Severe)
    expect(colorForBand('No Travel')).toBe(RISK_COLORS['No Travel'])
  })

  it('falls back for unknown', () => {
    expect(colorForBand('Unknown')).toBe('#94a3b8')
  })
})
