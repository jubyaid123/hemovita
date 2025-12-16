import { NextResponse } from "next/server";

import { getServerAuthSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

const REC_ENGINE_URL =
  process.env.REC_ENGINE_URL ?? "http://127.0.0.1:8000";

/**
 * Proxy labs -> FastAPI /api/report and save labs to Prisma.
 */
export async function POST(req: Request) {
  // 1) Auth check
  const session = await getServerAuthSession();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // 2) Parse body
  let body: any;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body" },
      { status: 400 },
    );
  }

  const { labs, patient, diet_filter } = body ?? {};

  if (!labs || typeof labs !== "object") {
    return NextResponse.json(
      { error: "Missing labs payload" },
      { status: 400 },
    );
  }

  try {
    // 3) Call FastAPI backend (NOTE: /api/report, not /report)
    const backendRes = await fetch(`${REC_ENGINE_URL}/api/report`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        labs,
        patient: patient ?? null,
        diet_filter: diet_filter ?? null,
      }),
    });

    const backendText = await backendRes.text();

    if (!backendRes.ok) {
      console.error(
        "Backend /api/report error",
        backendRes.status,
        backendText,
      );
      return NextResponse.json(
        {
          error: "Backend report service failed",
          details: backendText,
        },
        { status: 502 },
      );
    }

    const report = JSON.parse(backendText);

    // 4) Save labs to Prisma as a LabEntry
    //    Only numeric lab fields will be persisted
    const labData: Record<string, number> = {};
    for (const [key, value] of Object.entries(labs)) {
      if (typeof value === "number" && !Number.isNaN(value)) {
        labData[key] = value;
      }
    }

    await prisma.labEntry.create({
      data: {
        userId: session.user.id,
        ...labData,
      },
    });

    // 5) Return whatever the backend sent
    return NextResponse.json(report, { status: 200 });
  } catch (err) {
    console.error("Error calling backend report service", err);
    return NextResponse.json(
      { error: "Internal error talking to report service" },
      { status: 500 },
    );
  }
}
