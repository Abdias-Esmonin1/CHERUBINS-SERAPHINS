import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

/** Message utilisateur + retry — jamais de stack technique visible (Livrable 4 §6). */
export function ErrorState({ message = "Une erreur est survenue.", onRetry }: ErrorStateProps) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 rounded-xl border border-border p-8 text-center">
      <p className="text-sm text-destructive">{message}</p>
      {onRetry && (
        <Button type="button" variant="outline" onClick={onRetry}>
          Réessayer
        </Button>
      )}
    </div>
  );
}
