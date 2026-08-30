import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import type { SongRead } from "@/types/catalog";

interface SongCardProps {
  song: SongRead;
}

/**
 * Pas d'indicateur "paroles disponibles" : SongRead n'expose pas
 * lyrics_available (écart backend déjà documenté, docs/05-api/api.md).
 * Impossible de l'afficher sans deviner une donnée absente de l'API —
 * voir rapport final.
 */
export function SongCard({ song }: SongCardProps) {
  return (
    <Link href={`/songs/${song.slug}`} className="block">
      <Card className="h-full overflow-hidden transition-shadow hover:shadow-md">
        <div className="relative aspect-square w-full bg-muted">
          {song.cover_url ? (
            // eslint-disable-next-line @next/next/no-img-element -- domaine cover_url arbitraire, non connu à la configuration.
            <img src={song.cover_url} alt="" className="absolute inset-0 size-full object-cover" />
          ) : null}
        </div>
        <CardContent className="flex flex-col gap-0.5 pt-3">
          <p className="truncate font-medium">{song.title}</p>
          <p className="truncate text-sm text-muted-foreground">{song.artist.name}</p>
          <p className="truncate text-xs text-muted-foreground">
            {song.category?.name ?? song.original_language.name}
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}
