import { apiClient } from "@/lib/api/client";
import type { ApiSuccess, ApiSuccessPaginated } from "@/types/api";
import type { LyricsCreate, LyricsOwnerRead, LyricsSongView, LyricsUpdate } from "@/types/lyrics";

export const lyricsApi = {
  /** Auth requise. `submitted_by_user_id`/`authorization_status` forcés
   * côté serveur. 409 LYRICS_ALREADY_EXISTS si des paroles existent
   * déjà pour cette chanson. */
  submit: (payload: LyricsCreate) => apiClient.post<ApiSuccess<LyricsOwnerRead>>("/api/v1/lyrics", payload),

  /** Auth requise — soumissions propres, tous statuts, IDOR-safe. */
  mine: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<ApiSuccessPaginated<LyricsOwnerRead>>("/api/v1/lyrics/mine", { params }),

  /** Public (auth optionnelle) — toujours 200, jamais 403/404 pour
   * absence de contenu. Voir LyricsSongView / isLyricsOwnerView. */
  forSong: (songId: string) => apiClient.get<ApiSuccess<LyricsSongView>>(`/api/v1/lyrics/song/${songId}`),

  /** Auteur (si PENDING) ou ADMIN. 409 LYRICS_ALREADY_REVIEWED sinon. */
  update: (lyricsId: string, payload: LyricsUpdate) =>
    apiClient.put<ApiSuccess<LyricsOwnerRead>>(`/api/v1/lyrics/${lyricsId}`, payload),
};
