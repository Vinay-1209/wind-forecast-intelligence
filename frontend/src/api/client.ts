import type { DataQuality, DateRange, ForecastDetails, Summary, Timeseries } from "./types.ts"
import { apiUrl } from "./config.ts"

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

function endpoint(path: string): string {
  return apiUrl(path, import.meta.env.VITE_API_URL)
}

async function getJson<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(endpoint(path))
  } catch {
    throw new ApiError("The analysis service could not be reached.", 0)
  }
  if (!response.ok) {
    let detail = ""
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === "string") detail = body.detail
    } catch {
      detail = ""
    }
    throw new ApiError(detail || "The analysis service returned an error.", response.status)
  }
  return (await response.json()) as T
}

function rangeQuery(range: DateRange): string {
  return new URLSearchParams({
    delivery_from: range.from,
    delivery_to: range.to,
  }).toString()
}

export function getSummary(range: DateRange): Promise<Summary> {
  return getJson(`/api/analysis/summary?${rangeQuery(range)}`)
}

export function getTimeseries(range: DateRange): Promise<Timeseries> {
  return getJson(`/api/analysis/timeseries?${rangeQuery(range)}`)
}

export function getQuality(range: DateRange): Promise<DataQuality> {
  return getJson(`/api/analysis/data-quality?${rangeQuery(range)}`)
}

export function getDetails(start: string): Promise<ForecastDetails> {
  const query = new URLSearchParams({ start })
  return getJson(`/api/analysis/forecast-details?${query.toString()}`)
}
