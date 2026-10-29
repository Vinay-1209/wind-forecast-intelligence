import { describe, expect, it } from "vitest"
import { apiUrl } from "./config.ts"

describe("apiUrl", () => {
  it("uses a configured production origin and ignores a trailing slash", () => {
    expect(apiUrl("/api/health", "https://analysis.example")).toBe(
      "https://analysis.example/api/health",
    )
    expect(apiUrl("/api/health", "https://analysis.example/")).toBe(
      "https://analysis.example/api/health",
    )
  })

  it("stays on the page origin when no API URL is configured", () => {
    expect(apiUrl("/api/analysis/summary", undefined)).toBe("/api/analysis/summary")
    expect(apiUrl("/api/analysis/summary", "")).toBe("/api/analysis/summary")
    expect(apiUrl("/api/analysis/summary", "   ")).toBe("/api/analysis/summary")
  })
})
