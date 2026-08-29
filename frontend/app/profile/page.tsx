"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/providers/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isLoading, isAuthenticated, logout, isLogoutPending } = useAuth();

  useEffect(() => {
    // Filet de sécurité côté client : le middleware ne vérifie que la
    // présence du cookie (voir middleware.ts) — si /me répond 401 malgré
    // un cookie présent (session expirée/invalidée), c'est ici, une fois
    // le backend consulté, que la redirection réelle a lieu.
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  if (isLoading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <p className="text-sm text-muted-foreground">Chargement...</p>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Mon profil</CardTitle>
          <CardDescription>Informations de votre compte.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <p>
            <span className="font-medium">Nom d&apos;utilisateur : </span>
            {user.username}
          </p>
          <p>
            <span className="font-medium">Email : </span>
            {user.email}
          </p>
          <p>
            <span className="font-medium">Rôle : </span>
            {user.role}
          </p>
          <p>
            <span className="font-medium">Compte vérifié : </span>
            {user.is_verified ? "Oui" : "Non"}
          </p>
          <p>
            <span className="font-medium">Membre depuis : </span>
            {new Date(user.created_at).toLocaleDateString("fr-FR")}
          </p>
        </CardContent>
        <CardFooter>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={handleLogout}
            disabled={isLogoutPending}
          >
            {isLogoutPending ? "Déconnexion..." : "Se déconnecter"}
          </Button>
        </CardFooter>
      </Card>
    </main>
  );
}
