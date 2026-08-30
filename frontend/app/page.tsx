"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { songsApi } from "@/lib/api/songs";
import { categoriesApi } from "@/lib/api/categories";
import { artistsApi } from "@/lib/api/artists";
import { SearchBar } from "@/components/search/search-bar";
import { SongCard } from "@/components/song/song-card";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { EmptyState } from "@/components/feedback/empty-state";

export default function Home() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
    staleTime: 5 * 60 * 1000,
  });

  // "Chants récents" — libellé et tri définitivement tranchés (décision
  // officielle Phase 8.4) : GET /songs ne propose ni sort ni notion de
  // popularité ; on affiche donc le tri par défaut (created_at DESC),
  // libellé honnêtement "récents" plutôt que "populaires".
  const recentSongsQuery = useQuery({
    queryKey: ["songs", "recent"],
    queryFn: () => songsApi.list({ page_size: 8 }),
    staleTime: 60 * 1000,
  });

  const artistsQuery = useQuery({
    queryKey: ["artists", "home"],
    queryFn: () => artistsApi.list({ page_size: 8 }),
    staleTime: 60 * 1000,
  });

  function handleSearchSubmit(event?: FormEvent) {
    event?.preventDefault();
    if (query.trim().length > 0) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  }

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-10 p-6">
      <section className="flex flex-col items-center gap-4 py-8 text-center">
        <h1 className="text-2xl font-semibold sm:text-3xl">Chérubins &amp; Séraphins</h1>
        <p className="max-w-md text-muted-foreground">Retrouvez les paroles de vos chants préférés.</p>
        <div className="w-full max-w-lg">
          <SearchBar value={query} onChange={setQuery} onSubmit={handleSearchSubmit} autoFocus />
        </div>
      </section>

      {/* Catégories — pas de rendu d'erreur bloquant : masqué silencieusement si l'appel échoue (Livrable 4 écran 01). */}
      {categoriesQuery.data && categoriesQuery.data.data.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-medium">Catégories</h2>
          <div className="flex flex-wrap gap-2">
            {categoriesQuery.data.data.map((category) => (
              <Link
                key={category.id}
                href={`/search?category_id=${category.id}`}
                className="rounded-full border border-border px-3 py-1.5 text-sm hover:bg-muted"
              >
                {category.name}
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">Chants récents</h2>
        {recentSongsQuery.isLoading ? (
          <LoadingSkeleton variant="card" count={4} />
        ) : recentSongsQuery.isError ? null : recentSongsQuery.data && recentSongsQuery.data.data.length > 0 ? (
          <div className="flex gap-4 overflow-x-auto pb-2 sm:grid sm:grid-cols-3 sm:overflow-visible lg:grid-cols-4">
            {recentSongsQuery.data.data.map((song) => (
              <div key={song.id} className="w-40 shrink-0 sm:w-auto">
                <SongCard song={song} />
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="Aucun chant publié pour l'instant." />
        )}
      </section>

      {artistsQuery.data && artistsQuery.data.data.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-medium">Artistes</h2>
          <div className="flex gap-4 overflow-x-auto pb-2 sm:grid sm:grid-cols-4 sm:overflow-visible lg:grid-cols-8">
            {artistsQuery.data.data.map((artist) => (
              <Link
                key={artist.id}
                href={`/artists/${artist.slug}`}
                className="flex w-20 shrink-0 flex-col items-center gap-1.5 text-center sm:w-auto"
              >
                <span className="flex size-16 items-center justify-center rounded-full bg-muted text-lg font-medium">
                  {artist.name.charAt(0).toUpperCase()}
                </span>
                <span className="truncate text-xs">{artist.name}</span>
              </Link>
            ))}
          </div>
        </section>
      )}
      {artistsQuery.isLoading && <LoadingSkeleton variant="list" count={1} />}
    </main>
  );
}
