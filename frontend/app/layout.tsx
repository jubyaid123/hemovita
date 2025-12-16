import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

import { SiteHeader } from "@/components/layout/site-header";
import AuthSessionProvider from "@/components/providers/session-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "HemoVita",
  description: "Track hematology and micronutrient labs with clarity.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} gradient-bg min-h-screen bg-background`}>
        <AuthSessionProvider>
          {/* Full-width header (not constrained by the page container) */}
          <SiteHeader />

          {/* Page container applies only to content */}
          <div className="mx-auto w-full max-w-[1200px] px-6 pb-12">
            <main className="py-10">{children}</main>
          </div>
        </AuthSessionProvider>
      </body>
    </html>
  );
}

