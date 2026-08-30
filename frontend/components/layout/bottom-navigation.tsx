"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Heart, Home, Search, User } from "lucide-react";

import { useAuth } from "@/providers/auth-provider";
import { cn } from "@/lib/utils";

/** "Favoris" pointe vers une page non encore implémentée (Phase 8.5) — voir DesktopHeader. */
const ITEMS = [
  { href: "/", label: "Accueil", icon: Home },
  { href: "/search", label: "Recherche", icon: Search },
  { href: "/favorites", label: "Favoris", icon: Heart },
] as const;

export function BottomNavigation() {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();

  return (
    <nav
      aria-label="Navigation principale"
      className="fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-background md:hidden"
    >
      {ITEMS.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "flex flex-1 flex-col items-center gap-0.5 py-2 text-xs",
              isActive ? "text-primary" : "text-muted-foreground"
            )}
          >
            <Icon className="size-5" aria-hidden />
            {item.label}
          </Link>
        );
      })}
      <Link
        href={isAuthenticated ? "/profile" : "/login"}
        aria-current={pathname === "/profile" || pathname === "/login" ? "page" : undefined}
        className={cn(
          "flex flex-1 flex-col items-center gap-0.5 py-2 text-xs",
          pathname === "/profile" || pathname === "/login" ? "text-primary" : "text-muted-foreground"
        )}
      >
        <User className="size-5" aria-hidden />
        {isAuthenticated ? "Profil" : "Connexion"}
      </Link>
    </nav>
  );
}
