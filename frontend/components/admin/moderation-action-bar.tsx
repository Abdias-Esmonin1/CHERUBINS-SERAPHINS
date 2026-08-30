"use client";

import { useState } from "react";

import type { AuthorizationStatus } from "@/types/lyrics";
import type { ModerationAuthorizeRequest } from "@/types/admin";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ModerationActionBarProps {
  rawStatus: AuthorizationStatus;
  effectiveStatus: AuthorizationStatus;
  onAuthorize: (payload: ModerationAuthorizeRequest) => void;
  onReject: (reason: string) => void;
  onRevoke: (reason: string) => void;
  isPending: boolean;
}

type ActiveDialog = "authorize" | "reject" | "revoke" | null;

/**
 * Règles de transition exactes (backend/app/services/moderation_service.py) :
 *   authorize : PENDING ou EXPIRED(effectif) -> AUTHORIZED — vérifié sur le statut EFFECTIF
 *   reject    : PENDING uniquement — vérifié sur le statut BRUT
 *   revoke    : AUTHORIZED uniquement — vérifié sur le statut BRUT
 * Un bouton désactivé ici est un confort UX ; le backend reste la
 * seule autorité (409 INVALID_TRANSITION sinon, géré par la page
 * appelante).
 */
export function ModerationActionBar({
  rawStatus,
  effectiveStatus,
  onAuthorize,
  onReject,
  onRevoke,
  isPending,
}: ModerationActionBarProps) {
  const [activeDialog, setActiveDialog] = useState<ActiveDialog>(null);
  const [authorizationReference, setAuthorizationReference] = useState("");
  const [authorizationDate, setAuthorizationDate] = useState("");
  const [expirationDate, setExpirationDate] = useState("");
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState<string | null>(null);

  const canAuthorize = effectiveStatus === "PENDING" || effectiveStatus === "EXPIRED";
  const canReject = rawStatus === "PENDING";
  const canRevoke = rawStatus === "AUTHORIZED";

  function closeDialog() {
    setActiveDialog(null);
    setReason("");
    setReasonError(null);
  }

  function handleConfirmAuthorize() {
    onAuthorize({
      authorization_reference: authorizationReference.trim() || undefined,
      authorization_date: authorizationDate || undefined,
      expiration_date: expirationDate || undefined,
    });
    closeDialog();
  }

  function handleConfirmReasonAction() {
    if (!reason.trim()) {
      setReasonError("Le motif est obligatoire.");
      return;
    }
    if (activeDialog === "reject") onReject(reason.trim());
    else if (activeDialog === "revoke") onRevoke(reason.trim());
    closeDialog();
  }

  return (
    <>
      <div className="flex flex-wrap gap-3">
        <Button type="button" disabled={!canAuthorize || isPending} onClick={() => setActiveDialog("authorize")}>
          Autoriser
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={!canReject || isPending}
          onClick={() => setActiveDialog("reject")}
        >
          Rejeter
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={!canRevoke || isPending}
          onClick={() => setActiveDialog("revoke")}
        >
          Révoquer
        </Button>
      </div>

      <Dialog open={activeDialog === "authorize"} onOpenChange={(open) => !open && closeDialog()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Autoriser cette soumission</DialogTitle>
            <DialogDescription>Tous les champs sont optionnels.</DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="auth-reference">Référence</Label>
              <Input
                id="auth-reference"
                value={authorizationReference}
                onChange={(event) => setAuthorizationReference(event.target.value)}
                disabled={isPending}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="auth-date">Date d&apos;autorisation</Label>
              <Input
                id="auth-date"
                type="date"
                value={authorizationDate}
                onChange={(event) => setAuthorizationDate(event.target.value)}
                disabled={isPending}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="expiration-date">Date d&apos;expiration</Label>
              <Input
                id="expiration-date"
                type="date"
                value={expirationDate}
                onChange={(event) => setExpirationDate(event.target.value)}
                disabled={isPending}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={closeDialog} disabled={isPending}>
              Annuler
            </Button>
            <Button type="button" onClick={handleConfirmAuthorize} disabled={isPending}>
              {isPending ? "Confirmation..." : "Confirmer l'autorisation"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={activeDialog === "reject" || activeDialog === "revoke"}
        onOpenChange={(open) => !open && closeDialog()}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{activeDialog === "reject" ? "Rejeter" : "Révoquer"} cette soumission</DialogTitle>
            <DialogDescription className="text-destructive">Cette action a un impact juridique.</DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reason">Motif (obligatoire)</Label>
            <textarea
              id="reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              rows={3}
              disabled={isPending}
              aria-invalid={reasonError ? true : undefined}
              aria-describedby={reasonError ? "reason-error" : undefined}
              className="rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            {reasonError && (
              <p id="reason-error" role="alert" className="text-sm text-destructive">
                {reasonError}
              </p>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={closeDialog} disabled={isPending}>
              Annuler
            </Button>
            <Button type="button" onClick={handleConfirmReasonAction} disabled={isPending}>
              {isPending
                ? "Confirmation..."
                : `Confirmer ${activeDialog === "reject" ? "le rejet" : "la révocation"}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
