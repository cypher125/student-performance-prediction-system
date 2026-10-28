"use client";

import { Search } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Button, Card, ClassBadge, ErrorNote, Field, Input, Loading, PageHeader, RiskBadge, Select, StatusBadge, SuccessNote, Table, Td } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { gpa, num, pct } from "@/lib/format";
import type { AcademicRecord, Prediction, Student } from "@/lib/types";
import { LEVELS } from "@/lib/types";

interface Row extends Student {
  current_record: AcademicRecord | null;
  last_gpa: number | null;
  prediction: Prediction | null;
  alert_status: string | null;
}

export default function StudentsPage() {
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("");
  const [risk, setRisk] = useState("");
  const [scope, setScope] = useState("current");
  const [adding, setAdding] = useState(false);
  const query = useMemo(() => {
    const params = new URLSearchParams({ scope });
    if (level) params.set("level", level);
    if (risk) params.set("risk", risk);
    return `/api/students?${params}`;
  }, [scope, level, risk]);
  const { data, error, loading, reload } = useApi<{ count: number; students: Row[] }>(query);

  const term = search.trim().toLowerCase();
  const rows = (data?.students ?? []).filter((s) => !term || `${s.code} ${s.matric_number} ${s.full_name}`.toLowerCase().includes(term));

  return (
    <>
      <PageHeader title="Students" subtitle="Current-semester predictions, highest risk first"
        actions={<Button variant="secondary" onClick={() => setAdding((v) => !v)}>Register student</Button>} />

      {adding && <AddStudent onDone={() => { setAdding(false); reload(); }} />}

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="relative">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" aria-hidden />
          <Input placeholder="Search name, code or matric no." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" aria-label="Search students" />
        </div>
        <Select value={level} onChange={(e) => setLevel(e.target.value)} aria-label="Level">
          <option value="">All levels</option>
          {LEVELS.map((l) => <option key={l}>{l}</option>)}
        </Select>
        <Select value={risk} onChange={(e) => setRisk(e.target.value)} aria-label="Risk">
          <option value="">All risk levels</option>
          <option value="High">High risk</option><option value="Medium">Medium risk</option><option value="Low">Low risk</option>
        </Select>
        <Select value={scope} onChange={(e) => setScope(e.target.value)} aria-label="Scope">
          <option value="current">Current semester</option>
          <option value="all">All students (including past)</option>
        </Select>
      </div>

      {error && <ErrorNote message={error.message} />}
      {loading && !data ? <Loading /> : (
        <>
          <p className="mb-2 text-sm text-ink-2">{rows.length} students</p>
          <Table head={["Student", "Level", "Attendance", "CA", "Assignments", "Prev. GPA", "Predicted", "P(Fail)", "Risk", "Main factor", "Alert"]}>
            {rows.map((s) => (
              <tr key={s.code} className="hover:bg-page">
                <Td>
                  <Link href={`/students/view/?code=${s.code}`} className="font-medium text-brand-dark hover:underline">{s.full_name}</Link>
                  <span className="block text-xs text-muted">{s.code} · {s.matric_number}</span>
                </Td>
                <Td>{s.level}</Td>
                <Td>{s.current_record ? `${num(s.current_record.attendance_pct)}%` : "–"}</Td>
                <Td>{s.current_record ? `${num(s.current_record.ca_score)}%` : "–"}</Td>
                <Td>{s.current_record ? `${num(s.current_record.assignment_score)}%` : "–"}</Td>
                <Td>{gpa(s.current_record?.prior_gpa ?? s.last_gpa)}</Td>
                <Td><ClassBadge value={s.prediction?.predicted_class} /></Td>
                <Td>{pct(s.prediction?.fail_probability)}</Td>
                <Td><RiskBadge risk={s.prediction?.risk_level} /></Td>
                <Td className="text-ink-2">{s.prediction?.top_factor ?? "–"}</Td>
                <Td><StatusBadge status={s.alert_status} /></Td>
              </tr>
            ))}
          </Table>
        </>
      )}
    </>
  );
}

function AddStudent({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState({ first_name: "", last_name: "", matric_number: "", level: "ND1", session: "2025/2026" });
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const student = await api<Student>("/api/students", { method: "POST", json: form });
      setCreated(`${student.full_name} registered as ${student.code}. Add their semester record on the Records page.`);
      setTimeout(onDone, 1800);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not register the student.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Register a student" className="mb-5">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
        <Field label="First name"><Input value={form.first_name} onChange={set("first_name")} required /></Field>
        <Field label="Last name"><Input value={form.last_name} onChange={set("last_name")} required /></Field>
        <Field label="Matric number"><Input value={form.matric_number} onChange={set("matric_number")} required /></Field>
        <Field label="Level"><Select value={form.level} onChange={set("level")}>{LEVELS.map((l) => <option key={l}>{l}</option>)}</Select></Field>
        <Field label="Session"><Input value={form.session} onChange={set("session")} pattern="\d{4}/\d{4}" required /></Field>
        <div className="flex items-end"><Button type="submit" busy={busy} className="w-full">Register</Button></div>
      </form>
      <div className="mt-3">{error && <ErrorNote message={error} />}{created && <SuccessNote>{created}</SuccessNote>}</div>
    </Card>
  );
}
