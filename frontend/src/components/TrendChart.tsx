import type { TrendPoint } from '../lib/types'

type Props = { points: TrendPoint[] }

export function TrendChart({ points }: Props) {
  if (!points.length) return <div className="chart-empty">No cost history is available.</div>

  const values = points.map((point) => point.cost)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const path = points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * 100
      const y = 92 - ((point.cost - min) / range) * 76
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')
  const fillPath = `${path} L 100 100 L 0 100 Z`

  return (
    <div className="trend-chart" aria-label="Thirty day cost trend chart">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img">
        <defs>
          <linearGradient id="chart-fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#80edc8" stopOpacity="0.42" />
            <stop offset="100%" stopColor="#80edc8" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d="M 0 22 L 100 22 M 0 55 L 100 55 M 0 88 L 100 88" className="chart-grid" />
        <path d={fillPath} fill="url(#chart-fill)" />
        <path d={path} className="chart-line" />
      </svg>
      <div className="chart-axis"><span>{points[0].date.slice(5)}</span><span>Today</span></div>
    </div>
  )
}
