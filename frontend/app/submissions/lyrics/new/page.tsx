"use client";

import { Suspense, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { songsApi } from "@/lib/api/songs";
import { ApiClientError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";
import { LyricsSubmitForm } from "@/components/forms/lyrics-submit-form";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";

/**
 * Route : /submissions/lyrics/new?song={slug}
 *
 * Décision technique (non couverte explicitement par les instructions) :
 * le paramètre d'URL identifie la chanson par son SLUG, pas par son
 * UUID (song_id), bien que le Livrable 5 mentionne
 * "submissions/lyrics/new?song_id=X". Aucun endpoint public
 * GET /songs/{id} n'existe (uniquement GET /songs/{slug}, confirmé
 * dans backend/app/routers/songs.py) — utiliser un slug permet de
 * réutiliser songsApi.getBySlug() déjà existant (§1 des règles :
 * aucun nouveau client API) pour à la fois résoudre le song_id réel
 * (nécessaire au payload LyricsCreate) et afficher titre/artiste.
 * Un song_id brut dans l'URL n'aurait permis ni l'un ni l'autre sans
 * un nouvel endpoint, hors périmètre de cette phase.
 */
export default function NewLyricsSubmissionPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto max-w-xl p-6">
          <LoadingSkeleton variant="text" count={4} />
        </main>
      }
    >
      <NewLyricsSubmissionContent />
    </Suspense>
  );
}

function NewLyricsSubmissionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const songSlug = searchParams.get("song");

  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthLoading, isAuthenticated, router]);

  const songQuery = useQuery({
    queryKey: ["song", songSlug],
    queryFn: () => songsApi.getBySlug(songSlug as string),
    enabled: Boolean(songSlug) && isAuthenticated,
  });

  if (isAuthLoading || !isAuthenticated) {
    return (
      <main className="mx-auto max-w-xl p-6">
        <LoadingSkeleton variant="text" count={4} />
      </main>
    );
  }

  if (!songSlug) {
    return (
      <main className="mx-auto max-w-xl p-6">
        <EmptyState
          title="Aucune chanson sélectionnée"
          description="Recherchez d'abord la chanson pour laquelle vous souhaitez proposer des paroles."
          action={
            <Button variant="outline" render={<Link href="/search" />}>
              Rechercher une chanson
            </Button>
          }
        />
      </main>
    );
  }

  if (songQuery.isLoading) {
    return (
      <main className="mx-auto max-w-xl p-6">
        <LoadingSkeleton variant="text" count={4} />
      </main>
    );
  }

  if (songQuery.isError) {
    const isNotFound = songQuery.error instanceof ApiClientError && songQuery.error.status === 404;
    return (
      <main className="mx-auto max-w-xl p-6">
        {isNotFound ? (
          <div className="flex flex-col items-center gap-4 py-12 text-center">
            <p className="text-lg font-medium">Chanson introuvable</p>
            <Button variant="outline" render={<Link href="/search" />}>
              Rechercher une chanson
            </Button>
          </div>
        ) : (
          <ErrorState message="Impossible de charger cette chanson." onRetry={() => songQuery.refetch()} />
        )}
      </main>
    );
  }

  if (!songQuery.data) {
    return null;
  }

  return (
    <main className="mx-auto max-w-xl p-6">
      <LyricsSubmitForm song={songQuery.data.data} />
    </main>
  );
}
