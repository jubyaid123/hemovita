// import { NextResponse } from "next/server";

// import { buildRecommendations } from "@/lib/recommendations";
// import { toLabInputs } from "@/lib/validators/labs";

// export async function POST(req: Request) {
//   try {
//     const body = await req.json();
//     const labs = toLabInputs(body);
//     const payload = buildRecommendations(labs);
//     return NextResponse.json(payload);
//   } catch (error) {
//     console.error("[RECOMMEND]", error);
//     return NextResponse.json({ error: "Unable to process lab inputs." }, { status: 400 });
//   }
// }

import { NextRequest, NextResponse } from "next/server";

const ENGINE_URL = process.env.REC_ENGINE_URL || "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const res = await fetch(`${ENGINE_URL}/api/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    console.error("Error calling rec engine:", err);
    return NextResponse.json(
      { error: "Failed to reach recommendation engine" },
      { status: 500 }
    );
  }
}
