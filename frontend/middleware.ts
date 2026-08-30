import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Protection LÉGÈRE, non-autoritaire : vérifie uniquement la présence
 * du cookie "access_token" (nom exact — backend/app/core/security.py:
 * ACCESS_TOKEN_COOKIE_NAME), jamais son contenu ni sa validité. Ce
 * middleware ne décode ni ne vérifie le JWT — le backend (via
 * GET /api/v1/auth/me, appelé par AuthProvider) reste la seule
 * autorité sur la validité réelle de la session.
 *
 * Objectif unique : éviter un flash de contenu protégé pour le cas
 * courant (aucun cookie du tout). Le cas "cookie présent mais
 * invalide/expiré" est couvert par le filet de sécurité côté client
 * dans app/profile/page.tsx (redirection après /me -> 401).
 *
 * Limite connue (à traiter avant mise en production, hors scope 8.3) :
 * ce cookie est posé par le backend sur un domaine/port distincts du
 * frontend en dev (localhost:8000 vs localhost:3000). Il n'est visible
 * ici que parce que les navigateurs stockent les cookies par domaine
 * sans tenir compte du port — "localhost" est donc partagé par
 * accident entre les deux serveurs en dev. En production, si
 * frontend et backend sont sur des domaines réellement différents
 * (ex. app.example.com / api.example.com) sans configuration de
 * domaine de cookie partagé ni proxy/rewrite, ce middleware ne verra
 * jamais le cookie : il faudra alors soit un reverse proxy unifiant
 * les origines, soit accepter que la protection ne repose que sur le
 * filet côté client (déjà fonctionnel dans tous les cas, car basé sur
 * un vrai appel à /me).
 */
export function middleware(request: NextRequest) {
  const hasSessionCookie = request.cookies.has("access_token");

  if (!hasSessionCookie) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/profile/:path*", "/favorites/:path*", "/submissions/lyrics/:path*"],
};
