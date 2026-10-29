import { useMemo, useState } from "react"
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type { SeriesPoint } from "../api/types.ts"
import { formatMw, formatTick, formatWhen } from "../format.ts"

interface GenerationChartProps {
  points: SeriesPoint[]
  onSelect: (start: string) => void
}

export function GenerationChart({ points, onSelect }: GenerationChartProps) {
  const [showUnmatched, setShowUnmatched] = useState(false)
  const plotted = useMemo(
    () =>
      showUnmatched
        ? points
        : points.filter((point) => point.reason !== "no_forecast_for_interval"),
    [points, showUnmatched],
  )

  return (
    <section className="panel" aria-labelledby="generation-heading">
      <div className="section-heading">
        <h2 id="generation-heading">Forecast and actual generation</h2>
        <p>
          {showUnmatched
            ? "Forecasts are marked at the hours WINDFOR published. The line is not drawn across the half-hours in between, and those half-hours stay out of the metrics."
            : "Matched hourly intervals only. This is the same set used for the error metrics."}
        </p>
      </div>
      <label className="toggle">
        <input
          type="checkbox"
          checked={showUnmatched}
          onChange={(event) => setShowUnmatched(event.target.checked)}
        />
        Show unmatched half-hour actuals
      </label>
      <div className="chart-frame" role="img" aria-label="Line chart of decision-time wind forecast and actual generation">
        <ResponsiveContainer width="100%" height={380}>
          <LineChart
            data={plotted}
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
              unit=""
            />
            <Tooltip content={<GenerationTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="actual_mw"
              name="Actual"
              stroke="#9a4e16"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="forecast_mw"
              name="Decision-time forecast"
              stroke="#0f6e68"
              strokeWidth={2}
              dot={showUnmatched ? { r: 2.5, fill: "#0f6e68", strokeWidth: 0 } : false}
              connectNulls={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="chart-note">Megawatts, UK time. Select a point to open its publication audit.</p>
    </section>
  )
}

function GenerationTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ payload?: SeriesPoint }>
}) {
  const point = payload?.[0]?.payload
  if (!active || !point) return null
  return (
    <div className="tooltip">
      <p>{formatWhen(point.start_time)}</p>
      <p>Actual {formatMw(point.actual_mw, 0)}</p>
      <p>Forecast {formatMw(point.forecast_mw, 0)}</p>
      {!point.included ? <p>Not in the metrics. {point.reason === "no_forecast_for_interval" ? "No forecast at this half-hour." : "See the audit for the reason."}</p> : null}
    </div>
  )
}
