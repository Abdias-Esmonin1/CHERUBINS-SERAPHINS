import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Chérubins &amp; Séraphins</CardTitle>
          <CardDescription>
            Fondation frontend (Phase 8.1) — Next.js, Tailwind CSS et
            shadcn/ui sont opérationnels.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button>Composant shadcn/ui</Button>
        </CardContent>
      </Card>
    </main>
  );
}
