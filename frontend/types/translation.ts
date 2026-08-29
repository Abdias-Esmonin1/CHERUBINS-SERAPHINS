import type { LanguageBrief } from "@/types/catalog";
import type { AuthorizationStatus } from "@/types/lyrics";

/** translations.translation_type CHECK — backend/app/schemas/translation.py. */
export type TranslationType = "OFFICIAL" | "AUTHOR" | "HUMAN" | "AI_GENERATED";

/**
 * Élément de la liste publique (une entrée par langue cible) — GET
 * /translations/lyrics/{lyrics_id}. `translation_type`/`content` restent
 * null lorsque `available = false`, pour ne rien révéler d'une
 * traduction non visible.
 */
export interface TranslationVisibilityItem {
  available: boolean;
  target_language: LanguageBrief;
  translation_type: TranslationType | null;
  content: string | null;
}

/** Vue enrichie — auteur de la soumission ou ADMIN uniquement. */
export interface TranslationOwnerRead {
  id: string;
  lyrics_id: string;
  target_language: LanguageBrief;
  content: string;
  translation_type: TranslationType;
  authorization_status: AuthorizationStatus;
  authorization_reference: string | null;
  authorization_date: string | null;
  expiration_date: string | null;
  source_url: string | null;
  rights_holder: string | null;
  submitted_by_user_id: string | null;
  reviewed_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * GET /translations/lyrics/{lyrics_id} renvoie une LISTE dont chaque
 * élément est indépendamment l'une ou l'autre forme selon le viewer
 * (backend/app/services/translation_service.py:get_visibility_list).
 * Utiliser isTranslationOwnerView pour distinguer à l'exécution.
 */
export type TranslationView = TranslationVisibilityItem | TranslationOwnerRead;

export function isTranslationOwnerView(view: TranslationView): view is TranslationOwnerRead {
  return "authorization_status" in view;
}

/** Autorisé même si les paroles originales ne sont pas AUTHORIZED —
 * cycles de droits indépendants (décision validée). */
export interface TranslationCreate {
  lyrics_id: string;
  target_language_id: string;
  content: string;
  translation_type: TranslationType;
  source_url?: string | null;
  rights_holder?: string | null;
}

export interface TranslationUpdate {
  content?: string;
  source_url?: string | null;
  rights_holder?: string | null;
}
