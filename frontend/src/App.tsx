import { lazy, Suspense, useEffect, useState } from "react"
import { ApiError, getDetails, getQuality, getSummary, getTimeseries } from "./api/client.ts"
import type { DataQuality, ForecastDetails, Summary, Timeseries } from "./api/types.ts"
import { DateFilter } from "./components/DateFilter.tsx"
import { IntervalAudit } from "./components/IntervalAudit.tsx"
import { MetricCards } from "./components/MetricCards.tsx"
import { Methodology } from "./components/Methodology.tsx"
import { EmptyState, ErrorState, LoadingState } from "./components/Status.tsx"
import { formatDay } from "./format.ts"
import { STUDY_FROM, STUDY_TO } from "./study.ts"

const GenerationChart = lazy(() =>
  import("./components/GenerationChart.tsx").then((module) => ({ default: module.GenerationChart })),
)
const ErrorPanel = lazy(() =>
  import("./components/ErrorPanel.tsx").then((module) => ({ default: module.ErrorPanel })),
)

interface DashboardData {
  summary: Summary
  series: Timeseries
  quality: DataQuality
}

function messageFrom(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return "The analysis service could not be reached."
}

export default function App() {
  const [draftFrom, setDraftFrom] = useState(STUDY_FROM)
  const [draftTo, setDraftTo] = useState(STUDY_TO)
  const [from, setFrom] = useState(STUDY_FROM)
  const [to, setTo] = useState(STUDY_TO)
  const [attempt, setAttempt] = useState(0)
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading")
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<DashboardData | null>(null)
  const [selectedStart, setSelectedStart] = useState<string | null>(null)
  const [detail, setDetail] = useState<ForecastDetails | null>(null)
  const [detailStatus, setDetailStatus] = useState<"idle" | "loading" | "ready" | "error">("idle")
  const [detailError, setDetailError] = useState<string | null>(null)
  const [startedKey, setStartedKey] = useState<string | null>(null)
  const [detailFor, setDetailFor] = useState<string | null>(null)
  const requestKey = `${from}|${to}|${attempt}`
  if (startedKey !== requestKey) {
    setStartedKey(requestKey)
    setStatus("loading")
    setError(null)
  }
  if (detailFor !== selectedStart) {
    setDetailFor(selectedStart)
    setDetail(null)
    setDetailError(null)
    setDetailStatus(selectedStart ? "loading" : "idle")
  }

  useEffect(() => {
    let cancelled = false
    Promise.all([
      getSummary({ from, to }),
      getTimeseries({ from, to }),
      getQuality({ from, to }),
    ])
      .then(([summary, series, quality]) => {
        if (cancelled) return
        setData({ summary, series, quality })
        setStatus("ready")
        setSelectedStart((current) => {
          const stillVisible =
            current != null && series.points.some((point) => point.start_time === current)
          if (stillVisible) return current
          return (
            summary.largest_absolute_errors[0]?.start_time ??
            series.points.find((point) => point.included)?.start_time ??
            null
          )
        })
      })
      .catch((caught: unknown) => {
        if (cancelled) return
        setStatus("error")
        setError(messageFrom(caught))
      })
    return () => {
      cancelled = true
    }
  }, [from, to, attempt])

  useEffect(() => {
    if (!selectedStart) return
    let cancelled = false
    getDetails(selectedStart)
      .then((next) => {
        if (cancelled) return
        setDetail(next)
        setDetailStatus("ready")
      })
      .catch((caught: unknown) => {
        if (cancelled) return
        setDetail(null)
        setDetailStatus("error")
        setDetailError(messageFrom(caught))
      })
    return () => {
      cancelled = true
    }
  }, [selectedStart])

  const cutoff = data?.summary.rules.cutoff_time ?? "09:50"

  return (
    <div className="page">
      <header className="masthead">
        <p className="eyebrow">UK day-ahead procurement</p>
        <h1>Wind Forecast Intelligence</h1>
        <p className="lede">
          The national wind forecast a buyer could see before the day-ahead cutoff, set against
          what was actually generated.
        </p>
      </header>
      <div className="notice">
        <strong>Decision cutoff {cutoff} UK time</strong>
        <span>
          {" "}
          on the day before delivery. A forecast published at that minute still counts. Anything
          later is ignored, including updates on the delivery day.
        </span>
      </div>
      <main>
        <DateFilter
          from={draftFrom}
          to={draftTo}
          busy={status === "loading"}
          onFrom={setDraftFrom}
          onTo={setDraftTo}
          onApply={() => {
            setFrom(draftFrom)
            setTo(draftTo)
          }}
          onReset={() => {
            setDraftFrom(STUDY_FROM)
            setDraftTo(STUDY_TO)
            setFrom(STUDY_FROM)
            setTo(STUDY_TO)
          }}
        />
        {status === "loading" && data ? (
          <p className="updating" role="status">
            Updating figures…
          </p>
        ) : null}
        {status === "loading" && !data ? <LoadingState /> : null}
        {status === "error" && !data ? (
          <ErrorState
            message={error ?? "The analysis could not be loaded."}
            onRetry={() => setAttempt((value) => value + 1)}
          />
        ) : null}
        {status === "error" && data ? (
          <p className="status error" role="alert">
            {error}
          </p>
        ) : null}
        {data ? (
          <>
            <p className="period">
              Showing deliveries {formatDay(data.summary.delivery_from)} to{" "}
              {formatDay(data.summary.delivery_to)}.
            </p>
            <MetricCards summary={data.summary} />
            {data.summary.included_pairs === 0 ? (
              <EmptyState />
            ) : (
              <>
                <Suspense fallback={<p role="status">Loading charts…</p>}>
                  <GenerationChart points={data.series.points} onSelect={setSelectedStart} />
                  <ErrorPanel
                    points={data.series.points}
                    largest={data.summary.largest_absolute_errors}
                    selectedStart={selectedStart}
                    onSelect={setSelectedStart}
                  />
                </Suspense>
                <IntervalAudit detail={detail} status={detailStatus} error={detailError} />
              </>
            )}
            <Methodology quality={data.quality} />
          </>
        ) : null}
      </main>
    </div>
  )
}
