import type { ApiBusinessError, ApiValidationError } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;
  readonly fieldErrors: Record<string, string[]>;

  constructor(
    status: number,
    code: string,
    message: string,
    details: unknown = null,
    fieldErrors: Record<string, string[]> = {}
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.fieldErrors = fieldErrors;
  }
}

function isBusinessError(body: unknown): body is ApiBusinessError {
  return (
    typeof body === "object" &&
    body !== null &&
    "error" in body &&
    typeof (body as ApiBusinessError).error === "object"
  );
}

function isValidationError(body: unknown): body is ApiValidationError {
  return (
    typeof body === "object" &&
    body !== null &&
    "detail" in body &&
    Array.isArray((body as ApiValidationError).detail)
  );
}

/**
 * Le backend a deux formats d'erreur (écart documenté, non corrigé côté
 * backend, voir docs/05-api/api.md) :
 *   - erreurs métier : {"error": {"code","message","details"}}
 *   - erreurs 422 Pydantic natives FastAPI : {"detail": [...]}
 * Cette fonction normalise les deux vers ApiClientError.
 */
function toApiClientError(status: number, body: unknown): ApiClientError {
  if (isBusinessError(body)) {
    const { code, message, details } = body.error;
    return new ApiClientError(status, code, message, details);
  }

  if (isValidationError(body)) {
    const fieldErrors: Record<string, string[]> = {};
    for (const issue of body.detail) {
      const field = issue.loc.filter((part) => part !== "body").join(".") || "_";
      fieldErrors[field] = [...(fieldErrors[field] ?? []), issue.msg];
    }
    return new ApiClientError(
      status,
      "VALIDATION_ERROR",
      "Certaines données envoyées sont invalides.",
      body.detail,
      fieldErrors
    );
  }

  return new ApiClientError(status, "UNKNOWN_ERROR", "Une erreur inattendue est survenue.");
}

interface RequestOptions {
  params?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
}

function buildUrl(path: string, params?: RequestOptions["params"]): string {
  const url = new URL(path, API_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function request<T>(
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T> {
  const response = await fetch(buildUrl(path, options?.params), {
    method,
    credentials: "include",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: options?.signal,
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const parsed = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    throw toApiClientError(response.status, parsed);
  }

  return parsed as T;
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>("GET", path, undefined, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("POST", path, body, options),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PUT", path, body, options),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PATCH", path, body, options),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>("DELETE", path, undefined, options),
};
