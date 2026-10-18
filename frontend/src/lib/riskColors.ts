export type RiskBand = 'Low' | 'Moderate' | 'High' | 'Severe' | 'No Travel'

export const RISK_COLORS: Record<RiskBand, string> = {
  Low: '#4ade80',
  Moderate: '#eab308',
  High: '#f97316',
  Severe: '#ef6461',
  'No Travel': '#7f1d1d',
}

export function colorForBand(band: string): string {
  return RISK_COLORS[band as RiskBand] ?? '#94a3b8'
}
