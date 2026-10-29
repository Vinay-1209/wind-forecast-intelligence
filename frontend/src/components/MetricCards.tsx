import type { Summary } from "../api/types.ts"
import { biasText, formatDay, formatMw, formatSignedMw } from "../format.ts"

export function MetricCards({ summary }: { summary: Summary }) {
  const incomplete = summary.metrics_based_on_incomplete_hourly_coverage
  const halfHours = summary.excluded_by_reason.no_forecast_for_interval ?? 0

  return (
    <section className="metrics" aria-labelledby="metrics-heading">
      <div className="section-heading">
        <h2 id="metrics-heading">Forecast accuracy</h2>
        <p>
          {formatDay(summary.delivery_from)} to {formatDay(summary.delivery_to)}.{" "}
          {summary.included_pairs.toLocaleString("en-GB")} matched intervals.
          {incomplete ? " Hourly coverage is incomplete, so these averages describe only the matched hours." : " Every hourly slot in this range is matched."}
        </p>
      </div>
      <div className="metric-grid">
        <article className="metric">
          <h3>Mean absolute error</h3>
          <p className="metric-value">{formatMw(summary.mae_mw, 1)}</p>
          <p>Average size of the miss. Lower means the forecast was closer to actual wind.</p>
        </article>
        <article className="metric">
          <h3>Root mean squared error</h3>
          <p className="metric-value">{formatMw(summary.rmse_mw, 1)}</p>
          <p>Like the average miss, but a few large misses pull it up more than MAE.</p>
        </article>
        <article className="metric">
          <h3>Mean bias</h3>
          <p className="metric-value">{formatSignedMw(summary.mbe_mw, 1)}</p>
          <p>{biasText(summary.bias_label)} Positive means the forecast was higher than actual.</p>
        </article>
      </div>
      <p className="coverage">
        Actuals present for {summary.actuals_present.toLocaleString("en-GB")} of{" "}
        {summary.expected_intervals.toLocaleString("en-GB")} half-hours.{" "}
        {summary.hourly_slots_included.toLocaleString("en-GB")} of{" "}
        {summary.hourly_slots.toLocaleString("en-GB")} hourly slots have a decision-time forecast.{" "}
        {halfHours.toLocaleString("en-GB")} half-hours have an actual and no forecast at the same time.
      </p>
    </section>
  )
}
