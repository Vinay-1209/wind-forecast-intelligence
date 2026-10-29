import { useMemo } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type { SeriesPoint } from "../api/types.ts"
import { formatSignedMw, formatTick, formatWhen } from "../format.ts"

interface ErrorPanelProps {
  points: SeriesPoint[]
  largest: SeriesPoint[]
  selectedStart: string | null
  onSelect: (start: string) => void
}

interface ErrorRow extends SeriesPoint {
  over_mw: number | null
  under_mw: number | null
}

export function ErrorPanel({ points, largest, selectedStart, onSelect }: ErrorPanelProps) {
  const rows = useMemo<ErrorRow[]>(
    () =>
      points
        .filter((point) => point.reason !== "no_forecast_for_interval")
        .map((point) => ({
          ...point,
          over_mw: point.error_mw != null && point.error_mw > 0 ? point.error_mw : null,
          under_mw: point.error_mw != null && point.error_mw < 0 ? point.error_mw : null,
        })),
    [points],
  )

  return (
    <section className="split" aria-labelledby="error-heading">
      <div className="panel">
        <div className="section-heading">
          <h2 id="error-heading">Signed error over time</h2>
          <p>Forecast minus actual. Above zero, the desk would have expected more wind than arrived.</p>
        </div>
        <div className="chart-frame" role="img" aria-label="Line chart of signed forecast error in megawatts">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={rows}
              onClick={(state) => {
                if (typeof state.activeLabel === "string") onSelect(state.activeLabel)
              }}
            >
              <CartesianGrid stroke="#e4dccf" vertical={false} />
              <XAxis
                dataKey="start_time"
                tickFormatter={formatTick}
                minTickGap={28}
                tick={{ fill: "#4d453c", fontSize: 12 }}
                axisLine={{ stroke: "#d9d0c3" }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(value: number) =>
                  new Intl.NumberFormat("en-GB", { notation: "compact" }).format(value)
                }
                width={52}
                tick={{ fill: "#4d453c", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <ReferenceLine y={0} stroke="#8a8175" />
              <Tooltip content={<ErrorTooltip />} />
              <Line type="monotone" dataKey="over_mw" name="Forecast high" stroke="#8d3b32" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="under_mw" name="Forecast low" stroke="#1d4e89" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="panel">
        <div className="section-heading">
          <h2>Largest misses</h2>
          <p>The matched hours with the biggest absolute error. These are where the forecast would have moved a purchase the most.</p>
        </div>
        {largest.length === 0 ? (
          <p>No matched intervals in this range.</p>
        ) : (
          <ol className="miss-list">
            {largest.map((point) => (
              <li key={point.start_time}>
                <button
                  type="button"
                  className={point.start_time === selectedStart ? "miss is-selected" : "miss"}
                  aria-pressed={point.start_time === selectedStart}
                  onClick={() => onSelect(point.start_time)}
                >
                  <span>{formatWhen(point.start_time)}</span>
                  <strong>{formatSignedMw(point.error_mw, 0)}</strong>
                </button>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  )
}

function ErrorTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ payload?: SeriesPoint }>
}) {
  const point = payload?.[0]?.payload
  if (!active || !point || point.error_mw == null) return null
  return (
    <div className="tooltip">
      <p>{formatWhen(point.start_time)}</p>
      <p>Error {formatSignedMw(point.error_mw, 0)}</p>
    </div>
  )
}
