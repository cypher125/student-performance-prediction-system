"use client";

import { BrainCircuit } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
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
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand text-white"><BrainCircuit size={24} aria-hidden /></div>
          <div>
            <h1 className="text-xl font-semibold">Student Performance Prediction System</h1>
            <p className="text-sm text-ink-2">Department of Computer Science, YABATECH</p>
          </div>
        </div>

        <form onSubmit={submit} className="space-y-4 rounded-xl border border-line bg-surface p-6">
          <h2 className="text-base font-semibold">Sign in</h2>
          {error && <ErrorNote message={error} />}
          <Field label="Username">
            <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required autoFocus />
          </Field>
          <Field label="Password">
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
          </Field>
          <Button type="submit" busy={busy} className="w-full">Sign in</Button>
        </form>

        <details className="mt-4 rounded-xl border border-line bg-surface p-4 text-sm">
          <summary className="cursor-pointer font-medium">Demo accounts (simulated data)</summary>
          <table className="mt-3 w-full text-left text-xs">
            <tbody className="divide-y divide-line">
              {DEMO.map(([role, user, pass]) => (
                <tr key={role}><td className="py-1.5 pr-2 text-ink-2">{role}</td><td className="py-1.5 pr-2 font-mono">{user}</td><td className="py-1.5 font-mono">{pass}</td></tr>
              ))}
            </tbody>
          </table>
        </details>
      </div>
    </div>
  );
}
