"use client";

import { useQuery } from "@tanstack/react-query";

import { categoriesApi } from "@/lib/api/categories";
import { languagesApi } from "@/lib/api/languages";
import { Label } from "@/components/ui/label";

export interface SearchFilters {
  categoryId?: string;
  languageId?: string;
}

interface FilterPanelProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
}

/**
 * Filtres repliables (mobile) / sidebar (desktop) — Livrable 4 écrans
 * 02/03. Native <select> : pas de primitive shadcn Select dans le
 * périmètre de cette phase.
 */
export function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
    staleTime: 5 * 60 * 1000,
  });
  const languagesQuery = useQuery({
    queryKey: ["languages"],
    queryFn: () => languagesApi.list({ only_active: true }),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-language">Langue</Label>
        <select
          id="filter-language"
          value={filters.languageId ?? ""}
          onChange={(event) => onChange({ ...filters, languageId: event.target.value || undefined })}
          className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm"
        >
          <option value="">Toutes</option>
          {languagesQuery.data?.data.map((language) => (
            <option key={language.id} value={language.id}>
              {language.name}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-category">Catégorie</Label>
        <select
          id="filter-category"
          value={filters.categoryId ?? ""}
          onChange={(event) => onChange({ ...filters, categoryId: event.target.value || undefined })}
          className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm"
        >
          <option value="">Toutes</option>
          {categoriesQuery.data?.data.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
