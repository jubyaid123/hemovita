// frontend/app/labs/[id]/page.tsx
import { notFound, redirect } from "next/navigation";

import { getServerAuthSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const REC_ENGINE_URL = process.env.REC_ENGINE_URL ?? "http://127.0.0.1:8000";

type FoodItem = {
  name: string;
  serving_g?: number | null;
  category?: string | null;
};

type RiskMicronutrient = {
  micronutrient: string;
  predicted_risk: number;
};

type RiskMeta = {
  country?: string;
  population?: string;
  gender?: string;
  age?: number;
};

type RiskProfile = {
  overall_risk: number;
  risk_bucket: "low" | "moderate" | "high";
  high_risk_micronutrients: RiskMicronutrient[];
  micronutrient_risks: RiskMicronutrient[];
  summary_text: string;
  meta: RiskMeta;
};

type ReportResponse = {
  labels: Record<string, string>;
  supplement_plan: Record<string, string[]>;
  foods: Record<string, FoodItem[]>;
  network_notes: string[];
  report_text: string;
  risk_profile?: RiskProfile;
  micronutrient_risks?: RiskMicronutrient[];
  risk_summary_text?: string | null;
};

export default async function LabDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const session = await getServerAuthSession();
  if (!session?.user) {
    redirect("/sign-in");
  }

  // 1) Load lab entry and make sure it belongs to this user
  const entry = await prisma.labEntry.findUnique({
    where: { id: params.id },
  });

  if (!entry || entry.userId !== session.user.id) {
    notFound();
  }

  // 2) Build labs object from numeric fields
  const labs: Record<string, number> = {};
  for (const [key, value] of Object.entries(entry)) {
    if (typeof value === "number" && !Number.isNaN(value)) {
      // skip id/userId timestamps automatically because they are not numbers
      labs[key] = value;
    }
  }

  // 3) Load patient info from User table
  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
  });

  const patient = {
    age: user?.age ?? 25,
    sex: (user?.sex === "male" ? "male" : "female") as "male" | "female",
    country: user?.country ?? null,
    notes: null,
    pregnant: user?.pregnant ?? null,
    // optional: if you later add population to PatientPayload
    // population: user?.population ?? null,
  };

  // 4) Call backend report engine directly
  const backendRes = await fetch(`${REC_ENGINE_URL}/api/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      labs,
      patient,
      diet_filter: null,
    }),
    // prevent Next from caching this
    cache: "no-store",
  });

  if (!backendRes.ok) {
    console.error("Backend /api/report failed", backendRes.status);
    notFound();
  }

  const report: ReportResponse = await backendRes.json();

  const createdAt = entry.createdAt instanceof Date
    ? entry.createdAt
    : new Date(entry.createdAt as any);

  // 5) Render – reuse the same visual structure as in LabForm results
  return (
    <div className="space-y-6">
      <Card className="rounded-3xl border-0 bg-white/80 shadow-xl backdrop-blur">
        <CardHeader>
          <CardTitle>Lab report from {createdAt.toLocaleString()}</CardTitle>
          {/* <CardDescription>
            Re-run using your current recommendation engine settings.
          </CardDescription> */}
        </CardHeader>
      </Card>

      {/* Risk profile */}
      {report.risk_profile && (
        <Card className="rounded-3xl border-0 bg-white/80 shadow-xl backdrop-blur">
          <CardHeader>
            <CardTitle>Micronutrient risk overview</CardTitle>
            <CardDescription>
              Based on your age, sex, country and population profile.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex flex-wrap items-baseline gap-4">
              <p className="text-3xl font-semibold">
                {Math.round(report.risk_profile.overall_risk * 100)}%
              </p>
              <Badge
                variant={
                  report.risk_profile.risk_bucket === "low"
                    ? "secondary"
                    : report.risk_profile.risk_bucket === "moderate"
                    ? "outline"
                    : "default"
                }
                className="capitalize"
              >
                {report.risk_profile.risk_bucket} risk
              </Badge>
            </div>

            <p className="text-muted-foreground">
              {report.risk_profile.summary_text}
            </p>

            {report.risk_profile.high_risk_micronutrients.length > 0 && (
              <>
                <Separator />
                <div>
                  <p className="mb-2 font-semibold">Highest-risk micronutrients</p>
                  <div className="flex flex-wrap gap-2">
                    {report.risk_profile.high_risk_micronutrients.map((m) => (
                      <Badge key={m.micronutrient} variant="outline" className="capitalize">
                        {m.micronutrient.replace(/_/g, " ")} ·{" "}
                        {Math.round(m.predicted_risk * 100)}%
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Marker classification */}
      <Card className="rounded-3xl border-0 bg-white/80 shadow-xl backdrop-blur">
        <CardHeader>
          <CardTitle>Marker classification</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Marker</TableHead>
                <TableHead>Value</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(report.labels).map(([marker, status]) => {
                const value = (labs as any)[marker];
                return (
                  <TableRow key={marker}>
                    <TableCell className="font-medium">{marker}</TableCell>
                    <TableCell>{value ?? "—"}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          status === "normal"
                            ? "secondary"
                            : status === "unknown"
                            ? "outline"
                            : "default"
                        }
                      >
                        {status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Supplement schedule, network notes, foods – you can copy the exact JSX
          from the bottom of LabForm (the results section) and paste it here,
          using `report` instead of `result` and `labs` instead of `lastLabs`. */}
    </div>
  );
}
