/** roles.name est contraint en base à ('USER','ADMIN') — docs/04-database/database.md. */
export type UserRole = "USER" | "ADMIN";

/** Contrat exact de UserPublicRead (backend/app/schemas/user.py) — seule
 * forme de sortie autorisée pour un utilisateur, jamais le modèle
 * SQLAlchemy complet. Ne pas ajouter password/password_hash/first_name/
 * last_name/avatar_url : absents de ce schéma de sortie. */
export interface UserPublicRead {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  is_verified: boolean;
  created_at: string;
}
