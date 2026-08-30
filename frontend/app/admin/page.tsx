"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { adminApi } from "@/lib/api/admin";
import { ApiClientError } from "@/lib/api/client";
import { StatCard } from "@/components/admin/stat-card";
import { LoadingSkeleton } from "@/components/feedback/loading-skeleton";
import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";

export default function AdminDashboardPage() {
  const statsQuery = useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => adminApi.stats.get(),
  });

  if (statsQuery.isLoading) {
    return <LoadingSkeleton variant="card" count={8} />;
  }

  if (statsQuery.isError || !statsQuery.data) {
    const isForbidden = statsQuery.error instanceof ApiClientError && statsQuery.error.status === 403;
    return (
      <ErrorState
        message={isForbidden ? "Accès non autorisé." : "Impossible de charger les statistiques."}
        onRetry={() => statsQuery.refetch()}
      />
    );
  }

  const stats = statsQuery.data.data;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Administration</h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Utilisateurs" value={stats.users_count} />
        <StatCard label="Chansons" value={stats.songs_count} />
        <StatCard label="Artistes" value={stats.artists_count} />
        <StatCard label="Albums" value={stats.albums_count} />
        <StatCard label="Catégories" value={stats.categories_count} />
        <StatCard label="Langues" value={stats.languages_count} />
        <StatCard label="Favoris" value={stats.favorites_count} />
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">Paroles par statut</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <StatCard label="En attente" value={stats.lyrics_by_status_count.PENDING} />
          <StatCard label="Autorisées" value={stats.lyrics_by_status_count.AUTHORIZED} />
          <StatCard label="Rejetées" value={stats.lyrics_by_status_count.REJECTED} />
          <StatCard label="Expirées" value={stats.lyrics_by_status_count.EXPIRED} />
          <StatCard label="Retirées" value={stats.lyrics_by_status_count.REVOKED} />
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button render={<Link href="/admin/lyrics" />}>Modération paroles</Button>
        <Button variant="outline" render={<Link href="/admin/rights-records" />}>
          Rights Records
        </Button>
      </div>
    </div>
  );
}
