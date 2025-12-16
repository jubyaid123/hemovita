import Link from "next/link";

import { SignUpForm } from "@/components/auth/sign-up-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const metadata = {
  title: "Create account — HemoVita"
};

export default function SignUpPage() {
  return (
    <div className="mx-auto grid max-w-xl gap-6">
      <Card className="rounded-3xl border-0 bg-white/70 shadow-xl backdrop-blur">
        <CardHeader className="space-y-3 text-center">
          <CardTitle className="text-3xl font-semibold">Create your HemoVita account</CardTitle>
          {/* <CardDescription>Securely track hematology and micronutrient labs.</CardDescription> */}
        </CardHeader>
        <CardContent>
          <SignUpForm />
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Button asChild variant="link" className="font-semibold">
              <Link href="/sign-in">Sign in</Link>
            </Button>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
