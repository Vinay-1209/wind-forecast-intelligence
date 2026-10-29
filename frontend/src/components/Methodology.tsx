import type { DataQuality } from "../api/types.ts"
import { formatDay, formatWhen } from "../format.ts"

export function Methodology({ quality }: { quality: DataQuality }) {
  const extraNotes = quality.notes.filter((note) => note !== quality.assumption_note)
  const rejected = Object.values(quality.rejected_rows).reduce((sum, count) => sum + count, 0)

  return (
    <section className="panel method" aria-labelledby="method-heading">
      <div className="section-heading">
        <h2 id="method-heading">Method and data quality</h2>
        <p>
          Decisions {formatDay(quality.rules.decision_from)} to {formatDay(quality.rules.decision_to)}.
          Delivery settlement dates {formatDay(quality.rules.delivery_from)} to {formatDay(quality.rules.delivery_to)}.
        </p>
      </div>
      <p>{quality.assumption_note}</p>
      <dl className="formula-list">
        <div>
          <dt>Error</dt>
          <dd>Forecast minus actual, in MW. The sample is the matched intervals in the selected dates, not every half-hour.</dd>
        </div>
        <div>
          <dt>MAE</dt>
          <dd>The average of the absolute errors.</dd>
        </div>
        <div>
          <dt>RMSE</dt>
          <dd>The square root of the average squared error.</dd>
        </div>
        <div>
          <dt>Mean bias</dt>
          <dd>The average of the signed errors. It does not by itself say how many pounds a miss would cost. This study has no prices.</dd>
        </div>
      </dl>
      <p>
        {quality.included_pairs.toLocaleString("en-GB")} matched intervals in this view.
        {quality.metrics_based_on_incomplete_hourly_coverage
          ? " Hourly coverage is incomplete."
          : " Hourly coverage is complete."}{" "}
        {rejected === 0
          ? "No source rows were dropped as invalid or conflicting duplicates."
          : `${rejected.toLocaleString("en-GB")} source rows were dropped or resolved as duplicates.`}
      </p>
      <p>{quality.rules.duplicate_forecast_rule}</p>
      {quality.unexpected_gaps.length === 0 ? (
        <p>No unexpected gaps in this range.</p>
      ) : (
        <>
          <h3>Unexpected gaps</h3>
          <ul>
            {quality.unexpected_gaps.map((start) => (
              <li key={start}>{formatWhen(start)}</li>
            ))}
          </ul>
          {quality.unexpected_gaps_truncated ? <p>Further gaps were omitted from this list.</p> : null}
        </>
      )}
      {extraNotes.length > 0 ? (
        <ul className="notes">
          {extraNotes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : null}
      <p className="snapshot">
        Source snapshot {quality.snapshot_fetched_at ? formatWhen(quality.snapshot_fetched_at) : "time unavailable"}.
        National wind from Elexon FUELHH and WINDFOR only.
      </p>
    </section>
  )
}
