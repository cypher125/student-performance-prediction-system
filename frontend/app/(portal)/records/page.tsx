"use client";

import { Download, FileUp, Play } from "lucide-react";
import { useRef, useState } from "react";
import { PredictionPanel } from "@/components/prediction";
import { Button, Card, ErrorNote, Field, Input, PageHeader, Select, SuccessNote, Table, Td } from "@/components/ui";
import { api, API_BASE, ApiError } from "@/lib/api";
import type { Prediction } from "@/lib/types";
import { LEVELS } from "@/lib/types";

interface ImportResult {
  rows_received: number;
  rows_accepted: number;
  rows_rejected: number;
  records_created: number;
  records_updated: number;
  predictions_made: number;
  alerts_raised: number;
  errors: { row: number; field: string; message: string }[];
}

export default function RecordsPage() {
  return (
    <>
      <PageHeader title="Records & upload"
        subtitle="Add this semester's attendance, CA and assignment scores. Records without results are scored straight away."
        actions={<RunPredictions />} />
      <div className="grid gap-5">
        <UploadCard />
        <ManualEntry />
      </div>
    </>
  );
}

function UploadCard() {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function upload() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    const body = new FormData();
    body.append("file", file);
    try {
      setResult(await api<ImportResult>("/api/records/upload", { method: "POST", body }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Upload a CSV file" subtitle="One row per student: student_code, level, session, semester, attendance_pct, ca_score, assignment_score, prior_gpa"
      actions={<a href={`${API_BASE}/api/records/template`} className="inline-flex items-center gap-1.5 text-sm text-brand-dark hover:underline"><Download size={15} aria-hidden /> Template</a>}>
      <div className="flex flex-wrap items-center gap-3">
        <input ref={input} type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setResult(null); }} />
        <Button variant="secondary" onClick={() => input.current?.click()}><FileUp size={16} aria-hidden /> Choose file</Button>
        <span className="text-sm text-ink-2">{file ? file.name : "No file chosen"}</span>
        <Button onClick={upload} disabled={!file} busy={busy} className="ml-auto">Upload and predict</Button>
      </div>
      <p className="mt-2 text-xs text-muted">Labels such as “nd 1”, “1st” or “2025/26” are understood. Leave a cell blank if a value is not available.</p>

      <div className="mt-4 space-y-3">
        {error && <ErrorNote message={error} />}
        {result && (
          <>
            <SuccessNote>
              {result.rows_accepted} of {result.rows_received} rows saved ({result.records_created} new, {result.records_updated} updated).{" "}
              {result.predictions_made} predictions made and {result.alerts_raised} alerts raised.
            </SuccessNote>
            {result.errors.length > 0 && (
              <>
                <p className="text-sm font-medium text-critical">{result.rows_rejected} rows were not saved. Fix them and upload again:</p>
                <Table head={["Row", "Field", "Problem"]}>
                  {result.errors.map((e) => <tr key={`${e.row}-${e.field}`}><Td>{e.row}</Td><Td className="font-mono text-xs">{e.field}</Td><Td wrap>{e.message}</Td></tr>)}
                </Table>
              </>
            )}
          </>
        )}
      </div>
    </Card>
  );
}

const EMPTY = { student_code: "", level: "ND1", session: "2025/2026", semester: "First", attendance_pct: "", ca_score: "", assignment_score: "", prior_gpa: "" };

function ManualEntry() {
  const [form, setForm] = useState(EMPTY);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [error, setError] = useState<{ message: string; field?: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm({ ...form, [k]: e.target.value });
  const numberOrNull = (v: string) => (v.trim() === "" ? null : Number(v));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setPrediction(null);
    try {
      const result = await api<{ prediction: Prediction | null }>("/api/records", {
        method: "POST",
        json: { ...form, attendance_pct: numberOrNull(form.attendance_pct), ca_score: numberOrNull(form.ca_score),
          assignment_score: numberOrNull(form.assignment_score), prior_gpa: numberOrNull(form.prior_gpa) },
      });
      setPrediction(result.prediction);
    } catch (err) {
      setError(err instanceof ApiError ? { message: err.message, field: err.field } : { message: "Could not save the record." });
    } finally {
      setBusy(false);
    }
  }

  const fieldError = (name: string) => (error?.field === name ? error.message : undefined);

  return (
    <Card title="Enter one record" subtitle="For a single student; the prediction and its explanation appear below">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Student code" hint="e.g. S0379" error={fieldError("student_code")}><Input value={form.student_code} onChange={set("student_code")} required /></Field>
        <Field label="Level" error={fieldError("level")}><Select value={form.level} onChange={set("level")}>{LEVELS.map((l) => <option key={l}>{l}</option>)}</Select></Field>
        <Field label="Session" error={fieldError("session")}><Input value={form.session} onChange={set("session")} required /></Field>
        <Field label="Semester" error={fieldError("semester")}><Select value={form.semester} onChange={set("semester")}><option>First</option><option>Second</option></Select></Field>
        <Field label="Attendance (%)" error={fieldError("attendance_pct")}><Input type="number" min={0} max={100} step="0.1" value={form.attendance_pct} onChange={set("attendance_pct")} /></Field>
        <Field label="CA score (%)" error={fieldError("ca_score")}><Input type="number" min={0} max={100} step="0.1" value={form.ca_score} onChange={set("ca_score")} /></Field>
        <Field label="Assignment score (%)" error={fieldError("assignment_score")}><Input type="number" min={0} max={100} step="0.1" value={form.assignment_score} onChange={set("assignment_score")} /></Field>
        <Field label="Previous GPA" hint="Leave blank to use the last result" error={fieldError("prior_gpa")}><Input type="number" min={0} max={4} step="0.01" value={form.prior_gpa} onChange={set("prior_gpa")} /></Field>
        <div className="sm:col-span-2 lg:col-span-4 flex justify-end"><Button type="submit" busy={busy}>Save and predict</Button></div>
      </form>
      {error && !error.field && <div className="mt-3"><ErrorNote message={error.message} /></div>}
      {prediction && <div className="mt-5"><PredictionPanel prediction={prediction} audience="staff" /></div>}
    </Card>
  );
}

function RunPredictions() {
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function run() {
    setBusy(true);
    try {
      const r = await api<{ predictions_made: number; alerts_raised: number; records_checked: number; model_version: string }>("/api/predictions/run", { method: "POST" });
      setMessage(r.predictions_made ? `${r.predictions_made} records scored with model ${r.model_version}; ${r.alerts_raised} alerts raised.`
        : `All ${r.records_checked} current records are already scored by model ${r.model_version}.`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Could not run predictions.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="flex flex-col items-end gap-1">
      <Button variant="secondary" onClick={run} busy={busy}><Play size={16} aria-hidden /> Score current semester</Button>
      {message && <span className="max-w-xs text-right text-xs text-ink-2">{message}</span>}
    </div>
  );
}
