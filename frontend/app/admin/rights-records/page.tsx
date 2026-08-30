"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { adminApi } from "@/lib/api/admin";
import { ApiClientError } from "@/lib/api/client";
import type { RightsRecordAction } from "@/types/admin";
import { RightsRecordEntry } from "@/components/admin/rights-record-entry";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { Pagination } from "@/components/ui/pagination";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const ACTIONS: { label: string; value: RightsRecordAction | "ALL" }[] = [
  { label: "Toutes", value: "ALL" },
  { label: "Autorisé", value: "VALIDATED" },
  { label: "Rejeté", value: "REJECTED" },
  { label: "Révoqué", value: "REVOKED" },
];

/**
 * Le contrat GET /admin/rights-records filtre par lyrics_id/
 * translation_id PRÉCIS (un enregistrement précis), pas par "type de
 * cible" (toutes les entrées lyrics vs toutes les entrées
 * translation) — confirmé dans backend/app/repositories/
 * rights_record_repository.py, aucun paramètre de ce genre n'existe.
 * Le filtre "Cible lyrics/translation" évoqué par le Livrable 4 n'est
 * donc pas implémentable fidèlement sans post-filtrage client qui
 * casserait la pagination réelle — volontairement omis plutôt
 * qu'implémenté de façon trompeuse (voir rapport final).
 */
export default function AdminRightsRecordsPage() {
  const [action, setAction] = useState<RightsRecordAction | "ALL">("ALL");
  const [performedBy, setPerformedBy] = useState("");
  const [page, setPage] = useState(1);

  const listQuery = useQuery({
    queryKey: ["admin", "rights-records", action, performedBy, page],
    queryFn: () =>
      adminApi.rightsRecords.list({
        action: action === "ALL" ? undefined : action,
        performed_by_user_id: performedBy.trim() || undefined,
        page,
        page_size: 20,
      }),
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Rights Records</h1>
        <p className="text-sm text-muted-foreground">
          Journal append-only — les enregistrements ne sont pas modifiables.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-action">Action</Label>
          <select
            id="filter-action"
            value={action}
            onChange={(event) => {
              setAction(event.target.value as RightsRecordAction | "ALL");
              setPage(1);
            }}
            className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm"
          >
            {ACTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-user">ID utilisateur</Label>
          <Input
            id="filter-user"
            value={performedBy}
            onChange={(event) => {
              setPerformedBy(event.target.value);
              setPage(1);
            }}
            placeholder="UUID exact"
            className="w-56"
          />
        </div>
      </div>

      {listQuery.isLoading ? (
        <LoadingSkeleton variant="list" count={5} />
      ) : listQuery.isError ? (
        <ErrorState
          message={
            listQuery.error instanceof ApiClientError && listQuery.error.status === 403
              ? "Accès non autorisé."
              : "Impossible de charger le journal."
          }
          onRetry={() => listQuery.refetch()}
        />
      ) : listQuery.data && listQuery.data.data.length > 0 ? (
        <>
          <ul className="flex flex-col gap-2">
            {listQuery.data.data.map((record) => (
              <li key={record.id}>
                <RightsRecordEntry record={record} />
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={listQuery.data.meta.total_pages} onPageChange={setPage} />
        </>
      ) : (
        <EmptyState title="Aucun enregistrement" description="Aucun événement ne correspond à ce filtre." />
      )}
    </div>
  );
}
