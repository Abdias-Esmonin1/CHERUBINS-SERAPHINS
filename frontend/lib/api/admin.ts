import { apiClient } from "@/lib/api/client";
import type { ApiSuccess, ApiSuccessPaginated } from "@/types/api";
import type {
  AdminStatsRead,
  ModerationAuthorizeRequest,
  ModerationReasonRequest,
  RightsRecordAction,
  RightsRecordRead,
} from "@/types/admin";
import type { AuthorizationStatus, LyricsOwnerRead } from "@/types/lyrics";
import type { TranslationOwnerRead } from "@/types/translation";

/** Toutes les routes ci-dessous exigent require_admin côté backend. */
export const adminApi = {
  lyrics: {
    list: (params?: { status?: AuthorizationStatus; page?: number; page_size?: number }) =>
      apiClient.get<ApiSuccessPaginated<LyricsOwnerRead>>("/api/v1/admin/lyrics", { params }),

    get: (lyricsId: string) => apiClient.get<ApiSuccess<LyricsOwnerRead>>(`/api/v1/admin/lyrics/${lyricsId}`),

    /** PENDING -> AUTHORIZED ou EXPIRED(effectif) -> AUTHORIZED. */
    authorize: (lyricsId: string, payload: ModerationAuthorizeRequest) =>
      apiClient.patch<ApiSuccess<LyricsOwnerRead>>(`/api/v1/admin/lyrics/${lyricsId}/authorize`, payload),

    /** PENDING -> REJECTED uniquement. `reason` obligatoire. */
    reject: (lyricsId: string, payload: ModerationReasonRequest) =>
      apiClient.patch<ApiSuccess<LyricsOwnerRead>>(`/api/v1/admin/lyrics/${lyricsId}/reject`, payload),

    /** AUTHORIZED -> REVOKED uniquement. `reason` obligatoire. */
    revoke: (lyricsId: string, payload: ModerationReasonRequest) =>
      apiClient.patch<ApiSuccess<LyricsOwnerRead>>(`/api/v1/admin/lyrics/${lyricsId}/revoke`, payload),
  },

  translations: {
    list: (params?: { status?: AuthorizationStatus; page?: number; page_size?: number }) =>
      apiClient.get<ApiSuccessPaginated<TranslationOwnerRead>>("/api/v1/admin/translations", { params }),

    get: (translationId: string) =>
      apiClient.get<ApiSuccess<TranslationOwnerRead>>(`/api/v1/admin/translations/${translationId}`),

    authorize: (translationId: string, payload: ModerationAuthorizeRequest) =>
      apiClient.patch<ApiSuccess<TranslationOwnerRead>>(
        `/api/v1/admin/translations/${translationId}/authorize`,
        payload
      ),

    reject: (translationId: string, payload: ModerationReasonRequest) =>
      apiClient.patch<ApiSuccess<TranslationOwnerRead>>(
        `/api/v1/admin/translations/${translationId}/reject`,
        payload
      ),

    revoke: (translationId: string, payload: ModerationReasonRequest) =>
      apiClient.patch<ApiSuccess<TranslationOwnerRead>>(
        `/api/v1/admin/translations/${translationId}/revoke`,
        payload
      ),
  },

  /** Append-only : GET uniquement, aucune méthode d'écriture. */
  rightsRecords: {
    list: (params?: {
      lyrics_id?: string;
      translation_id?: string;
      action?: RightsRecordAction;
      performed_by_user_id?: string;
      page?: number;
      page_size?: number;
    }) => apiClient.get<ApiSuccessPaginated<RightsRecordRead>>("/api/v1/admin/rights-records", { params }),
  },

  stats: {
    get: () => apiClient.get<ApiSuccess<AdminStatsRead>>("/api/v1/admin/stats"),
  },
};
