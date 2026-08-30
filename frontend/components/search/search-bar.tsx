"use client";

import { Loader2, Search, X } from "lucide-react";

import { Input } from "@/components/ui/input";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  isLoading?: boolean;
  autoFocus?: boolean;
  placeholder?: string;
}

/**
 * Composant présentationnel — la logique de debounce/navigation reste
 * dans la page appelante (Accueil redirige vers /search, écran
 * Recherche déclenche une requête live).
 */
export function SearchBar({
  value,
  onChange,
  onSubmit,
  isLoading,
  autoFocus,
  placeholder = "Titre, artiste, extrait...",
}: SearchBarProps) {
  return (
    <form
      role="search"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit?.();
      }}
      className="relative w-full"
    >
      <Search
        className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden
      />
      <Input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        autoFocus={autoFocus}
        placeholder={placeholder}
        aria-label="Rechercher un chant"
        className="pl-9 pr-9"
      />
      {isLoading ? (
        <Loader2
          className="absolute right-3 top-1/2 size-4 -translate-y-1/2 animate-spin text-muted-foreground"
          aria-hidden
        />
      ) : (
        value.length > 0 && (
          <button
            type="button"
            onClick={() => onChange("")}
            aria-label="Effacer la recherche"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="size-4" aria-hidden />
          </button>
        )
      )}
    </form>
  );
}
