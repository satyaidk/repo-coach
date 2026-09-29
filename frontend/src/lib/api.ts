import type { ExplainResult, ProvidersResponse, Report } from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

export class ApiError extends Error {}

async function request<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      `Can't reach the RepoCompass API at ${API_URL}. Start it by running \`python -m repocompass\` in the backend folder.`,
    );
  }

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON error page; handled below.
  }
  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    if (typeof detail === "string") throw new ApiError(detail);
    if (Array.isArray(detail)) throw new ApiError(detail.map((d: { msg?: string }) => d.msg).join("; "));
    throw new ApiError(`Request failed with status ${response.status}.`);
  }
  return data as T;
}

export const api = {
  providers: () => request<ProvidersResponse>("/api/providers"),
  analyze: (url: string) => request<Report>("/api/analyze", { url }),
  explain: (url: string, provider: string, model: string | null, refresh = false) =>
    request<ExplainResult>("/api/explain", { url, provider, model, refresh }),
};
