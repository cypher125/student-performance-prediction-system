"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { SiteFooter, TopBar } from "@/components/topbar";
import { Button, ErrorNote, Field, Input } from "@/components/ui";
import { api, ApiError } from "@/lib/api";

const DEMO = [
  ["Administrator", "admin", "Admin@2026"],
  ["Lecturer", "lecturer", "Lecturer@2026"],
  ["Academic adviser", "adviser", "Adviser@2026"],
  ["Student", "student code, e.g. s0379", "Student@2026"],
];

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api("/api/auth/login", { method: "POST", json: { username, password } });
      router.replace("/dashboard/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the server.");
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <TopBar right={<p className="hidden text-sm text-white/80 md:block">Department of Computer Science</p>} />
      <main className="flex flex-1 justify-center px-4 py-10 sm:py-14">
        <div className="w-full max-w-md">
          <section className="rounded border border-line bg-surface">
            <div className="border-b border-line bg-panel px-6 py-5 text-center">
              {/* eslint-disable-next-line @next/next/no-img-element -- static export serves files as they are */}
              <img src="/crest.png" alt="Yaba College of Technology crest" className="mx-auto h-16 w-16" />
              <h1 className="mt-3 text-lg font-semibold">Sign in</h1>
              <p className="mt-1 text-sm text-ink-2">Use the username and password given to you by the department.</p>
            </div>
            <form onSubmit={submit} className="space-y-4 px-6 py-5">
              {error && <ErrorNote message={error} />}
              <Field label="Username">
                <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required autoFocus />
              </Field>
              <Field label="Password">
                <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
              </Field>
              <Button type="submit" busy={busy} className="w-full">Sign in</Button>
            </form>
          </section>

          <details className="mt-4 rounded border border-line bg-surface px-4 py-3 text-sm">
            <summary className="cursor-pointer font-medium">Demo accounts (simulated data)</summary>
            <table className="mt-3 w-full text-left text-xs">
              <tbody className="divide-y divide-line-soft">
                {DEMO.map(([role, user, pass]) => (
                  <tr key={role}><td className="py-1.5 pr-2 text-ink-2">{role}</td><td className="py-1.5 pr-2 font-mono">{user}</td><td className="py-1.5 font-mono">{pass}</td></tr>
                ))}
              </tbody>
            </table>
          </details>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
