"use client";

import { X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { SessionContext } from "@/components/session";
import { SiteFooter, TopBar } from "@/components/topbar";
import { Loading } from "@/components/ui";
import { api } from "@/lib/api";
import type { Role, User } from "@/lib/types";

const NAV: { href: string; label: string; roles: Role[] }[] = [
  { href: "/dashboard/", label: "Dashboard", roles: ["admin", "lecturer", "adviser", "student"] },
  { href: "/students/", label: "Students", roles: ["admin", "lecturer", "adviser"] },
  { href: "/records/", label: "Records & upload", roles: ["admin", "lecturer", "adviser"] },
  { href: "/alerts/", label: "Alerts", roles: ["admin", "lecturer", "adviser"] },
  { href: "/reports/", label: "Reports", roles: ["admin", "lecturer", "adviser"] },
  { href: "/model/", label: "Model", roles: ["admin", "lecturer", "adviser"] },
  { href: "/users/", label: "Users", roles: ["admin"] },
  { href: "/account/", label: "My account", roles: ["admin", "lecturer", "adviser", "student"] },
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
  const menu = (
    <nav className="py-4" aria-label="Main menu">
      <p className="px-5 pb-2 text-[11px] font-semibold uppercase tracking-wider text-muted">Menu</p>
      {links.map(({ href, label }) => {
        const active = pathname.startsWith(href.replace(/\/$/, ""));
        return (
          <Link key={href} href={href} aria-current={active ? "page" : undefined}
            className={`block border-l-[3px] px-5 py-2 text-sm ${active
              ? "border-gold bg-brand-soft font-semibold text-brand"
              : "border-transparent text-ink-2 hover:bg-page hover:text-ink"}`}>
            {label}
          </Link>
        );
      })}
    </nav>
  );

  const account = (
    <>
      <div className="hidden text-right leading-tight sm:block">
        <p className="text-sm font-medium">{user.full_name}</p>
        <p className="text-xs text-white/75">{ROLE_LABEL[user.role]}</p>
      </div>
      <button onClick={signOut} className="rounded border border-white/40 px-3 py-1.5 text-sm font-medium text-white hover:bg-white/10">
        Sign out
      </button>
    </>
  );

  return (
    <SessionContext.Provider value={user}>
      <div className="flex min-h-screen flex-col">
        <TopBar right={account} onMenu={() => setMenuOpen(true)} />
        <div className="flex flex-1">
          <aside className="no-print hidden w-60 shrink-0 border-r border-line bg-surface lg:block">{menu}</aside>
          <div className="flex min-w-0 flex-1 flex-col">
            <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 lg:px-8">{children}</main>
            <SiteFooter />
          </div>
        </div>

        {menuOpen && (
          <div className="fixed inset-0 z-40 bg-black/30 lg:hidden" onClick={() => setMenuOpen(false)}>
            <div className="h-full w-64 border-r border-line bg-surface" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between border-b border-line px-5 py-3">
                <p className="text-sm font-semibold">{user.full_name}<span className="block text-xs font-normal text-muted">{ROLE_LABEL[user.role]}</span></p>
                <button onClick={() => setMenuOpen(false)} aria-label="Close menu" className="p-1 text-ink-2"><X size={20} /></button>
              </div>
              {menu}
            </div>
          </div>
        )}
      </div>
    </SessionContext.Provider>
  );
}
