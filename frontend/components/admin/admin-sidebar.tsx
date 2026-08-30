"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

/** Modération traductions volontairement absente — hors périmètre Phase 8.7. */
const ITEMS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/lyrics", label: "Modération paroles" },
  { href: "/admin/rights-records", label: "Rights Records" },
] as const;

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Navigation administration"
      className="flex shrink-0 gap-2 overflow-x-auto md:w-48 md:flex-col md:overflow-visible"
    >
      {ITEMS.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "shrink-0 rounded-lg px-3 py-2 text-sm",
              isActive ? "bg-muted font-medium" : "text-muted-foreground hover:bg-muted/50"
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
