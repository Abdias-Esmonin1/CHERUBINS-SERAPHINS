import type { RightsRecordRead } from "@/types/admin";

interface RightsRecordEntryProps {
  record: RightsRecordRead;
}

const ACTION_LABEL: Record<string, string> = {
  VALIDATED: "Autorisé",
  REJECTED: "Rejeté",
  REVOKED: "Révoqué",
};

/**
 * performed_by_user_id affiché en UUID brut : RightsRecordRead ne
 * nest pas de nom d'utilisateur (aucun endpoint public/admin de
 * résolution utilisateur n'existe dans ce MVP) — décision documentée,
 * voir rapport final, pas une donnée fabriquée.
 */
export function RightsRecordEntry({ record }: RightsRecordEntryProps) {
  return (
    <div className="rounded-lg border border-border p-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-medium">{ACTION_LABEL[record.action] ?? record.action}</span>
        <span className="text-muted-foreground">{new Date(record.created_at).toLocaleString("fr-FR")}</span>
      </div>
      <p className="text-muted-foreground">
        {record.previous_status ?? "—"} → {record.new_status}
      </p>
      {record.reason && <p className="mt-1">{record.reason}</p>}
      <p className="mt-1 font-mono text-xs text-muted-foreground">
        Par (ID utilisateur) : {record.performed_by_user_id ?? "—"}
      </p>
    </div>
  );
}
