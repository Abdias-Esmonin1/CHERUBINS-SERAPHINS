export interface CategoryRead {
  id: string;
  name: string;
  description: string | null;
}

export interface LanguageRead {
  id: string;
  code: string;
  name: string;
  native_name: string | null;
  is_active: boolean;
}

export interface ArtistRead {
  id: string;
  name: string;
  slug: string;
  biography: string | null;
  country: string | null;
  image_url: string | null;
  official_links: Record<string, unknown> | null;
  is_verified: boolean;
}

/** Contrat exact ArtistCreate — pas de `slug` (généré côté serveur). */
export interface ArtistCreate {
  name: string;
  biography?: string | null;
  country?: string | null;
  image_url?: string | null;
  official_links?: Record<string, unknown> | null;
}

export interface AlbumRead {
  id: string;
  artist_id: string;
  title: string;
  release_year: number | null;
  cover_url: string | null;
}

export interface AlbumCreate {
  artist_id: string;
  title: string;
  release_year?: number | null;
  cover_url?: string | null;
}

/** Structures imbriquées "brief" utilisées dans SongRead/FavoriteRead. */
export interface ArtistBrief {
  id: string;
  name: string;
  slug: string;
}

export interface AlbumBrief {
  id: string;
  title: string;
}

export interface CategoryBrief {
  id: string;
  name: string;
}

export interface LanguageBrief {
  id: string;
  code: string;
  name: string;
}

/** songs.status CHECK IN ('DRAFT','PUBLISHED','ARCHIVED') — docs/04-database/database.md. */
export type SongStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

/**
 * Contrat exact SongRead (backend/app/schemas/song.py).
 * `lyrics_available` n'existe volontairement PAS dans ce schéma
 * (écart documenté, docs/05-api/api.md) — ne pas l'ajouter ici. Pour
 * connaître la disponibilité réelle des paroles, appeler
 * GET /lyrics/song/{song_id} (voir lib/api/lyrics.ts).
 */
export interface SongRead {
  id: string;
  title: string;
  slug: string;
  status: SongStatus;
  cover_url: string | null;
  external_provider: string | null;
  external_id: string | null;
  external_url: string | null;
  artist: ArtistBrief;
  album: AlbumBrief | null;
  category: CategoryBrief | null;
  original_language: LanguageBrief;
}

/** `status` n'est pas fourni par le client : forcé à DRAFT à la création. */
export interface SongCreate {
  title: string;
  artist_id: string;
  album_id?: string | null;
  category_id?: string | null;
  original_language_id: string;
  cover_url?: string | null;
  external_provider?: string | null;
  external_id?: string | null;
  external_url?: string | null;
}

export interface SongUpdate {
  title?: string;
  album_id?: string | null;
  category_id?: string | null;
  cover_url?: string | null;
  status?: SongStatus;
  external_provider?: string | null;
  external_id?: string | null;
  external_url?: string | null;
}
