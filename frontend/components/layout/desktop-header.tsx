"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/providers/auth-provider";
import { SearchBar } from "@/components/search/search-bar";
import { Button } from "@/components/ui/button";

/**
 * Liens "Favoris" et "Mes soumissions" pointent vers des pages non
 * encore implémentées (Phases 8.5/8.6) — 404 jusqu'à ces phases,
 * signalé dans le rapport plutôt que masqué (cohérent avec le
 * traitement de "Proposer ces paroles"/"Fiche artiste").
 */
export function DesktopHeader() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [query, setQuery] = useState("");

  function handleSubmit(event?: FormEvent) {
    event?.preventDefault();
    if (query.trim().length > 0) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  }

  return (
    <header className="hidden border-b border-border px-6 py-3 md:block">
      <div className="mx-auto flex max-w-6xl items-center gap-6">
        <Link href="/" className="shrink-0 font-semibold">
          Chérubins &amp; Séraphins
        </Link>
        <div className="max-w-md flex-1">
          <SearchBar value={query} onChange={setQuery} onSubmit={handleSubmit} />
        </div>
        <nav className="flex shrink-0 items-center gap-4 text-sm">
          <Link href="/favorites" className="hover:underline">
            Favoris
          </Link>
          <Link href="/submissions" className="hover:underline">
            Mes soumissions
          </Link>
          {isAuthenticated && user?.role === "ADMIN" && (
            <Link href="/admin" className="hover:underline">
              Administration
            </Link>
          )}
          {isAuthenticated ? (
            <Button variant="ghost" size="sm" render={<Link href="/profile" />}>
              Profil
            </Button>
          ) : (
            <Button size="sm" render={<Link href="/login" />}>
              Connexion
            </Button>
          )}
        </nav>
      </div>
    </header>
  );
}
