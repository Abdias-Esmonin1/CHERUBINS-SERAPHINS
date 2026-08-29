import type { SongRead } from "@/types/catalog";

/** FavoriteRead imbrique la fiche chanson complète (SongRead), pas
 * seulement song_id — reflet exact de backend/app/schemas/favorite.py. */
export interface FavoriteRead {
  id: string;
  song: SongRead;
  created_at: string;
}

/** `user_id` structurellement absent — toujours current_user.id côté
 * serveur (protection IDOR par construction). */
export interface FavoriteCreate {
  song_id: string;
}
