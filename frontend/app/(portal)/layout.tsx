"use client";

import {
  Bell, BrainCircuit, FileBarChart, GraduationCap, LayoutDashboard, LogOut, Menu, Upload, UserCog, Users, X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loading } from "@/components/ui";
import { SessionContext } from "@/components/session";
import { api } from "@/lib/api";
import type { Role, User } from "@/lib/types";

const NAV: { href: string; label: string; Icon: typeof Bell; roles: Role[] }[] = [
  { href: "/dashboard/", label: "Dashboard", Icon: LayoutDashboard, roles: ["admin", "lecturer", "adviser", "student"] },
  { href: "/students/", label: "Students", Icon: Users, roles: ["admin", "lecturer", "adviser"] },
  { href: "/records/", label: "Records & upload", Icon: Upload, roles: ["admin", "lecturer", "adviser"] },
  { href: "/alerts/", label: "Alerts", Icon: Bell, roles: ["admin", "lecturer", "adviser"] },
  { href: "/reports/", label: "Reports", Icon: FileBarChart, roles: ["admin", "lecturer", "adviser"] },
  { href: "/model/", label: "Model", Icon: BrainCircuit, roles: ["admin", "lecturer", "adviser"] },
  { href: "/users/", label: "Users", Icon: UserCog, roles: ["admin"] },
  { href: "/account/", label: "My account", Icon: GraduationCap, roles: ["admin", "lecturer", "adviser", "student"] },
];

const ROLE_LABEL: Record<Role, string> = { admin: "Administrator", lecturer: "Lecturer", adviser: "Academic adviser", student: "Student" };

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    api<User>("/api/auth/me").then(setUser).catch(() => router.replace("/login/"));
  }, [router]);

  useEffect(() => setMenuOpen(false), [pathname]);

  async function signOut() {
    await api("/api/auth/logout", { method: "POST" }).catch(() => undefined);
    router.replace("/login/");
  }

  if (!user) return <div className="mx-auto max-w-md p-10"><Loading label="Checking your session…" /></div>;

  const links = NAV.filter((n) => n.roles.includes(user.role));
  const nav = (
    <nav className="flex flex-col gap-1">
      {links.map(({ href, label, Icon }) => {
        const active = pathname.startsWith(href.replace(/\/$/, ""));
        return (
          <Link key={href} href={href}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${active ? "bg-brand-soft text-brand-dark" : "text-ink-2 hover:bg-page hover:text-ink"}`}>
            <Icon size={18} aria-hidden /> {label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <SessionContext.Provider value={user}>
      <div className="flex min-h-screen">
        <aside className="no-print hidden w-64 shrink-0 flex-col border-r border-line bg-surface px-4 py-5 lg:flex">
          <Brand />
          <div className="mt-6 flex-1">{nav}</div>
          <p className="text-xs text-muted">Department of Computer Science · YABATECH</p>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="no-print flex items-center justify-between gap-3 border-b border-line bg-surface px-4 py-3 lg:px-8">
            <button className="rounded-lg p-2 text-ink-2 hover:bg-page lg:hidden" onClick={() => setMenuOpen(true)} aria-label="Open menu">
              <Menu size={20} />
            </button>
            <p className="hidden text-sm text-ink-2 lg:block">AI-powered early warning for student performance</p>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-medium">{user.full_name}</p>
                <p className="text-xs text-muted">{ROLE_LABEL[user.role]}</p>
              </div>
              <button onClick={signOut} className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-sm text-ink-2 hover:bg-page">
                <LogOut size={15} aria-hidden /> Sign out
              </button>
            </div>
          </header>

          {menuOpen && (
            <div className="fixed inset-0 z-40 bg-black/30 lg:hidden" onClick={() => setMenuOpen(false)}>
              <div className="h-full w-72 bg-surface p-4" onClick={(e) => e.stopPropagation()}>
                <div className="mb-6 flex items-center justify-between">
                  <Brand />
                  <button onClick={() => setMenuOpen(false)} aria-label="Close menu" className="p-1 text-ink-2"><X size={20} /></button>
                </div>
                {nav}
              </div>
            </div>
          )}

          <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 lg:px-8">{children}</main>
        </div>
      </div>
    </SessionContext.Provider>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-white"><BrainCircuit size={20} aria-hidden /></div>
      <div className="leading-tight">
        <p className="text-sm font-semibold">Performance Predictor</p>
        <p className="text-xs text-muted">Early-warning system</p>
      </div>
    </div>
  );
}
