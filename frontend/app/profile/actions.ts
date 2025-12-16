"use server";

import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { getServerSession } from "next-auth";

export async function updateProfileAction(values: any) {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    return { error: "Not authenticated." };
  }

  try {
    await prisma.user.update({
      where: { id: session.user.id },
      data: {
        name: values.name,
        age: values.age ?? null,
        sex: values.sex ?? null,
        country: values.country ?? null,
        pregnant: values.pregnant ?? null,
      },
    });

    return { success: true };
  } catch (err) {
    console.error("PROFILE UPDATE ERROR:", err);
    return { error: "Could not update profile. Try again." };
  }
}
