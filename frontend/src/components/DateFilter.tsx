import { formatDay } from "../format.ts"
import { STUDY_FROM, STUDY_TO } from "../study.ts"

interface DateFilterProps {
  from: string
  to: string
  busy: boolean
  onFrom: (value: string) => void
  onTo: (value: string) => void
  onApply: () => void
  onReset: () => void
}

export function DateFilter({ from, to, busy, onFrom, onTo, onApply, onReset }: DateFilterProps) {
  const invalid = from > to
  const atStudyWindow = from === STUDY_FROM && to === STUDY_TO

  return (
    <form
      className="filters"
      onSubmit={(event) => {
        event.preventDefault()
        if (!invalid) onApply()
      }}
    >
      <div className="filter-field">
        <label htmlFor="delivery-from">Delivery from</label>
        <input
          id="delivery-from"
          type="date"
          min={STUDY_FROM}
          max={STUDY_TO}
          value={from}
          onChange={(event) => onFrom(event.target.value)}
        />
      </div>
      <div className="filter-field">
        <label htmlFor="delivery-to">Delivery to</label>
        <input
          id="delivery-to"
          type="date"
          min={STUDY_FROM}
          max={STUDY_TO}
          value={to}
          onChange={(event) => onTo(event.target.value)}
        />
      </div>
      <div className="filter-actions">
        <button type="submit" className="button primary" disabled={busy || invalid}>
          {busy ? "Updating…" : "Apply"}
        </button>
        <button type="button" className="button" onClick={onReset} disabled={busy || atStudyWindow}>
          Reset
        </button>
      </div>
      {invalid ? (
        <p className="filter-error" role="alert">
          The start date has to be on or before the end date.
        </p>
      ) : (
        <p className="filter-hint">
          Settlement dates from {formatDay(STUDY_FROM)} to {formatDay(STUDY_TO)}.
        </p>
      )}
    </form>
  )
}
