"use client";

import { useState } from "react";
import { useUser } from "@/components/session";
import { Button, Card, ErrorNote, Field, Input, PageHeader, SuccessNote } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { date } from "@/lib/format";

export default function AccountPage() {
  const user = useUser();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [repeat, setRepeat] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setDone(false);
    if (next !== repeat) return setError("The new passwords do not match.");
    setBusy(true);
    try {
      await api("/api/auth/password", { method: "POST", json: { current_password: current, new_password: next } });
      setDone(true);
      setCurrent(""); setNext(""); setRepeat("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not change the password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader title="My account" />
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Profile">
          <dl className="grid grid-cols-3 gap-y-3 text-sm">
            <dt className="text-ink-2">Name</dt><dd className="col-span-2">{user.full_name}</dd>
            <dt className="text-ink-2">Username</dt><dd className="col-span-2 font-mono">{user.username}</dd>
            <dt className="text-ink-2">Role</dt><dd className="col-span-2 capitalize">{user.role}</dd>
            {user.student_code && <><dt className="text-ink-2">Student code</dt><dd className="col-span-2">{user.student_code}</dd></>}
            <dt className="text-ink-2">Last sign-in</dt><dd className="col-span-2">{date(user.last_login)}</dd>
          </dl>
        </Card>
        <Card title="Change password">
          <form onSubmit={submit} className="space-y-3">
            <Field label="Current password"><Input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" /></Field>
            <Field label="New password" hint="At least 8 characters"><Input type="password" value={next} onChange={(e) => setNext(e.target.value)} required minLength={8} autoComplete="new-password" /></Field>
            <Field label="Repeat new password"><Input type="password" value={repeat} onChange={(e) => setRepeat(e.target.value)} required autoComplete="new-password" /></Field>
            {error && <ErrorNote message={error} />}
            {done && <SuccessNote>Password changed.</SuccessNote>}
            <Button type="submit" busy={busy}>Change password</Button>
          </form>
        </Card>
      </div>
    </>
  );
}
