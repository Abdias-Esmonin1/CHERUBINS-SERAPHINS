"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminApi } from "@/lib/api/admin";
import { ApiClientError } from "@/lib/api/client";
import type { AuthorizationStatus } from "@/types/lyrics";
import type { ModerationAuthorizeRequest } from "@/types/admin";
import { StatusBadge } from "@/components/feedback/status-badge";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { ErrorState } from "@/components/feedback/error-state";
import { ModerationActionBar } from "@/components/admin/moderation-action-bar";
import { RightsRecordEntry } from "@/components/admin/rights-record-entry";

function getEffectiveStatus(rawStatus: AuthorizationStatus, expirationDate: string | null): AuthorizationStatus {
  if (rawStatus === "AUTHORIZED" && expirationDate && new Date(expirationDate) < new Date()) {
    return "EXPIRED";
  }
  return rawStatus;
}

export default function AdminLyricsDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const queryClient = useQueryClient();
  const [mutationError, setMutationError] = useState<string | null>(null);

  const lyricsQuery = useQuery({
    queryKey: ["admin", "lyrics", id],
    queryFn: () => adminApi.lyrics.get(id),
  });

  const historyQuery = useQuery({
    queryKey: ["admin", "rights-records", "lyrics", id],
    queryFn: () => adminApi.rightsRecords.list({ lyrics_id: id, page_size: 50 }),
  });

  function invalidateAfterMutation(songId: string) {
    queryClient.invalidateQueries({ queryKey: ["admin", "lyrics"] });
    queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
    queryClient.invalidateQueries({ queryKey: ["admin", "rights-records"] });
    queryClient.invalidateQueries({ queryKey: ["lyrics", "song", songId] });
  }

  function handleMutationError(error: unknown) {
    if (error instanceof ApiClientError) {
      if (error.status === 409) {
        setMutationError("Cette transition n'est plus valide — la ressource a peut-être été modifiée entre-temps.");
      } else if (error.status === 422) {
        setMutationError(error.fieldErrors.reason?.join(" ") ?? error.message);
      } else {
        setMutationError(error.message);
      }
      // 409/422 : l'état affiché peut être périmé, on force un
      // rechargement réel plutôt que de continuer sur des données obsolètes.
      queryClient.invalidateQueries({ queryKey: ["admin", "lyrics", id] });
    } else {
      setMutationError("Une erreur inattendue est survenue.");
    }
  }

  const authorizeMutation = useMutation({
    mutationFn: (payload: ModerationAuthorizeRequest) => adminApi.lyrics.authorize(id, payload),
    onSuccess: (result) => invalidateAfterMutation(result.data.song_id),
    onError: handleMutationError,
  });
  const rejectMutation = useMutation({
    mutationFn: (reason: string) => adminApi.lyrics.reject(id, { reason }),
    onSuccess: (result) => invalidateAfterMutation(result.data.song_id),
    onError: handleMutationError,
  });
  const revokeMutation = useMutation({
    mutationFn: (reason: string) => adminApi.lyrics.revoke(id, { reason }),
    onSuccess: (result) => invalidateAfterMutation(result.data.song_id),
    onError: handleMutationError,
  });

  if (lyricsQuery.isLoading) {
    return <LoadingSkeleton variant="text" count={6} />;
  }

  if (lyricsQuery.isError || !lyricsQuery.data) {
    const isForbidden = lyricsQuery.error instanceof ApiClientError && lyricsQuery.error.status === 403;
    const isNotFound = lyricsQuery.error instanceof ApiClientError && lyricsQuery.error.status === 404;
    return (
      <ErrorState
        message={
          isForbidden
            ? "Accès non autorisé."
            : isNotFound
              ? "Paroles introuvables."
              : "Impossible de charger cette soumission."
        }
        onRetry={() => lyricsQuery.refetch()}
      />
    );
  }

  const lyrics = lyricsQuery.data.data;
  const effectiveStatus = getEffectiveStatus(lyrics.authorization_status, lyrics.expiration_date);
  const isMutating = authorizeMutation.isPending || rejectMutation.isPending || revokeMutation.isPending;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Modération — Parole</h1>
        {/* song_id/submitted_by_user_id affichés en UUID brut : LyricsOwnerRead
            n'imbrique ni le titre de la chanson ni le nom d'utilisateur — voir
            rapport final (écart backend découvert pendant cette phase). */}
        <p className="font-mono text-xs text-muted-foreground">Chanson (ID) : {lyrics.song_id}</p>
        <p className="font-mono text-xs text-muted-foreground">Auteur (ID) : {lyrics.submitted_by_user_id ?? "—"}</p>
      </div>

      <StatusBadge status={effectiveStatus} />

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
        <dt className="text-muted-foreground">Langue</dt>
        <dd>{lyrics.language.name}</dd>
        <dt className="text-muted-foreground">Source</dt>
        <dd>{lyrics.source_type}</dd>
        {lyrics.source_url && (
          <>
            <dt className="text-muted-foreground">Lien source</dt>
            <dd className="truncate">{lyrics.source_url}</dd>
          </>
        )}
        {lyrics.rights_holder && (
          <>
            <dt className="text-muted-foreground">Détenteur des droits</dt>
            <dd>{lyrics.rights_holder}</dd>
          </>
        )}
        <dt className="text-muted-foreground">Soumis le</dt>
        <dd>{new Date(lyrics.created_at).toLocaleString("fr-FR")}</dd>
      </dl>

      <div className="rounded-lg border border-border p-4">
        <p className="mb-2 text-sm font-medium">Contenu</p>
        <div className="whitespace-pre-wrap text-sm">{lyrics.content}</div>
      </div>

      {mutationError && (
        <p role="alert" className="text-sm text-destructive">
          {mutationError}
        </p>
      )}

      <ModerationActionBar
        rawStatus={lyrics.authorization_status}
        effectiveStatus={effectiveStatus}
        onAuthorize={(payload) => {
          setMutationError(null);
          authorizeMutation.mutate(payload);
        }}
        onReject={(reason) => {
          setMutationError(null);
          rejectMutation.mutate(reason);
        }}
        onRevoke={(reason) => {
          setMutationError(null);
          revokeMutation.mutate(reason);
        }}
        isPending={isMutating}
      />

      <div className="flex flex-col gap-2">
        <h2 className="text-lg font-medium">Historique</h2>
        {historyQuery.isLoading ? (
          <LoadingSkeleton variant="text" count={2} />
        ) : historyQuery.isError ? (
          <ErrorState message="Impossible de charger l'historique." onRetry={() => historyQuery.refetch()} />
        ) : historyQuery.data && historyQuery.data.data.length > 0 ? (
          <ul className="flex flex-col gap-2">
            {historyQuery.data.data.map((record) => (
              <li key={record.id}>
                <RightsRecordEntry record={record} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Aucun événement enregistré.</p>
        )}
      </div>
    </div>
  );
}
