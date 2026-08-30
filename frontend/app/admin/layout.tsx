"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/providers/auth-provider";
import { AdminSidebar } from "@/components/admin/admin-sidebar";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { Button } from "@/components/ui/button";

/**
 * Garde de rôle purement côté client — confort UX, pas une mesure de
 * sécurité (Livrable 5 §11) : le backend (require_admin sur chaque
 * route /admin/*) reste l'unique autorité réelle. middleware.ts ne
 * vérifie que la présence du cookie (aucun décodage de rôle) ; la
 * vérification role === "ADMIN" ne peut vivre que côté client, ici.
 *
 * Unauthorized (non connecté) -> redirection /login, même pattern que
 * /profile, /favorites, /submissions/lyrics/new.
 * Forbidden (connecté, role != ADMIN) -> message explicite, pas une
 * redirection silencieuse (Livrable 4 : "Forbidden -> message 'Accès
 * non autorisé'").
 */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <LoadingSkeleton variant="text" count={4} />
      </main>
    );
  }

  if (user?.role !== "ADMIN") {
    return (
      <main className="mx-auto flex max-w-xl flex-col items-center gap-4 p-6 py-16 text-center">
        <p className="text-lg font-medium">Accès non autorisé</p>
        <p className="text-sm text-muted-foreground">Cette section est réservée aux administrateurs.</p>
        <Button variant="outline" render={<Link href="/" />}>
          Retour à l&apos;accueil
        </Button>
      </main>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-6 md:flex-row">
      <AdminSidebar />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
