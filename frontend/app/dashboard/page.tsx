import Link from "next/link";
import { redirect } from "next/navigation";

import { getServerAuthSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LabHistory } from "@/components/dashboard/lab-history";

export default async function DashboardPage() {
  const session = await getServerAuthSession();

  if (!session?.user) {
    redirect("/sign-in");
  }

  const entries = await prisma.labEntry.findMany({
    where: { userId: session.user.id },
    orderBy: { createdAt: "desc" },
    take: 10,
  });

  return (
    <div className="space-y-6">
      <Card className="rounded-3xl border-0 bg-white/80 shadow-xl backdrop-blur">
        <CardHeader className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <CardTitle>
              Welcome back{session.user.name ? `, ${session.user.name}` : ""}
            </CardTitle>
            <CardDescription>
              Start a new lab analysis or review your previous entries.
            </CardDescription>
          </div>
          <Button asChild size="lg" className="rounded-full">
            <Link href="/labs/new">New lab entry</Link>
          </Button>
        </CardHeader>
      </Card>

      <LabHistory initialEntries={entries} />
    </div>
  );
}
