// frontend/app/labs/new/page.tsx
import { redirect } from "next/navigation";

import { getServerAuthSession } from "@/lib/auth";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { LabForm } from "@/components/labs/lab-form";

export default async function NewLabPage() {
  const session = await getServerAuthSession();

  if (!session?.user) {
    redirect("/sign-in");
  }

  return (
    <div className="space-y-6">
      <Card className="rounded-3xl border-0 bg-white/80 shadow-xl backdrop-blur">
        <CardHeader>
          <CardTitle>New lab entry</CardTitle>
          <CardDescription>
            Enter the markers from your latest bloodwork to generate personalised
            insights
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            You can leave any field blank if it wasn&apos;t measured in this panel.
          </p>
        </CardContent>
      </Card>

      <LabForm />
    </div>
  );
}
