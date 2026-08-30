import Link from "next/link";
import { ExternalLink } from "lucide-react";

import { FavoriteButton } from "@/components/favorites/favorite-button";
import { Button } from "@/components/ui/button";
import type { SongRead } from "@/types/catalog";

interface SongDetailHeaderProps {
  song: SongRead;
}

/**
 * Lien "Fiche artiste" pointe vers /artists/{slug}, page non encore
 * implémentée (P1, hors périmètre 8.4) — 404 jusqu'à cette phase,
 * signalé dans le rapport plutôt que masqué.
 */
export function SongDetailHeader({ song }: SongDetailHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row">
      <div className="aspect-square w-full shrink-0 overflow-hidden rounded-xl bg-muted sm:w-64">
        {song.cover_url ? (
          // eslint-disable-next-line @next/next/no-img-element -- domaine cover_url arbitraire, voir SongCard.
          <img src={song.cover_url} alt="" className="size-full object-cover" />
        ) : null}
      </div>
      <div className="flex flex-1 flex-col gap-2">
        <h1 className="text-2xl font-semibold">{song.title}</h1>
        <Link href={`/artists/${song.artist.slug}`} className="text-lg text-muted-foreground hover:underline">
          {song.artist.name}
        </Link>
        <dl className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-sm text-muted-foreground">
          {song.album && (
            <>
              <dt>Album</dt>
              <dd>{song.album.title}</dd>
            </>
          )}
          {song.category && (
            <>
              <dt>Catégorie</dt>
              <dd>{song.category.name}</dd>
            </>
          )}
          <dt>Langue originale</dt>
          <dd>{song.original_language.name}</dd>
        </dl>

        <div className="mt-2 flex flex-wrap items-center gap-3">
          <FavoriteButton songId={song.id} />
          {song.external_url && (
            <Button
              variant="ghost"
              render={<a href={song.external_url} target="_blank" rel="noopener noreferrer" />}
            >
              <ExternalLink className="size-4" aria-hidden />
              {song.external_provider ?? "Lien externe"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
