/**
 * Types API — squelette de fondation (Phase 8.1).
 *
 * Les types métier complets (User, Song, Lyrics, Translation, Favorite,
 * Admin*, ...) sont construits à partir des schemas backend réels et
 * ajoutés en Phase 8.2. Ne rien y anticiper ici.
 */

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApiSuccess<T> {
  data: T;
}

export interface ApiSuccessPaginated<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface ApiBusinessError {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
}

/** Format natif FastAPI pour les erreurs de validation Pydantic (422). */
export interface ApiValidationError {
  detail: Array<{
    type: string;
    loc: (string | number)[];
    msg: string;
    input?: unknown;
  }>;
}
