"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { songsApi } from "@/lib/api/songs";
import { lyricsApi } from "@/lib/api/lyrics";
import { ApiClientError } from "@/lib/api/client";
import { isLyricsOwnerView } from "@/types/lyrics";
import { useAuth } from "@/providers/auth-provider";
import { SongDetailHeader } from "@/components/song/song-detail-header";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";

export default function SongPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);

  const songQuery = useQuery({
    queryKey: ["song", slug],
    queryFn: () => songsApi.getBySlug(slug),
  });

  if (songQuery.isLoading) {
    return (
      <main className="mx-auto max-w-4xl p-6">
        <LoadingSkeleton variant="card" count={1} />
      </main>
    );
  }

  if (songQuery.isError) {
    // 404 SONG_NOT_FOUND ou tout autre statut -> message générique,
    // jamais de distinction technique (Livrable 4 écran 04).
    const isNotFound = songQuery.error instanceof ApiClientError && songQuery.error.status === 404;
    return (
      <main className="mx-auto max-w-4xl p-6">
        {isNotFound ? (
          <div className="flex flex-col items-center gap-4 py-12 text-center">
            <p className="text-lg font-medium">Chanson introuvable</p>
            <Button variant="outline" render={<Link href="/" />}>
              Retour à l&apos;accueil
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

  const song = songQuery.data.data;

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 p-6">
      <SongDetailHeader song={song} />
      <div className="rounded-xl border border-border p-4">
        <LyricsAvailability slug={song.slug} songId={song.id} />
      </div>
    </main>
  );
}

function LyricsAvailability({ slug, songId }: { slug: string; songId: string }) {
  const { isAuthenticated } = useAuth();

  const lyricsQuery = useQuery({
    queryKey: ["lyrics", "song", songId],
    queryFn: () => lyricsApi.forSong(songId),
  });

  if (lyricsQuery.isLoading) {
    return <LoadingSkeleton variant="text" count={2} />;
  }

  if (lyricsQuery.isError) {
    return (
      <ErrorState
        message="Impossible de vérifier la disponibilité des paroles."
        onRetry={() => lyricsQuery.refetch()}
      />
    );
  }

  if (!lyricsQuery.data) {
    return null;
  }

  const view = lyricsQuery.data.data;
  // L'auteur/ADMIN voit toujours le contenu réel (LyricsOwnerRead), quel
  // que soit le statut — donc "disponible" pour eux au sens de cet écran.
  const available = isLyricsOwnerView(view) ? true : view.available;

  if (available) {
    return (
      <div className="flex flex-col gap-3">
        <p className="font-medium">✓ Paroles disponibles</p>
        <Button render={<Link href={`/songs/${slug}/lyrics`} />}>Voir les paroles</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="font-medium">Paroles non disponibles actuellement</p>
      {isAuthenticated && (
        <Button variant="outline" render={<Link href={`/songs/${slug}/submissions/lyrics/new`} />}>
          Proposer ces paroles
        </Button>
      )}
    </div>
  );
}
