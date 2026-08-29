import type { AuthorizationStatus } from "@/types/lyrics";

/** rights_records.action CHECK IN ('VALIDATED','REJECTED','REVOKED'). */
export type RightsRecordAction = "VALIDATED" | "REJECTED" | "REVOKED";

/**
 * Sortie uniquement — pas de RightsRecordCreate/Update : la table
 * n'est jamais alimentée directement par un endpoint, uniquement en
 * interne par moderation_service.py (append-only strict).
 */
export interface RightsRecordRead {
  id: string;
  lyrics_id: string | null;
  translation_id: string | null;
  action: RightsRecordAction;
  previous_status: AuthorizationStatus | null;
  new_status: AuthorizationStatus;
  reason: string | null;
  performed_by_user_id: string | null;
  created_at: string;
}

/** Body pour PATCH .../authorize — identique lyrics et translations. */
export interface ModerationAuthorizeRequest {
  authorization_reference?: string | null;
  authorization_date?: string | null;
  expiration_date?: string | null;
}

/** Body pour PATCH .../reject et .../revoke — reason obligatoire. */
export interface ModerationReasonRequest {
  reason: string;
}

export interface LyricsStatusCounts {
  PENDING: number;
  AUTHORIZED: number;
  REJECTED: number;
  EXPIRED: number;
  REVOKED: number;
}

export interface AdminStatsRead {
  users_count: number;
  songs_count: number;
  artists_count: number;
  albums_count: number;
  categories_count: number;
  languages_count: number;
  favorites_count: number;
  lyrics_by_status_count: LyricsStatusCounts;
}
