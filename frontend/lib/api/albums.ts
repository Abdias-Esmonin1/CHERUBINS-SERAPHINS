import { apiClient } from "@/lib/api/client";
import type { ApiSuccess, ApiSuccessPaginated } from "@/types/api";
import type { AlbumCreate, AlbumRead } from "@/types/catalog";

export const albumsApi = {
  list: (params?: { artist_id?: string; page?: number; page_size?: number }) =>
    apiClient.get<ApiSuccessPaginated<AlbumRead>>("/api/v1/albums", { params }),

  getById: (albumId: string) => apiClient.get<ApiSuccess<AlbumRead>>(`/api/v1/albums/${albumId}`),

  /** [ADMIN] */
  create: (payload: AlbumCreate) => apiClient.post<ApiSuccess<AlbumRead>>("/api/v1/albums", payload),
};
