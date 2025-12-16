import Link from "next/link";

import { SignInForm } from "@/components/auth/sign-in-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const metadata = {
  title: "Sign in — HemoVita"
};

export default function SignInPage() {
  return (
    <div className="mx-auto grid max-w-xl gap-6">
      <Card className="rounded-3xl border-0 bg-white/70 shadow-xl backdrop-blur">
        <CardHeader className="space-y-3 text-center">
          <CardTitle className="text-3xl font-semibold">Welcome back</CardTitle>
          {/* <CardDescription>Sign in to continue your hematology tracking journey.</CardDescription> */}
        </CardHeader>
        <CardContent>
          <SignInForm />
          <p className="mt-6 text-center text-sm text-muted-foreground">
            New to HemoVita?{" "}
            <Button asChild variant="link" className="font-semibold">
              <Link href="/sign-up">Create an account</Link>
            </Button>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
