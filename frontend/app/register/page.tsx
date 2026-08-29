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

export default function RegisterPage() {
  const router = useRouter();
  const { register, isRegisterPending } = useAuth();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setFieldErrors({});

    try {
      // Le backend pose le cookie HttpOnly dès l'inscription (auto-login,
      // confirmé dans backend/app/routers/auth.py) — pas de login()
      // supplémentaire nécessaire après un register réussi.
      await register({ email, username, password });
      router.push("/");
    } catch (error) {
      if (error instanceof ApiClientError) {
        setFormError(error.message);
        setFieldErrors(error.fieldErrors);
      } else {
        setFormError("Une erreur inattendue est survenue.");
      }
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <Card className="w-full max-w-sm">
        <form onSubmit={handleSubmit} noValidate>
          <CardHeader>
            <CardTitle>Créer un compte</CardTitle>
            <CardDescription>Rejoignez Chérubins &amp; Séraphins.</CardDescription>
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
                disabled={isRegisterPending}
                aria-invalid={fieldErrors.email ? true : undefined}
                aria-describedby={fieldErrors.email ? "email-error" : undefined}
              />
              {fieldErrors.email && (
                <p id="email-error" role="alert" className="text-sm text-destructive">
                  {fieldErrors.email.join(" ")}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="username">Nom d&apos;utilisateur</Label>
              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                disabled={isRegisterPending}
                aria-invalid={fieldErrors.username ? true : undefined}
                aria-describedby={fieldErrors.username ? "username-error" : undefined}
              />
              {fieldErrors.username && (
                <p id="username-error" role="alert" className="text-sm text-destructive">
                  {fieldErrors.username.join(" ")}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={isRegisterPending}
                aria-invalid={fieldErrors.password ? true : undefined}
                aria-describedby={fieldErrors.password ? "password-error" : undefined}
              />
              {fieldErrors.password && (
                <p id="password-error" role="alert" className="text-sm text-destructive">
                  {fieldErrors.password.join(" ")}
                </p>
              )}
            </div>
            {formError && (
              <p role="alert" className="text-sm text-destructive">
                {formError}
              </p>
            )}
          </CardContent>
          <CardFooter className="flex flex-col gap-3">
            <Button type="submit" disabled={isRegisterPending} className="w-full">
              {isRegisterPending ? "Inscription..." : "S'inscrire"}
            </Button>
            <p className="text-sm text-muted-foreground">
              Déjà un compte ?{" "}
              <Link href="/login" className="underline underline-offset-2">
                Se connecter
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </main>
  );
}
