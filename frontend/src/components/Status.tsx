export function LoadingState() {
  return (
    <p className="status" role="status">
      Loading the January wind analysis…
    </p>
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
