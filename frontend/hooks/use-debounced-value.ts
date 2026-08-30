import { useEffect, useState } from "react";

/** Retourne `value` retardée de `delayMs` — utilisé pour la recherche live (Livrable 4 écran 02, debounce ~300ms). */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timeout = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timeout);
  }, [value, delayMs]);

  return debounced;
}
