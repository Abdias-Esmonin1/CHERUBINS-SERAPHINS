"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { songsApi } from "@/lib/api/songs";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { SearchBar } from "@/components/search/search-bar";
import { FilterPanel, type SearchFilters } from "@/components/search/filter-panel";
import { SongCard } from "@/components/song/song-card";
import { Pagination } from "@/components/ui/pagination";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";

const MIN_QUERY_LENGTH = 2;

export default function SearchPage() {
  return (
    <Suspense fallback={<main className="mx-auto max-w-6xl p-6"><LoadingSkeleton variant="card" count={6} /></main>}>
      <SearchPageContent />
    </Suspense>
  );
}

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [filters, setFilters] = useState<SearchFilters>({
    categoryId: searchParams.get("category_id") ?? undefined,
    languageId: searchParams.get("language_id") ?? undefined,
  });
  const [page, setPage] = useState(1);

  const debouncedQuery = useDebouncedValue(query, 300);

  // Réinitialise la pagination à chaque nouvelle recherche/filtre.
  useEffect(() => {
    setPage(1);
  }, [debouncedQuery, filters.categoryId, filters.languageId]);

  const shouldSearch = debouncedQuery.trim().length >= MIN_QUERY_LENGTH;

  const resultsQuery = useQuery({
    queryKey: ["songs", "search", debouncedQuery, filters.categoryId, filters.languageId, page],
    queryFn: () =>
      songsApi.search({
        q: debouncedQuery.trim(),
        category_id: filters.categoryId,
        language_id: filters.languageId,
        page,
        page_size: 20,
      }),
    enabled: shouldSearch,
  });

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-4">
        <SearchBar value={query} onChange={setQuery} autoFocus isLoading={resultsQuery.isFetching} />
        <FilterPanel filters={filters} onChange={setFilters} />
      </div>

      {!shouldSearch ? (
        <EmptyState
          title="Que cherchez-vous ?"
          description="Saisissez au moins deux caractères — titre, artiste ou extrait de paroles."
        />
      ) : resultsQuery.isLoading ? (
        <LoadingSkeleton variant="card" count={6} />
      ) : resultsQuery.isError ? (
        <ErrorState message="Recherche indisponible, réessayez." onRetry={() => resultsQuery.refetch()} />
      ) : resultsQuery.data && resultsQuery.data.data.length > 0 ? (
        <>
          <p className="text-sm text-muted-foreground">
            {resultsQuery.data.meta.total} résultat{resultsQuery.data.meta.total > 1 ? "s" : ""} pour «{" "}
            {debouncedQuery.trim()} »
          </p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {resultsQuery.data.data.map((song) => (
              <SongCard key={song.id} song={song} />
            ))}
          </div>
          <Pagination page={page} totalPages={resultsQuery.data.meta.total_pages} onPageChange={setPage} />
        </>
      ) : (
        <EmptyState
          title={`Aucun chant trouvé pour « ${debouncedQuery.trim()} »`}
          description="Vérifiez l'orthographe ou essayez un autre terme."
        />
      )}

      {/* Conserve l'URL synchronisée pour permettre le partage du lien de recherche. */}
      <UrlSync query={debouncedQuery} filters={filters} router={router} />
    </main>
  );
}

function UrlSync({
  query,
  filters,
  router,
}: {
  query: string;
  filters: SearchFilters;
  router: ReturnType<typeof useRouter>;
}) {
  useEffect(() => {
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    if (filters.categoryId) params.set("category_id", filters.categoryId);
    if (filters.languageId) params.set("language_id", filters.languageId);
    router.replace(`/search${params.toString() ? `?${params.toString()}` : ""}`, { scroll: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- router est stable, ne doit pas re-déclencher l'effet.
  }, [query, filters.categoryId, filters.languageId]);

  return null;
}
