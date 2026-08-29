import { apiClient } from "@/lib/api/client";
import type { ApiSuccess, ApiSuccessPaginated } from "@/types/api";
import type { SongCreate, SongRead, SongUpdate } from "@/types/catalog";

export const songsApi = {
  /** Ne retourne que status = PUBLISHED (appliqué côté backend). */
  list: (params?: {
    category_id?: string;
    language_id?: string;
    artist_id?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<ApiSuccessPaginated<SongRead>>("/api/v1/songs", { params }),

  /** `q` obligatoire (422 sinon). Ne recherche PAS dans les paroles
   * (écart documenté, ILIKE sur title/artist.name uniquement). */
  search: (params: {
    q: string;
    category_id?: string;
    language_id?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<ApiSuccessPaginated<SongRead>>("/api/v1/songs/search", { params }),

  getBySlug: (slug: string) => apiClient.get<ApiSuccess<SongRead>>(`/api/v1/songs/${slug}`),

  /** [ADMIN] `slug` généré serveur, `status` forcé à DRAFT. */
  create: (payload: SongCreate) => apiClient.post<ApiSuccess<SongRead>>("/api/v1/songs", payload),

  /** [ADMIN] Seul endpoint permettant la transition DRAFT -> PUBLISHED. */
  update: (songId: string, payload: SongUpdate) =>
    apiClient.put<ApiSuccess<SongRead>>(`/api/v1/songs/${songId}`, payload),
};
