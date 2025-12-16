import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { z } from "zod";

import { prisma } from "@/lib/prisma";

// --- Matches the payload the signup form sends AFTER conversion ---
const registerSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  password: z.string().min(8),

  age: z.number().int().min(0).max(120).optional(),
  sex: z.enum(["female", "male"]).optional(),
  country: z.string().max(100).optional(),
  pregnant: z.boolean().optional(),
});

export async function POST(req: Request) {
  try {
    const body = await req.json();

    // Validate the incoming payload
    const parsed = registerSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: "Invalid registration data." },
        { status: 400 }
      );
    }

    const { name, email, password, age, sex, country, pregnant } = parsed.data;

    // Check if email already exists
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
      return NextResponse.json(
        { error: "Email is already in use." },
        { status: 400 }
      );
    }

    // Hash password
    const passwordHash = await bcrypt.hash(password, 10);

    // Create user
    const user = await prisma.user.create({
      data: {
        name,
        email,
        passwordHash,
        age,
        sex,
        country,
        pregnant,
      },
    });

    return NextResponse.json(
      { id: user.id, email: user.email },
      { status: 201 }
    );
  } catch (error) {
    console.error("REGISTER ERROR:", error);
    return NextResponse.json(
      { error: "Registration failed." },
      { status: 500 }
    );
  }
}
