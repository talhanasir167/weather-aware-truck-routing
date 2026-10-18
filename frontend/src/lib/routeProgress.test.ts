import { describe, expect, it } from 'vitest'
import { pointAtFraction } from './routeProgress'

const LINE: [number, number][] = [
  [-87.63, 41.88],
  [-85.0, 42.0],
  [-83.05, 42.33],
]

describe('pointAtFraction', () => {
  it('returns start at t=0', () => {
    expect(pointAtFraction(LINE, 0)).toEqual(LINE[0])
  })

  it('returns end at t=1', () => {
    expect(pointAtFraction(LINE, 1)).toEqual(LINE[2])
  })

  it('interpolates midpoint between ends', () => {
    const mid = pointAtFraction(LINE, 0.5)
    expect(mid[0]).toBeGreaterThan(LINE[0][0])
    expect(mid[0]).toBeLessThan(LINE[2][0])
    expect(mid[1]).toBeGreaterThan(LINE[0][1] - 0.5)
  })

  it('handles empty and single-point geometry', () => {
    expect(pointAtFraction([], 0.5)).toEqual([0, 0])
    expect(pointAtFraction([[1, 2]], 0.5)).toEqual([1, 2])
  })
})
