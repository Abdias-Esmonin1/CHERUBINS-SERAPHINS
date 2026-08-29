import { apiClient } from "@/lib/api/client";
import type { ApiSuccess, ApiSuccessPaginated } from "@/types/api";
import type {
  TranslationCreate,
  TranslationOwnerRead,
  TranslationUpdate,
  TranslationView,
} from "@/types/translation";

export const translationsApi = {
  /** Autorisé même si les paroles originales ne sont pas AUTHORIZED. */
  submit: (payload: TranslationCreate) =>
    apiClient.post<ApiSuccess<TranslationOwnerRead>>("/api/v1/translations", payload),

  mine: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<ApiSuccessPaginated<TranslationOwnerRead>>("/api/v1/translations/mine", { params }),

  /** Public — retourne une LISTE (une entrée par langue cible), voir
   * TranslationView / isTranslationOwnerView. */
  forLyrics: (lyricsId: string, params?: { target_language_id?: string }) =>
    apiClient.get<ApiSuccess<TranslationView[]>>(`/api/v1/translations/lyrics/${lyricsId}`, { params }),

  update: (translationId: string, payload: TranslationUpdate) =>
    apiClient.put<ApiSuccess<TranslationOwnerRead>>(`/api/v1/translations/${translationId}`, payload),
};
