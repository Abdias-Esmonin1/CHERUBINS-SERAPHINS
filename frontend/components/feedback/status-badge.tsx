import { Ban, CheckCircle2, Clock, Hourglass, XCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import type { AuthorizationStatus } from "@/types/lyrics";

const STATUS_CONFIG: Record<
  AuthorizationStatus,
  { label: string; icon: typeof Clock; className: string }
> = {
  PENDING: { label: "En attente", icon: Clock, className: "text-yellow-600 dark:text-yellow-500" },
  AUTHORIZED: { label: "Autorisée", icon: CheckCircle2, className: "text-green-600 dark:text-green-500" },
  REJECTED: { label: "Rejetée", icon: XCircle, className: "text-red-600 dark:text-red-500" },
  EXPIRED: { label: "Expirée", icon: Hourglass, className: "text-muted-foreground" },
  REVOKED: { label: "Retirée", icon: Ban, className: "text-red-600 dark:text-red-500" },
};

interface StatusBadgeProps {
  status: AuthorizationStatus;
  reason?: string | null;
}

/**
 * Statut visuel des droits — toujours couleur + icône + libellé texte,
 * jamais la couleur seule (Livrable 4 §8 accessibilité).
 */
export function StatusBadge({ status, reason }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <span className={cn("inline-flex items-center gap-1.5 text-sm font-medium", config.className)}>
      <Icon className="size-4" aria-hidden />
      {config.label}
      {reason && <span className="text-muted-foreground">— {reason}</span>}
    </span>
  );
}
