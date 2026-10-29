const LONDON: Intl.DateTimeFormatOptions = { timeZone: "Europe/London" }

export function formatMw(value: number | null | undefined, digits = 0): string {
  if (value == null || !Number.isFinite(value)) return "—"
  return `${new Intl.NumberFormat("en-GB", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)} MW`
}

export function formatSignedMw(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return "—"
  const prefix = value > 0 ? "+" : ""
  return prefix + formatMw(value, digits)
}

export function formatWhen(value: string | null | undefined): string {
  if (!value) return "—"
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat("en-GB", {
    ...LONDON,
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZoneName: "short",
  }).format(parsed)
}

export function formatTick(value: string): string {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat("en-GB", {
    ...LONDON,
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(parsed)
}

export function formatDay(value: string): string {
  const [year, month, day] = value.split("-").map(Number)
  if (!year || !month || !day) return value
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(Date.UTC(year, month - 1, day)))
}

export function reasonText(reason: string | null, cutoff: string): string {
  switch (reason) {
    case null:
      return "Included. This is the latest forecast published at or before the cutoff."
    case "no_forecast_for_interval":
      return "Excluded. WINDFOR has no forecast at this delivery time. It is left out of the metrics and is not filled with zero."
    case "no_eligible_forecast":
      return `Excluded. Forecasts exist, but none were published at or before ${cutoff} UK time on the decision day.`
    case "no_actual":
      return "Excluded. A forecast was published, but there is no wind actual for this delivery time."
    case "missing_interval":
      return "Excluded. This settlement interval has neither a wind actual nor a forecast."
    default:
      return "Excluded from the metrics."
  }
}

export function biasText(label: string | null): string {
  switch (label) {
    case "overforecast":
      return "On average the decision-time forecast was higher than actual wind."
    case "underforecast":
      return "On average the decision-time forecast was lower than actual wind."
    case "no_bias":
      return "The average signed error is zero."
    default:
      return "There are no matched intervals, so bias is not defined."
  }
}
