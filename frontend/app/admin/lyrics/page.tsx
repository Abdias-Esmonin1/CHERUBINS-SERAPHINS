"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { adminApi } from "@/lib/api/admin";
import { ApiClientError } from "@/lib/api/client";
import type { AuthorizationStatus, LyricsOwnerRead } from "@/types/lyrics";
import { StatusBadge } from "@/components/feedback/status-badge";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { Pagination } from "@/components/ui/pagination";
import { cn } from "@/lib/utils";

const FILTERS: { label: string; value: AuthorizationStatus | "ALL" }[] = [
  { label: "Tous", value: "ALL" },
  { label: "En attente", value: "PENDING" },
  { label: "Autorisées", value: "AUTHORIZED" },
  { label: "Rejetées", value: "REJECTED" },
  { label: "Expirées", value: "EXPIRED" },
  { label: "Retirées", value: "REVOKED" },
];

function isEffectivelyExpired(lyrics: LyricsOwnerRead): boolean {
  return (
    lyrics.authorization_status === "AUTHORIZED" &&
    lyrics.expiration_date !== null &&
    new Date(lyrics.expiration_date) < new Date()
  );
}

export default function AdminLyricsListPage() {
  const [status, setStatus] = useState<AuthorizationStatus | "ALL">("ALL");
  const [page, setPage] = useState(1);

  // "EXPIRED" n'est jamais stocké littéralement en base (calculé à la
  // lecture, cf. moderation_service.py — confirmé dans le rapport
  // d'inspection) : filtrer status=EXPIRED côté backend renverrait
  // toujours zéro résultat. On récupère donc les paroles AUTHORIZED
  // et on filtre côté client celles dont expiration_date est dépassée
  // — limite documentée : pas de pagination réelle pour ce filtre
  // précis, plafonné aux 100 dernières paroles AUTHORIZED (voir
  // rapport final).
  const isExpiredFilter = status === "EXPIRED";

  const listQuery = useQuery({
    queryKey: ["admin", "lyrics", isExpiredFilter ? "expired-workaround" : status, isExpiredFilter ? 1 : page],
    queryFn: () =>
      adminApi.lyrics.list(
        isExpiredFilter
          ? { status: "AUTHORIZED", page: 1, page_size: 100 }
          : { status: status === "ALL" ? undefined : status, page, page_size: 20 }
      ),
  });

  const items = listQuery.data?.data ?? [];
  const displayedItems = isExpiredFilter ? items.filter(isEffectivelyExpired) : items;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Modération — Paroles</h1>

      <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrer par statut">
        {FILTERS.map((filter) => (
          <button
            key={filter.value}
            type="button"
            onClick={() => {
              setStatus(filter.value);
              setPage(1);
            }}
            aria-pressed={status === filter.value}
            className={cn(
              "rounded-full border px-3 py-1.5 text-sm",
              status === filter.value ? "border-primary bg-primary text-primary-foreground" : "border-border"
            )}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {listQuery.isLoading ? (
        <LoadingSkeleton variant="list" count={5} />
      ) : listQuery.isError ? (
        <ErrorState
          message={
            listQuery.error instanceof ApiClientError && listQuery.error.status === 403
              ? "Accès non autorisé."
              : "Impossible de charger les soumissions."
          }
          onRetry={() => listQuery.refetch()}
        />
      ) : displayedItems.length === 0 ? (
        <EmptyState title="Aucune soumission" description="Aucune parole ne correspond à ce filtre." />
      ) : (
        <>
          {isExpiredFilter && (
            <p className="text-sm text-muted-foreground">
              Recherche parmi les 100 dernières paroles autorisées — le statut expiré n&apos;étant jamais stocké
              tel quel en base, cette liste peut être incomplète au-delà.
            </p>
          )}
          <ul className="flex flex-col gap-2">
            {displayedItems.map((lyrics) => (
              <li key={lyrics.id}>
                <Link
                  href={`/admin/lyrics/${lyrics.id}`}
                  className="flex flex-col gap-1 rounded-lg border border-border p-3 hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="truncate font-mono text-xs text-muted-foreground">
                      Chanson (ID) : {lyrics.song_id}
                    </p>
                    <p className="truncate font-mono text-xs text-muted-foreground">
                      Auteur (ID) : {lyrics.submitted_by_user_id ?? "—"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {lyrics.source_type} · {new Date(lyrics.created_at).toLocaleDateString("fr-FR")}
                    </p>
                  </div>
                  <StatusBadge status={isEffectivelyExpired(lyrics) ? "EXPIRED" : lyrics.authorization_status} />
                </Link>
              </li>
            ))}
          </ul>
          {!isExpiredFilter && listQuery.data && (
            <Pagination page={page} totalPages={listQuery.data.meta.total_pages} onPageChange={setPage} />
          )}
        </>
      )}
    </div>
  );
}
