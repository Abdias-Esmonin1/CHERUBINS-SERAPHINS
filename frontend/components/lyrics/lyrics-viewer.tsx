"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { translationsApi } from "@/lib/api/translations";
import { isLyricsOwnerView, type LyricsSongView } from "@/types/lyrics";
import type { TranslationView } from "@/types/translation";
import type { LanguageBrief } from "@/types/catalog";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/feedback/status-badge";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { TranslationSelector } from "@/components/lyrics/translation-selector";

const TEXT_SIZES = ["text-base", "text-lg", "text-xl"] as const;

function useTextSize() {
  const [index, setIndex] = useState(1);
  return {
    className: TEXT_SIZES[index],
    controls: (
      <div className="flex items-center gap-1" role="group" aria-label="Taille du texte">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={index === 0}
          onClick={() => setIndex((i) => Math.max(0, i - 1))}
        >
          A-
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={index === TEXT_SIZES.length - 1}
          onClick={() => setIndex((i) => Math.min(TEXT_SIZES.length - 1, i + 1))}
        >
          A+
        </Button>
      </div>
    ),
  };
}

interface LyricsViewerProps {
  slug: string;
  isAuthenticated: boolean;
  view: LyricsSongView;
}

/**
 * Implémente les 3 vues du Livrable 4 (écran 05). Limite connue et
 * documentée (rapport final) : le sélecteur de traductions n'est
 * fonctionnel que pour l'auteur/ADMIN (LyricsOwnerRead expose l'id des
 * paroles) — LyricsVisibilityRead (vue publique) n'expose aucun id,
 * rendant GET /translations/lyrics/{lyrics_id} inappelable pour un
 * visiteur public. Aucune donnée n'est inventée pour contourner cette
 * limite ; la vue publique se limite donc à la langue originale.
 */
export function LyricsViewer({ slug, isAuthenticated, view }: LyricsViewerProps) {
  const textSize = useTextSize();

  // Doit rester inconditionnel (règle des Hooks) : `enabled` porte la
  // condition réelle. Le narrowing de `view` se refait plus bas via un
  // appel direct de isLyricsOwnerView(view) dans chaque branche (une
  // variable booléenne intermédiaire ne permettrait pas à TypeScript
  // de rétablir le type union).
  const translationsQuery = useQuery({
    queryKey: ["translations", "lyrics", isLyricsOwnerView(view) ? view.id : null],
    queryFn: () => translationsApi.forLyrics(isLyricsOwnerView(view) ? view.id : ""),
    enabled: isLyricsOwnerView(view),
  });

  if (!isLyricsOwnerView(view)) {
    // Vue B — non autorisé pour un tiers, quel que soit le statut réel.
    if (!view.available) {
      return (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-border p-8 text-center">
          <p className="text-muted-foreground">Ces paroles ne sont pas disponibles actuellement.</p>
          {isAuthenticated && (
            <Button variant="outline" render={<Link href={`/songs/${slug}/submissions/lyrics/new`} />}>
              Proposer ces paroles
            </Button>
          )}
        </div>
      );
    }

    // Vue A — visiteur public, paroles AUTHORIZED. Pas de sélecteur de
    // traductions (voir limite documentée en tête de fichier).
    return (
      <div className="flex flex-col gap-4">
        <p className="text-sm text-muted-foreground">{view.language!.name} (originale)</p>
        <div className={`whitespace-pre-wrap leading-relaxed ${textSize.className}`}>{view.content}</div>
        <div className="flex items-center justify-between border-t border-border pt-3">
          {textSize.controls}
        </div>
      </div>
    );
  }

  // Vue C (ou vue A équivalente si le statut est déjà AUTHORIZED) — auteur/ADMIN.
  return (
    <div className="flex flex-col gap-4">
      {view.authorization_status !== "AUTHORIZED" && (
        <div className="rounded-lg border border-border bg-muted/50 p-3">
          <StatusBadge
            status={view.authorization_status}
            reason={
              view.authorization_status === "REJECTED" || view.authorization_status === "REVOKED"
                ? "voir le motif auprès de l'administration"
                : undefined
            }
          />
          {view.authorization_status === "PENDING" && (
            <div className="mt-2">
              <Button
                variant="outline"
                size="sm"
                render={<Link href={`/songs/${slug}/submissions/lyrics/${view.id}/edit`} />}
              >
                Modifier ma soumission
              </Button>
            </div>
          )}
        </div>
      )}

      {translationsQuery.isLoading ? (
        <LoadingSkeleton variant="text" count={3} />
      ) : translationsQuery.isError ? (
        <ErrorState message="Impossible de charger les traductions." onRetry={() => translationsQuery.refetch()} />
      ) : (
        <TranslationSelectorWithState
          language={view.language}
          content={view.content}
          translations={translationsQuery.data?.data ?? []}
          textSizeClassName={textSize.className}
        />
      )}

      <div className="flex items-center justify-between border-t border-border pt-3">
        {textSize.controls}
      </div>
    </div>
  );
}

function TranslationSelectorWithState({
  language,
  content,
  translations,
  textSizeClassName,
}: {
  language: LanguageBrief;
  content: string;
  translations: TranslationView[];
  textSizeClassName: string;
}) {
  const [selectedCode, setSelectedCode] = useState(language.code);
  return (
    <TranslationSelector
      originalLanguage={language}
      originalContent={content}
      translations={translations}
      selectedCode={selectedCode}
      onSelectCode={setSelectedCode}
      textSizeClassName={textSizeClassName}
    />
  );
}
