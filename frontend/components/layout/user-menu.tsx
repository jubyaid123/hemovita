"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { LogOut, User } from "lucide-react";
import { signOut } from "next-auth/react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

type NavUserMenuProps = {
  user: {
    id: string;
    name: string | null;
    email: string;
  };
};

export function NavUserMenu({ user }: NavUserMenuProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      window.addEventListener("click", onClick);
    }
    return () => window.removeEventListener("click", onClick);
  }, [open]);

  return (
    <div className="relative" ref={containerRef}>
      <Button
        variant="secondary"
        className="flex items-center gap-2 rounded-full px-4"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary">
          {user.name ? user.name.charAt(0).toUpperCase() : "U"}
        </span>
        <div className="hidden text-left text-sm leading-tight md:block">
          <p className="font-semibold text-foreground">{user.name ?? "Member"}</p>
          <p className="text-xs text-muted-foreground">{user.email}</p>
        </div>
      </Button>
      {open ? (
        <div className="absolute right-0 mt-2 w-52 rounded-2xl border bg-card p-3 shadow-lg">
          <p className="text-xs font-medium text-muted-foreground">Signed in as</p>
          <p className="text-sm font-semibold text-foreground">{user.email}</p>
          <Separator className="my-3" />
          <div className="flex flex-col gap-2">
            <Link
              href="/profile"
              className="flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
              onClick={() => setOpen(false)}
            >
              <User className="h-4 w-4" /> Profile
            </Link>
            <button
              type="button"
              onClick={async () => {
                setOpen(false);
                await signOut({ callbackUrl: "/" });
              }}
              className="flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium text-destructive transition-colors hover:bg-secondary"
            >
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
