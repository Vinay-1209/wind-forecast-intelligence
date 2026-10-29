export function WindMark() {
  return (
    <svg className="wind-mark" viewBox="0 0 64 40" aria-hidden="true">
      <path d="M4 30c8-2 12-9 20-9s12 7 22 6" />
      <path d="M8 20c8-2 12-9 18-9s10 7 20 6" />
      <path d="M2 10c8-2 12-7 18-7s8 5 14 4" />
    </svg>
  )
}

export function LoadingState() {
  return (
    <div className="loading-layout">
      <div className="wind-loader" role="status">
        <WindMark />
        <p>Loading the January wind analysis…</p>
      </div>
      <div className="metric-grid" aria-hidden="true">
        <div className="skeleton metric-skel" />
        <div className="skeleton metric-skel" />
        <div className="skeleton metric-skel" />
      </div>
      <div className="skeleton chart-skel" aria-hidden="true" />
    </div>
  )
}

export function ChartFallback() {
  return (
    <div className="chart-fallback" role="status" aria-busy="true">
      <WindMark />
      <p>Loading charts…</p>
      <div className="skeleton chart-skel" aria-hidden="true" />
      <div className="skeleton chart-skel short" aria-hidden="true" />
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="status error" role="alert">
      <p>{message}</p>
      <button type="button" className="button primary" onClick={onRetry}>
        Try again
      </button>
    </div>
  )
}

export function EmptyState() {
  return (
    <div className="status empty" role="status">
      <h2>No matched intervals</h2>
      <p>
        None of the half-hours in this range have both an actual and a forecast published at or before the cutoff.
        The error metrics are left blank rather than shown as zero.
      </p>
    </div>
  )
}
