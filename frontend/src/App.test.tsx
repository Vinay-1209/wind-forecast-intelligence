import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import type { ReactNode } from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import App from "./App.tsx"
import { details, excludedDetails, quality, series, summary } from "./test/fixtures.ts"

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children?: ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children?: ReactNode }) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  CartesianGrid: () => null,
  Legend: () => null,
  ReferenceLine: () => null,
}))

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function installFetch() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes("/api/analysis/summary")) return jsonResponse(summary)
    if (url.includes("/api/analysis/timeseries")) return jsonResponse(series)
    if (url.includes("/api/analysis/data-quality")) return jsonResponse(quality)
    if (url.includes("/api/analysis/forecast-details")) return jsonResponse(details)
    return jsonResponse({ detail: "missing" }, 404)
  })
  vi.stubGlobal("fetch", fetchMock)
  return fetchMock
}

describe("App", () => {
  beforeEach(() => {
    vi.unstubAllGlobals()
  })

  it("shows a loading state before the analysis arrives", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)))
    render(<App />)
    expect(screen.getByRole("status")).toHaveTextContent("Loading the January wind analysis")
  })

  it("shows the metrics, cutoff, and bias once the analysis loads", async () => {
    installFetch()
    render(<App />)
    expect(await screen.findByText("1,995.6 MW")).toBeInTheDocument()
    expect(screen.getByText("2,498.8 MW")).toBeInTheDocument()
    expect(screen.getByText("+1,728.0 MW")).toBeInTheDocument()
    expect(screen.getByText(/Decision cutoff 09:50 UK time/)).toBeInTheDocument()
    expect(screen.getByText(/higher than actual wind/)).toBeInTheDocument()
    expect(await screen.findAllByText("18,883 MW")).not.toHaveLength(0)
    expect(screen.getByText(/latest forecast published at or before the cutoff/)).toBeInTheDocument()
    expect(screen.getByText(/not stored as zero error/)).toBeInTheDocument()
  })

  it("leaves the metrics blank when nothing matched", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input)
        if (url.includes("/summary")) {
          return jsonResponse({
            ...summary,
            included_pairs: 0,
            mae_mw: null,
            rmse_mw: null,
            mbe_mw: null,
            bias_label: null,
            largest_absolute_errors: [],
            hourly_slots_included: 0,
            metrics_based_on_incomplete_hourly_coverage: true,
          })
        }
        if (url.includes("/timeseries")) return jsonResponse({ ...series, points: [] })
        if (url.includes("/data-quality")) {
          return jsonResponse({ ...quality, included_pairs: 0, notes: [quality.assumption_note] })
        }
        return jsonResponse({ detail: "unexpected" }, 500)
      }),
    )
    render(<App />)
    expect(await screen.findByRole("heading", { name: "No matched intervals" })).toBeInTheDocument()
    expect(screen.getAllByText("—").length).toBeGreaterThan(0)
    expect(screen.queryByText("0.0 MW")).not.toBeInTheDocument()
    expect(screen.queryByText("0 MW")).not.toBeInTheDocument()
  })

  it("shows the service error and retries", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(
        { detail: "Analysis snapshot is not available. Run scripts/refresh_snapshot.py." },
        503,
      ),
    )
    vi.stubGlobal("fetch", fetchMock)
    render(<App />)
    expect(await screen.findByRole("alert")).toHaveTextContent("Analysis snapshot is not available")
    fireEvent.click(screen.getByRole("button", { name: "Try again" }))
    await waitFor(() => expect(fetchMock.mock.calls.length).toBeGreaterThan(3))
  })

  it("requests the selected delivery dates", async () => {
    const fetchMock = installFetch()
    render(<App />)
    await screen.findByText("1,995.6 MW")
    fireEvent.change(screen.getByLabelText("Delivery from"), { target: { value: "2026-01-10" } })
    fireEvent.change(screen.getByLabelText("Delivery to"), { target: { value: "2026-01-12" } })
    fireEvent.click(screen.getByRole("button", { name: "Apply" }))
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((call) => String(call[0]))
      expect(urls.some((url) => url.includes("delivery_from=2026-01-10"))).toBe(true)
      expect(urls.some((url) => url.includes("delivery_to=2026-01-12"))).toBe(true)
    })
  })
})

describe("excluded interval", () => {
  it("keeps the previous interval on screen while the next one loads", async () => {
    const { IntervalAudit } = await import("./components/IntervalAudit.tsx")
    render(<IntervalAudit detail={details} status="loading" error={null} />)
    expect(screen.getByRole("status")).toHaveTextContent("Loading this interval")
    expect(screen.getAllByText("18,883 MW").length).toBeGreaterThan(0)
    expect(document.querySelector(".audit-slot")).toHaveClass("is-loading")
  })

  it("shows a missing forecast without turning it into zero", async () => {
    const { IntervalAudit } = await import("./components/IntervalAudit.tsx")
    render(<IntervalAudit detail={excludedDetails} status="ready" error={null} />)
    expect(screen.getByText(/not filled with zero/)).toBeInTheDocument()
    expect(screen.getByText("14,000 MW")).toBeInTheDocument()
    expect(screen.queryByText("0 MW")).not.toBeInTheDocument()
    expect(screen.getByText("No WINDFOR publication for this delivery time.")).toBeInTheDocument()
  })
})
