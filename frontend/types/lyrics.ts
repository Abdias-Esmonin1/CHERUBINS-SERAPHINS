import type { LanguageBrief } from "@/types/catalog";

/** lyrics.source_type CHECK — backend/app/schemas/lyrics.py (SourceType). */
export type LyricsSourceType =
  | "ORIGINAL"
  | "ARTIST"
  | "RIGHTS_HOLDER"
  | "LICENSE"
  | "PARTNER"
  | "PUBLIC_DOMAIN"
  | "USER_SUBMITTED";

/** authorization_status CHECK, partagé lyrics/translations/rights_records
 * — docs/04-database/database.md. EXPIRED est un statut effectif calculé,
 * jamais littéralement écrit en base, mais reste une valeur possible sur
 * le fil (ex. GET /lyrics/mine d'un auteur). */
export type AuthorizationStatus = "PENDING" | "AUTHORIZED" | "REJECTED" | "EXPIRED" | "REVOKED";

/**
 * Vue publique — GET /lyrics/song/{song_id} pour un visiteur non
 * autorisé à voir le contenu réel (non-auteur, non-ADMIN, ou statut
 * != AUTHORIZED / expiré). Structurellement séparée de LyricsOwnerRead :
 * ne contient AUCUN champ interne (statut, source, droits...).
 */
export interface LyricsVisibilityRead {
  available: boolean;
  language: LanguageBrief | null;
  content: string | null;
}

/** Vue enrichie — auteur de la soumission ou ADMIN uniquement. */
export interface LyricsOwnerRead {
  id: string;
  song_id: string;
  language: LanguageBrief;
  content: string;
  source_type: LyricsSourceType;
  source_url: string | null;
  rights_holder: string | null;
  authorization_status: AuthorizationStatus;
  authorization_reference: string | null;
  authorization_date: string | null;
  expiration_date: string | null;
  submitted_by_user_id: string | null;
  reviewed_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * GET /lyrics/song/{song_id} renvoie l'une ou l'autre forme selon le
 * viewer (backend/app/services/lyrics_service.py:get_visibility), sans
 * discriminant explicite sur le fil JSON. Utiliser isLyricsOwnerView
 * pour distinguer les deux à l'exécution.
 */
export type LyricsSongView = LyricsVisibilityRead | LyricsOwnerRead;

export function isLyricsOwnerView(view: LyricsSongView): view is LyricsOwnerRead {
  return "authorization_status" in view;
}

/** `submitted_by_user_id`/`authorization_status` structurellement absents
 * — forcés côté serveur, jamais fournis par le client. */
export interface LyricsCreate {
  song_id: string;
  language_id: string;
  content: string;
  source_type: LyricsSourceType;
  source_url?: string | null;
  rights_holder?: string | null;
}

/** Édition — uniquement le contenu, `song_id`/`language_id`/`source_type`/
 * `submitted_by_user_id`/`authorization_status`/`reviewed_by_user_id`
 * structurellement absents. */
export interface LyricsUpdate {
  content?: string;
  source_url?: string | null;
  rights_holder?: string | null;
}
