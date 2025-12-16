"use client";

import { useTransition, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { updateProfileAction } from "@/app/profile/actions";

const schema = z.object({
  name: z.string().min(1),
  age: z.number().int().min(0).max(120).nullable().optional(),
  sex: z.enum(["male", "female"]).nullable().optional(),
  country: z.string().max(100).nullable().optional(),
  pregnant: z.boolean().nullable().optional(),
});

export function ProfileForm({ user }: { user: any }) {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isPending, startTransition] = useTransition();

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: user.name ?? "",
      age: user.age ?? null,
      sex: (user.sex as "female" | "male" | null) ?? null,
      country: user.country ?? "",
      pregnant: user.pregnant ?? null,
    },
  });

  const sex = form.watch("sex");

  function onSubmit(values: z.infer<typeof schema>) {
    setError(null);
    setSuccess(false);

    startTransition(async () => {
      const result = await updateProfileAction(values);

      if (result?.error) {
        setError(result.error);
      } else {
        setSuccess(true);
      }
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert>
            <AlertDescription>Profile updated successfully.</AlertDescription>
          </Alert>
        )}

        {/* name */}
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl><Input {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* age */}
        <FormField
          control={form.control}
          name="age"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Age</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  value={field.value ?? ""}
                  onChange={(e) =>
                    field.onChange(e.target.value === "" ? null : Number(e.target.value))
                  }
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* sex */}
        <FormField
          control={form.control}
          name="sex"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Sex</FormLabel>
              <FormControl>
                <select
                  className="border rounded-md p-2"
                  value={field.value ?? ""}
                  onChange={(e) =>
                    field.onChange(e.target.value === "" ? null : e.target.value)
                  }
                >
                  <option value="">Select</option>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </FormControl>
            </FormItem>
          )}
        />

        {/* pregnant */}
        <FormField
          control={form.control}
          name="pregnant"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Pregnant</FormLabel>
              <FormControl>
                <select
                  className="border rounded-md p-2"
                  disabled={sex !== "female"}
                  value={
                    field.value === null || field.value === undefined
                      ? ""
                      : field.value
                        ? "yes"
                        : "no"
                  }
                  onChange={(e) => {
                    if (e.target.value === "") return field.onChange(null);
                    field.onChange(e.target.value === "yes");
                  }}
                >
                  <option value="">Select</option>
                  <option value="yes" disabled={sex !== "female"}>
                    Yes
                  </option>
                  <option value="no">No</option>
                </select>
              </FormControl>
              {sex !== "female" && (
                <p className="text-xs text-muted-foreground">
                  Pregnancy is only applicable to female users.
                </p>
              )}
            </FormItem>
          )}
        />

        {/* country */}
        <FormField
          control={form.control}
          name="country"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Country</FormLabel>
              <FormControl><Input {...field} /></FormControl>
            </FormItem>
          )}
        />

        <Button disabled={isPending} type="submit">
          {isPending ? "Saving…" : "Save changes"}
        </Button>
      </form>
    </Form>
  );
}
