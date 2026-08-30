"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

import { lyricsApi } from "@/lib/api/lyrics";
import { languagesApi } from "@/lib/api/languages";
import { ApiClientError } from "@/lib/api/client";
import type { SongRead } from "@/types/catalog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StatusBadge } from "@/components/feedback/status-badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface LyricsSubmitFormProps {
  song: SongRead;
}

/**
 * source_type est imposé à "USER_SUBMITTED" et n'est jamais exposé
 * comme un choix utilisateur (décision Phase 8.6) — le frontend ne
 * doit jamais influencer le cycle de droits au-delà de ce que le
 * contrat autorise. authorization_status/submitted_by_user_id restent
 * structurellement absents de LyricsCreate (forcés côté serveur,
 * jamais fournis ici) — voir types/lyrics.ts.
 */
export function LyricsSubmitForm({ song }: LyricsSubmitFormProps) {
  const router = useRouter();

  const languagesQuery = useQuery({
    queryKey: ["languages"],
    queryFn: () => languagesApi.list({ only_active: true }),
    staleTime: 5 * 60 * 1000,
  });

  const [languageId, setLanguageId] = useState(song.original_language.id);
  const [content, setContent] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [rightsHolder, setRightsHolder] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  const submitMutation = useMutation({
    mutationFn: () =>
      lyricsApi.submit({
        song_id: song.id,
        language_id: languageId,
        content,
        source_type: "USER_SUBMITTED",
        source_url: sourceUrl.trim() || undefined,
        rights_holder: rightsHolder.trim() || undefined,
      }),
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Garde explicite en plus du bouton désactivé — empêche toute
    // double soumission même sur un double Enter avant le re-rendu.
    if (submitMutation.isPending) return;

    setFormError(null);
    setFieldErrors({});
    submitMutation.mutate(undefined, {
      onError: (error) => {
        if (error instanceof ApiClientError) {
          if (error.status === 401) {
            router.push("/login");
            return;
          }
          setFormError(error.message);
          setFieldErrors(error.fieldErrors);
        } else {
          setFormError("Une erreur inattendue est survenue.");
        }
      },
    });
  }

  if (submitMutation.isSuccess) {
    // authorization_status affiché tel que réellement renvoyé par le
    // backend — jamais supposé égal à "PENDING" par le frontend.
    const result = submitMutation.data.data;
    return (
      <Card>
        <CardHeader>
          <CardTitle>Proposition envoyée</CardTitle>
          <CardDescription>Votre soumission sera vérifiée avant publication.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <StatusBadge status={result.authorization_status} />
          <p className="text-sm text-muted-foreground">
            {song.title} — {song.artist.name}
          </p>
        </CardContent>
        <CardFooter>
          <Button variant="outline" render={<Link href={`/songs/${song.slug}/lyrics`} />}>
            Voir le statut
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card>
      <form onSubmit={handleSubmit} noValidate>
        <CardHeader>
          <CardTitle>Proposer des paroles</CardTitle>
          <CardDescription>
            Chanson : {song.title} — {song.artist.name}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="language">Langue</Label>
            <select
              id="language"
              value={languageId}
              onChange={(event) => setLanguageId(event.target.value)}
              disabled={submitMutation.isPending}
              className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm"
            >
              {(languagesQuery.data?.data ?? [song.original_language]).map((language) => (
                <option key={language.id} value={language.id}>
                  {language.name}
                </option>
              ))}
            </select>
            {fieldErrors.language_id && (
              <p role="alert" className="text-sm text-destructive">
                {fieldErrors.language_id.join(" ")}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="content">Paroles</Label>
            <textarea
              id="content"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              rows={10}
              disabled={submitMutation.isPending}
              aria-invalid={fieldErrors.content ? true : undefined}
              aria-describedby={fieldErrors.content ? "content-error" : undefined}
              className="rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            {fieldErrors.content && (
              <p id="content-error" role="alert" className="text-sm text-destructive">
                {fieldErrors.content.join(" ")}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="source-url">Lien source (optionnel)</Label>
            <Input
              id="source-url"
              type="url"
              value={sourceUrl}
              onChange={(event) => setSourceUrl(event.target.value)}
              disabled={submitMutation.isPending}
              aria-invalid={fieldErrors.source_url ? true : undefined}
            />
            {fieldErrors.source_url && (
              <p role="alert" className="text-sm text-destructive">
                {fieldErrors.source_url.join(" ")}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="rights-holder">Détenteur des droits (optionnel)</Label>
            <Input
              id="rights-holder"
              type="text"
              value={rightsHolder}
              onChange={(event) => setRightsHolder(event.target.value)}
              disabled={submitMutation.isPending}
              aria-invalid={fieldErrors.rights_holder ? true : undefined}
            />
            {fieldErrors.rights_holder && (
              <p role="alert" className="text-sm text-destructive">
                {fieldErrors.rights_holder.join(" ")}
              </p>
            )}
          </div>

          {formError && (
            <p role="alert" className="text-sm text-destructive">
              {formError}
            </p>
          )}

          <p className="text-sm text-muted-foreground">Votre soumission sera vérifiée avant publication.</p>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={submitMutation.isPending} className="w-full">
            {submitMutation.isPending ? "Envoi..." : "Envoyer ma proposition"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
