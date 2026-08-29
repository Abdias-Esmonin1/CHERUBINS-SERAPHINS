import { apiClient } from "@/lib/api/client";
import type { ApiSuccess } from "@/types/api";
import type { LanguageRead } from "@/types/catalog";

/**
 * GET uniquement — même écart que categories (schemas Create/Update
 * existants côté backend, mais pas de router exposant ces routes).
 */
export const languagesApi = {
  list: (params?: { only_active?: boolean }) =>
    apiClient.get<ApiSuccess<LanguageRead[]>>("/api/v1/languages", { params }),
};
