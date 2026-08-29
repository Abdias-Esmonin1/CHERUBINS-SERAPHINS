import { apiClient } from "@/lib/api/client";
import type { ApiSuccess } from "@/types/api";
import type { LoginRequest, RegisterRequest } from "@/types/auth";
import type { UserPublicRead } from "@/types/user";

export const authApi = {
  register: (payload: RegisterRequest) =>
    apiClient.post<ApiSuccess<UserPublicRead>>("/api/v1/auth/register", payload),

  login: (payload: LoginRequest) =>
    apiClient.post<ApiSuccess<UserPublicRead>>("/api/v1/auth/login", payload),

  /** 204 No Content — idempotent, aucune auth requise. */
  logout: () => apiClient.post<void>("/api/v1/auth/logout"),

  me: () => apiClient.get<ApiSuccess<UserPublicRead>>("/api/v1/auth/me"),
};
