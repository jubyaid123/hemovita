import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getServerAuthSession } from "@/lib/auth";

const highlights = [
  "Accurate, clinically backed lab ranges",
  "Instant, personalized guidance",
  "Your data stays private and secure",
];

export default async function LandingPage() {
  const session = await getServerAuthSession();
  const isLoggedIn = !!session?.user;

  return (
    <div className="relative w-full">
      <section className="mx-auto grid max-w-4xl gap-10 text-center">
        <Badge
          variant="secondary"
          className="mx-auto px-4 py-1 uppercase tracking-wide text-xs text-muted-foreground"
        >
          Smarter micronutrient tracking
        </Badge>

        <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">
          Understand your blood health with clarity and personalised guidance.
        </h1>

        <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
          HemoVita transforms raw blood test data into clear, personalized health recommendations.
        </p>

        {/* 🔹 Only show these buttons if the user is NOT logged in */}
        {!isLoggedIn && (
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Button asChild size="lg">
              <Link href="/sign-up">Sign up</Link>
            </Button>

            <Button asChild size="lg" variant="outline">
              <Link href="/sign-in">Log in</Link>
            </Button>

            <Button asChild size="lg" variant="ghost" className="gap-2">
              <Link href="/labs/new">
                Try demo
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        )}
      </section>

      <section className="mt-16 grid gap-8 sm:grid-cols-2">
        <Card className="border-0 bg-white/70 shadow-xl backdrop-blur">
          <CardHeader>
            <CardTitle>For clinicians &amp; self-advocates</CardTitle>
            <CardDescription>Bring order to complex micronutrient assessments.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {highlights.map((item) => (
              <div key={item} className="flex items-start gap-3 text-left">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Check className="h-4 w-4" />
                </span>
                <p className="text-sm text-muted-foreground">{item}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-0 bg-white/70 shadow-xl backdrop-blur">
          <CardHeader>
            <CardTitle>Streamlined workflow</CardTitle>
            {/* <CardDescription>Enter your labs quickly, get answers instantly.</CardDescription> */}
          </CardHeader>
          <CardContent className="space-y-3 text-left text-sm text-muted-foreground">
            <p>Enter your labs quickly, get answers instantly</p>
            <Separator />
            <p>Helpful prompts and tooltips walk you through every marker.</p>
            <Separator />
            <p>Access your previous results whenever you need them.</p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
