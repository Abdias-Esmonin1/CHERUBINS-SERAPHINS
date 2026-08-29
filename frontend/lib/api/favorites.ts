import { apiClient } from "@/lib/api/client";
import type { ApiSuccess, ApiSuccessPaginated } from "@/types/api";
import type { FavoriteCreate, FavoriteRead } from "@/types/favorite";

export const favoritesApi = {
  /** Auth requise — favoris de current_user uniquement. */
  list: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<ApiSuccessPaginated<FavoriteRead>>("/api/v1/favorites", { params }),

  /** 409 ALREADY_FAVORITED si déjà en favoris. */
  add: (payload: FavoriteCreate) => apiClient.post<ApiSuccess<FavoriteRead>>("/api/v1/favorites", payload),

  /** 204. 404 FAVORITE_NOT_FOUND même si le favori existe mais
   * appartient à quelqu'un d'autre (jamais de 403 révélateur). */
  remove: (songId: string) => apiClient.delete<void>(`/api/v1/favorites/${songId}`),
};
