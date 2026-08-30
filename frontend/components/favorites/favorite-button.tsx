"use client";

import { useRouter } from "next/navigation";
import { Heart } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/providers/auth-provider";
import { favoritesApi } from "@/lib/api/favorites";
import { Button } from "@/components/ui/button";

interface FavoriteButtonProps {
  songId: string;
}

const FAVORITES_QUERY_KEY = ["favorites"] as const;

/**
 * L'API n'expose pas de champ "is_favorited" sur SongRead, ni
 * d'endpoint de vérification par chanson (écart non documenté
 * découvert pendant cette phase — voir rapport final). L'état initial
 * du bouton est donc déterminé en chargeant la liste des favoris de
 * l'utilisateur (page_size élevée) et en vérifiant l'appartenance —
 * fiable jusqu'à ~100 favoris, au-delà l'état initial peut être
 * incorrect (limite documentée, pas corrigée silencieusement).
 */
export function FavoriteButton({ songId }: FavoriteButtonProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();

  const favoritesQuery = useQuery({
    queryKey: FAVORITES_QUERY_KEY,
    queryFn: () => favoritesApi.list({ page_size: 100 }),
    enabled: isAuthenticated,
    staleTime: 0,
  });

  const isFavorited = favoritesQuery.data?.data.some((favorite) => favorite.song.id === songId) ?? false;

  const addMutation = useMutation({
    mutationFn: () => favoritesApi.add({ song_id: songId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: FAVORITES_QUERY_KEY }),
  });

  const removeMutation = useMutation({
    mutationFn: () => favoritesApi.remove(songId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: FAVORITES_QUERY_KEY }),
  });

  const isPending = addMutation.isPending || removeMutation.isPending;

  function handleClick() {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    if (isFavorited) {
      removeMutation.mutate();
    } else {
      addMutation.mutate();
    }
  }

  return (
    <Button
      type="button"
      variant={isFavorited ? "default" : "outline"}
      onClick={handleClick}
      disabled={isAuthLoading || isPending}
      aria-pressed={isFavorited}
      aria-label={isFavorited ? "Retirer des favoris" : "Ajouter aux favoris"}
    >
      <Heart className="size-4" fill={isFavorited ? "currentColor" : "none"} aria-hidden />
      {isFavorited ? "Dans mes favoris" : "Ajouter aux favoris"}
    </Button>
  );
}
