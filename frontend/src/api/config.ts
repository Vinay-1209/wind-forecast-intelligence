/** Join a path to the configured API origin. An empty origin uses the page origin. */
export function apiUrl(path: string, configured: string | undefined): string {
  const base = (configured ?? "").trim().replace(/\/$/, "")
  const suffix = path.startsWith("/") ? path : `/${path}`
  return `${base}${suffix}`
}
