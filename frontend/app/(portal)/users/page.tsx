"use client";

import { Fragment, useState } from "react";
import { Button, Card, ErrorNote, Field, Input, Loading, PageHeader, Select, SuccessNote, Table, Td } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { date, plural } from "@/lib/format";
import type { Role, User } from "@/lib/types";

const ROLES: Role[] = ["admin", "lecturer", "adviser", "student"];

export default function UsersPage() {
  const { data, error, loading, reload } = useApi<{ count: number; users: User[] }>("/api/users");
  const [roleFilter, setRoleFilter] = useState("staff");
  const [resetting, setResetting] = useState<number | null>(null);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const users = (data?.users ?? []).filter((u) => roleFilter === "" || (roleFilter === "staff" ? u.role !== "student" : u.role === roleFilter));

  async function toggle(user: User) {
    setNote(null);
    try {
      await api(`/api/users/${user.id}`, { method: "PATCH", json: { is_active: !user.is_active } });
    } catch (err) {
      setNote({ ok: false, text: err instanceof ApiError ? err.message : "Could not change the account." });
    }
    reload();
  }

  return (
    <>
      <PageHeader title="User accounts" subtitle="Administrators create accounts and control who can sign in" />
      <NewUser onCreated={reload} />
      <div className="mb-3 mt-5 flex items-center gap-3">
        <div className="w-56">
          <Select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} aria-label="Filter by role">
            <option value="staff">Staff accounts</option><option value="student">Student accounts</option><option value="">All accounts</option>
          </Select>
        </div>
        <span className="text-sm text-ink-2">{plural(users.length, "account")}</span>
      </div>
      {error && <ErrorNote message={error.message} />}
      {note && <div className="mb-3">{note.ok ? <SuccessNote>{note.text}</SuccessNote> : <ErrorNote message={note.text} />}</div>}
      {loading && !data ? <Loading /> : (
        <Table head={["Username", "Name", "Role", "Student", "Last sign-in", "Status", ""]}>
          {users.map((u) => (
            <Fragment key={u.id}>
              <tr>
                <Td className="font-mono text-xs">{u.username}</Td><Td>{u.full_name}</Td><Td className="capitalize">{u.role}</Td>
                <Td>{u.student_code ?? "–"}</Td><Td>{date(u.last_login)}</Td>
                <Td>{u.is_active ? <span className="text-ink">Active</span> : <span className="text-muted">Disabled</span>}</Td>
                <Td>
                  <Button variant="ghost" onClick={() => toggle(u)}>{u.is_active ? "Disable" : "Enable"}</Button>
                  <Button variant="ghost" onClick={() => { setNote(null); setResetting(resetting === u.id ? null : u.id); }}>Reset password</Button>
                </Td>
              </tr>
              {resetting === u.id && (
                <tr><td colSpan={7} className="bg-panel px-3 py-3">
                  <ResetPassword user={u} onDone={(text) => { setResetting(null); setNote({ ok: true, text }); }} onCancel={() => setResetting(null)} />
                </td></tr>
              )}
            </Fragment>
          ))}
        </Table>
      )}
    </>
  );
}

/** Sets a new temporary password for someone who has forgotten theirs. */
function ResetPassword({ user, onDone, onCancel }: { user: User; onDone: (text: string) => void; onCancel: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api(`/api/users/${user.id}`, { method: "PATCH", json: { password } });
      onDone(`New temporary password set for ${user.username}. Give it to them and ask them to change it under My account.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reset the password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
      <div className="w-64">
        <Field label={`New temporary password for ${user.username}`}>
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8}
            placeholder="At least 8 characters" autoComplete="new-password" />
        </Field>
      </div>
      <Button type="submit" busy={busy}>Save password</Button>
      <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
      {error && <div className="w-full"><ErrorNote message={error} /></div>}
    </form>
  );
}

function NewUser({ onCreated }: { onCreated: () => void }) {
  const blank = { username: "", full_name: "", email: "", role: "lecturer" as Role, password: "", student_code: "" };
  const [form, setForm] = useState(blank);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof blank) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setDone(null);
    try {
      const user = await api<User>("/api/users", {
        method: "POST",
        json: { ...form, email: form.email || null, student_code: form.role === "student" ? form.student_code : null },
      });
      setDone(`Account ${user.username} created.`);
      setForm(blank);
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Create an account">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Username"><Input value={form.username} onChange={set("username")} required minLength={3} /></Field>
        <Field label="Full name"><Input value={form.full_name} onChange={set("full_name")} required /></Field>
        <Field label="Email (optional)"><Input type="email" value={form.email} onChange={set("email")} /></Field>
        <Field label="Role"><Select value={form.role} onChange={set("role")}>{ROLES.map((r) => <option key={r} value={r} className="capitalize">{r}</option>)}</Select></Field>
        {form.role === "student" && <Field label="Student code"><Input value={form.student_code} onChange={set("student_code")} required /></Field>}
        <Field label="Temporary password" hint="At least 8 characters"><Input type="password" value={form.password} onChange={set("password")} required minLength={8} /></Field>
        <div className="flex items-end"><Button type="submit" busy={busy}>Create account</Button></div>
      </form>
      <div className="mt-3">{error && <ErrorNote message={error} />}{done && <SuccessNote>{done}</SuccessNote>}</div>
    </Card>
  );
}
