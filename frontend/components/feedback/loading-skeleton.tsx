import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  variant?: "card" | "list" | "text";
  count?: number;
  className?: string;
}

/** Placeholder de chargement — jamais d'écran blanc (Livrable 4 §6). */
export function LoadingSkeleton({ variant = "text", count = 1, className }: LoadingSkeletonProps) {
  const items = Array.from({ length: count });

  if (variant === "card") {
    return (
      <div className={cn("grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3", className)}>
        {items.map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-xl bg-muted" aria-hidden />
        ))}
      </div>
    );
  }

  if (variant === "list") {
    return (
      <div className={cn("flex flex-col gap-3", className)}>
        {items.map((_, i) => (
          <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" aria-hidden />
        ))}
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {items.map((_, i) => (
        <div key={i} className="h-4 w-full animate-pulse rounded bg-muted" aria-hidden />
      ))}
    </div>
  );
}
