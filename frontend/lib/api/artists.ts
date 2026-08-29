import { apiClient } from "@/lib/api/client";
import type { ApiSuccess, ApiSuccessPaginated } from "@/types/api";
import type { ArtistCreate, ArtistRead } from "@/types/catalog";

export const artistsApi = {
  list: (params?: { country?: string; is_verified?: boolean; page?: number; page_size?: number }) =>
    apiClient.get<ApiSuccessPaginated<ArtistRead>>("/api/v1/artists", { params }),

  getBySlug: (slug: string) => apiClient.get<ApiSuccess<ArtistRead>>(`/api/v1/artists/${slug}`),

  /** [ADMIN] `slug` généré côté serveur, jamais fourni par le client. */
  create: (payload: ArtistCreate) => apiClient.post<ApiSuccess<ArtistRead>>("/api/v1/artists", payload),
};
