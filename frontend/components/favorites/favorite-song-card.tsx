import Link from "next/link";
import { Heart } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { SongRead } from "@/types/catalog";

interface FavoriteSongCardProps {
  song: SongRead;
  onRemove: () => void;
  isRemoving: boolean;
}

/**
 * Carte dédiée à l'écran Favoris — ne réutilise pas SongCard (Phase
 * 8.4) car celui-ci enveloppe toute la carte dans un <Link>, rendant
 * impossible d'y imbriquer un bouton de retrait sans HTML invalide
 * (décision explicite : composition dédiée, SongCard non modifié).
 * Le lien vers la fiche chanson et le bouton de retrait sont des
 * éléments frères, pas imbriqués.
 */
export function FavoriteSongCard({ song, onRemove, isRemoving }: FavoriteSongCardProps) {
  return (
    <Card className="overflow-hidden py-0">
      <div className="flex items-center gap-3 p-3">
        <Link href={`/songs/${song.slug}`} className="flex min-w-0 flex-1 items-center gap-3">
          <div className="relative size-14 shrink-0 overflow-hidden rounded-lg bg-muted">
            {song.cover_url ? (
              // eslint-disable-next-line @next/next/no-img-element -- domaine cover_url arbitraire, voir SongCard.
              <img src={song.cover_url} alt="" className="size-full object-cover" />
            ) : null}
          </div>
          <div className="min-w-0">
            <p className="truncate font-medium">{song.title}</p>
            <p className="truncate text-sm text-muted-foreground">{song.artist.name}</p>
          </div>
        </Link>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onRemove}
          disabled={isRemoving}
          aria-label={`Retirer ${song.title} des favoris`}
        >
          <Heart className="size-4" fill="currentColor" aria-hidden />
        </Button>
      </div>
    </Card>
  );
}
