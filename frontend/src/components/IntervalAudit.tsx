import type { ForecastDetails } from "../api/types.ts"
import { formatDay, formatMw, formatSignedMw, formatWhen, reasonText } from "../format.ts"
import { WindMark } from "./Status.tsx"

export function IntervalAudit({
  detail,
  status,
  error,
}: {
  detail: ForecastDetails | null
  status: "idle" | "loading" | "ready" | "error"
  error: string | null
}) {
  const waiting = status === "loading"
  return (
    <section className="panel" aria-labelledby="audit-heading">
      <div className="section-heading">
        <h2 id="audit-heading">Why this interval was scored</h2>
        <p>Each row is a WINDFOR publication for the selected delivery time. Only the latest one at or before the cutoff can enter the metrics.</p>
      </div>
      <div className={waiting ? "audit-slot is-loading" : "audit-slot"} aria-busy={waiting}>
        {waiting ? (
          <div className="audit-overlay">
            <div className="wind-loader" role="status">
              <WindMark />
              <p>Loading this interval…</p>
            </div>
          </div>
        ) : null}
        {status === "error" ? (
          <p className="status error">
            {error}
            {detail ? " The figures below are from the previous interval." : null}
          </p>
        ) : null}
        {detail ? (
          <div className={waiting ? "audit-stale" : undefined}>
            <AuditBody detail={detail} />
          </div>
        ) : waiting ? (
          <AuditSkeleton />
        ) : (
          <p>Select an interval from the chart or the largest misses.</p>
        )}
      </div>
    </section>
  )
}

function AuditSkeleton() {
  return (
    <div className="audit-skeleton" aria-hidden="true">
      <div className="skeleton sk-verdict" />
      <div className="sk-grid">
        {Array.from({ length: 8 }, (_, index) => (
          <div key={index} className="skeleton sk-cell" />
        ))}
      </div>
      <div className="skeleton sk-table" />
    </div>
  )
}

function AuditBody({ detail }: { detail: ForecastDetails }) {
  const cutoffLabel = formatWhen(detail.cutoff_time)
  return (
    <>
      <p className={detail.included ? "verdict included" : "verdict excluded"}>
        {reasonText(detail.reason, cutoffLabel)}
      </p>
      <dl className="audit-grid">
        <div>
          <dt>Delivery</dt>
          <dd>{formatWhen(detail.start_time)}</dd>
        </div>
        <div>
          <dt>Decision day</dt>
          <dd>{formatDay(detail.decision_date)}</dd>
        </div>
        <div>
          <dt>Cutoff</dt>
          <dd>{cutoffLabel}</dd>
        </div>
        <div>
          <dt>Selected forecast</dt>
          <dd>{formatMw(detail.forecast_mw, 0)}</dd>
        </div>
        <div>
          <dt>Published</dt>
          <dd>{formatWhen(detail.publish_time)}</dd>
        </div>
        <div>
          <dt>Actual</dt>
          <dd>{formatMw(detail.actual_mw, 0)}</dd>
        </div>
        <div>
          <dt>Signed error</dt>
          <dd>{formatSignedMw(detail.error_mw, 0)}</dd>
        </div>
        <div>
          <dt>Absolute error</dt>
          <dd>{formatMw(detail.absolute_error_mw, 0)}</dd>
        </div>
      </dl>
      <div className="table-wrap">
        <table>
          <caption>Forecast publications for this delivery interval</caption>
          <thead>
            <tr>
              <th scope="col">Published</th>
              <th scope="col">Generation</th>
              <th scope="col">At or before cutoff</th>
              <th scope="col">Used</th>
            </tr>
          </thead>
          <tbody>
            {detail.versions.length === 0 ? (
              <tr>
                <td colSpan={4}>No WINDFOR publication for this delivery time.</td>
              </tr>
            ) : (
              detail.versions.map((version) => (
                <tr key={version.publish_time} className={version.selected ? "is-selected" : undefined}>
                  <td>{formatWhen(version.publish_time)}</td>
                  <td>{formatMw(version.generation_mw, 0)}</td>
                  <td>{version.eligible ? "Yes" : "No"}</td>
                  <td>{version.selected ? "Yes" : "No"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}
