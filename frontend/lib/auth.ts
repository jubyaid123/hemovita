import { PrismaAdapter } from "@next-auth/prisma-adapter";
import type { NextAuthOptions } from "next-auth";
import { getServerSession } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";

import { prisma } from "./prisma";

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  session: {
    strategy: "jwt",
  },
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const user = await prisma.user.findUnique({
          where: { email: credentials.email },
        });

        if (!user || !user.passwordHash) {
          return null;
        }

        const isValid = await bcrypt.compare(
          credentials.password,
          user.passwordHash
        );

        if (!isValid) return null;

        // Fields that will be encoded into the JWT / session
        return {
          id: user.id,
          name: user.name,
          email: user.email,
          age: user.age ?? null,
          sex: (user.sex as "female" | "male" | null) ?? null,
          country: user.country ?? null,
          pregnant: user.pregnant ?? null,
        };
      },
    }),
  ],
  pages: {
    signIn: "/sign-in",
  },
  callbacks: {
    async jwt({ token, user }) {
      // First time: user is defined after authorize()
      if (user) {
        token.id = (user as any).id;
        token.name = user.name;
        token.email = user.email;

        token.age = (user as any).age ?? null;
        token.sex = (user as any).sex ?? null;
        token.country = (user as any).country ?? null;
        token.pregnant = (user as any).pregnant ?? null;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.age = (token as any).age ?? null;
        session.user.sex = (token as any).sex ?? null;
        session.user.country = (token as any).country ?? null;
        session.user.pregnant = (token as any).pregnant ?? null;
      }
      return session;
    },
  },
};

// Helper for server components / server actions / middleware
export function getServerAuthSession() {
  return getServerSession(authOptions);
}
