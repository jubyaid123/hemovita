import NextAuth, { type DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session extends DefaultSession {
    user: DefaultSession["user"] & {
      id: string;
      age?: number | null;
      sex?: "female" | "male" | null;
      country?: string | null;
      pregnant?: boolean | null;
    };
  }

  interface User {
    id: string;
    age?: number | null;
    sex?: "female" | "male" | null;
    country?: string | null;
    pregnant?: boolean | null;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id?: string;
    age?: number | null;
    sex?: "female" | "male" | null;
    country?: string | null;
    pregnant?: boolean | null;
  }
}
