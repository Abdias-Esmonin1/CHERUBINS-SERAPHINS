"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/providers/auth-provider";
import { favoritesApi } from "@/lib/api/favorites";
import { ApiClientError } from "@/lib/api/client";
import { FavoriteSongCard } from "@/components/favorites/favorite-song-card";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { Pagination } from "@/components/ui/pagination";
import { Button } from "@/components/ui/button";

const FAVORITES_QUERY_KEY = ["favorites"] as const;

export default function FavoritesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [page, setPage] = useState(1);

  useEffect(() => {
    // Filet de sécurité côté client, même pattern que /profile — le
    // middleware ne vérifie que la présence du cookie.
    if (!isAuthLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthLoading, isAuthenticated, router]);

  const favoritesQuery = useQuery({
    queryKey: [...FAVORITES_QUERY_KEY, page],
    queryFn: () => favoritesApi.list({ page, page_size: 20 }),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    // Session expirée pendant la consultation (Livrable 4 écran 06) :
    // AuthProvider.isAuthenticated peut rester vrai en cache jusqu'à
    // 60s (staleTime de la query /me) après une expiration réelle —
    // on se fie donc à la réponse réelle de CET appel, pas seulement
    // au contexte, avant de rediriger.
    if (favoritesQuery.error instanceof ApiClientError && favoritesQuery.error.status === 401) {
      router.replace("/login");
    }
  }, [favoritesQuery.error, router]);

  const removeMutation = useMutation({
    mutationFn: (songId: string) => favoritesApi.remove(songId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FAVORITES_QUERY_KEY });
    },
  });

  if (isAuthLoading || !isAuthenticated) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <LoadingSkeleton variant="list" count={3} />
      </main>
    );
  }

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <h1 className="text-xl font-semibold">Mes favoris</h1>

      {favoritesQuery.isLoading ? (
        <LoadingSkeleton variant="list" count={4} />
      ) : favoritesQuery.isError ? (
        <ErrorState message="Impossible de charger vos favoris." onRetry={() => favoritesQuery.refetch()} />
      ) : favoritesQuery.data && favoritesQuery.data.data.length > 0 ? (
        <>
          <div className="flex flex-col gap-3">
            {favoritesQuery.data.data.map((favorite) => (
              <FavoriteSongCard
                key={favorite.id}
                song={favorite.song}
                onRemove={() => removeMutation.mutate(favorite.song.id)}
                isRemoving={removeMutation.isPending && removeMutation.variables === favorite.song.id}
              />
            ))}
          </div>
          <Pagination page={page} totalPages={favoritesQuery.data.meta.total_pages} onPageChange={setPage} />
        </>
      ) : (
        <EmptyState
          title="Aucun favori pour l'instant"
          description="Recherchez un chant à ajouter."
          action={
            <Button variant="outline" render={<Link href="/search" />}>
              Rechercher un chant
            </Button>
          }
        />
      )}
    </main>
  );
}
