import type { ForecastDetails } from "../api/types.ts"
import { formatDay, formatMw, formatSignedMw, formatWhen, reasonText } from "../format.ts"

export function IntervalAudit({
  detail,
  status,
  error,
}: {
  detail: ForecastDetails | null
  status: "idle" | "loading" | "ready" | "error"
  error: string | null
}) {
  return (
    <section className="panel" aria-labelledby="audit-heading">
      <div className="section-heading">
        <h2 id="audit-heading">Why this interval was scored</h2>
        <p>Each row is a WINDFOR publication for the selected delivery time. Only the latest one at or before the cutoff can enter the metrics.</p>
      </div>
      {status === "loading" ? <p role="status">Loading this interval…</p> : null}
      {status === "error" ? <p role="alert">{error}</p> : null}
      {detail ? <AuditBody detail={detail} /> : null}
      {status === "idle" && !detail ? <p>Select an interval from the chart or the largest misses.</p> : null}
    </section>
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
