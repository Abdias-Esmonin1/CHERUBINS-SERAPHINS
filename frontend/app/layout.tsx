import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { AuthProvider } from "@/providers/auth-provider";
import { DesktopHeader } from "@/components/layout/desktop-header";
import { BottomNavigation } from "@/components/layout/bottom-navigation";

export const metadata: Metadata = {
  title: "Chérubins & Séraphins",
  description: "Moteur de recherche intelligent de chants chrétiens.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className="antialiased">
        <QueryProvider>
          <AuthProvider>
            <DesktopHeader />
            <div className="pb-14 md:pb-0">{children}</div>
            <BottomNavigation />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
