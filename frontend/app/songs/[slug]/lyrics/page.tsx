"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { songsApi } from "@/lib/api/songs";
import { lyricsApi } from "@/lib/api/lyrics";
import { ApiClientError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";
import { LyricsViewer } from "@/components/lyrics/lyrics-viewer";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";

export default function LyricsPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { isAuthenticated } = useAuth();

  const songQuery = useQuery({
    queryKey: ["song", slug],
    queryFn: () => songsApi.getBySlug(slug),
  });

  const song = songQuery.data?.data;

  const lyricsQuery = useQuery({
    queryKey: ["lyrics", "song", song?.id],
    queryFn: () => lyricsApi.forSong(song!.id),
    enabled: Boolean(song),
  });

  const isLoading = songQuery.isLoading || (Boolean(song) && lyricsQuery.isLoading);

  if (isLoading) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <LoadingSkeleton variant="text" count={6} />
      </main>
    );
  }

  if (songQuery.isError) {
    const isNotFound = songQuery.error instanceof ApiClientError && songQuery.error.status === 404;
    return (
      <main className="mx-auto max-w-2xl p-6 text-center">
        <p className="text-lg font-medium">{isNotFound ? "Chanson introuvable" : "Une erreur est survenue"}</p>
      </main>
    );
  }

  if (!song || lyricsQuery.isError) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <ErrorState message="Impossible de charger les paroles." onRetry={() => lyricsQuery.refetch()} />
      </main>
    );
  }

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-4 p-6">
      <Button variant="ghost" size="sm" className="w-fit" render={<Link href={`/songs/${slug}`} />}>
        <ArrowLeft className="size-4" aria-hidden />
        Retour à la fiche
      </Button>
      <div>
        <h1 className="text-xl font-semibold">
          {song.title} — {song.artist.name}
        </h1>
      </div>
      <LyricsViewer slug={slug} isAuthenticated={isAuthenticated} view={lyricsQuery.data!.data} />
    </main>
  );
}
