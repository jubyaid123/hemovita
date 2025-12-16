"use client";

import Link from "next/link";
import { useState, useTransition } from "react";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Button } from "@/components/ui/button";

type LabEntry = {
  id: string;
  createdAt: string | Date;
  Hemoglobin: number | null;
  ferritin: number | null;
  vitamin_D: number | null;
};

export function LabHistory({ initialEntries }: { initialEntries: LabEntry[] }) {
  const [entries, setEntries] = useState(
    initialEntries.map((e) => ({
      ...e,
      createdAt: new Date(e.createdAt),
    })),
  );

  const [isPending, startTransition] = useTransition();

  async function handleDelete(id: string) {
    try {
      const res = await fetch(`/api/labs/${id}`, { method: "DELETE" });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      console.error("Failed to delete lab entry", err);
    }
  }

  return (
    <Card className="rounded-3xl border-0 bg-white/80 shadow-xl backdrop-blur">
      <CardHeader>
        <CardTitle>Previous lab entries</CardTitle>
        <CardDescription>Your 10 most recent saved panels.</CardDescription>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            You don&apos;t have any saved lab entries yet. Run your first analysis to see it here.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Hemoglobin</TableHead>
                <TableHead>Ferritin</TableHead>
                <TableHead>Vitamin D</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell className="whitespace-nowrap text-sm">
                    {entry.createdAt instanceof Date
                      ? entry.createdAt.toLocaleString()
                      : String(entry.createdAt)}
                  </TableCell>
                  <TableCell>{entry.Hemoglobin ?? "—"}</TableCell>
                  <TableCell>{entry.ferritin ?? "—"}</TableCell>
                  <TableCell>{entry.vitamin_D ?? "—"}</TableCell>
                  <TableCell className="flex justify-end gap-2">
                    <Button asChild variant="ghost" size="sm">
                      <Link href={`/labs/${entry.id}`}>View</Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={isPending}
                      onClick={() => handleDelete(entry.id)}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

