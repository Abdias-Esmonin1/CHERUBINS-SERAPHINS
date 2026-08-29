"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { useAuth } from "@/providers/auth-provider";
import { ApiClientError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoginPending } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    try {
      await login({ email, password });
      router.push("/");
    } catch (error) {
      // INVALID_CREDENTIALS (401) et ACCOUNT_DISABLED (403) portent déjà
      // un message utilisateur sûr côté backend (anti-énumération) — on
      // l'affiche tel quel, jamais de détail technique.
      setFormError(
        error instanceof ApiClientError ? error.message : "Une erreur inattendue est survenue."
      );
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <Card className="w-full max-w-sm">
        <form onSubmit={handleSubmit} noValidate>
          <CardHeader>
            <CardTitle>Connexion</CardTitle>
            <CardDescription>Accédez à votre compte Chérubins &amp; Séraphins.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                disabled={isLoginPending}
                aria-invalid={formError ? true : undefined}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={isLoginPending}
                aria-invalid={formError ? true : undefined}
                aria-describedby={formError ? "login-error" : undefined}
              />
            </div>
            {formError && (
              <p id="login-error" role="alert" className="text-sm text-destructive">
                {formError}
              </p>
            )}
          </CardContent>
          <CardFooter className="flex flex-col gap-3">
            <Button type="submit" disabled={isLoginPending} className="w-full">
              {isLoginPending ? "Connexion..." : "Se connecter"}
            </Button>
            <p className="text-sm text-muted-foreground">
              Pas encore de compte ?{" "}
              <Link href="/register" className="underline underline-offset-2">
                S&apos;inscrire
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </main>
  );
}
