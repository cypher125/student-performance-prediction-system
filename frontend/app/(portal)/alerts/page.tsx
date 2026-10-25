"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, Card, ErrorNote, Loading, PageHeader, RiskBadge, Select, StatusBadge } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import { date, pct } from "@/lib/format";
import type { Alert } from "@/lib/types";

export default function AlertsPage() {
  const [status, setStatus] = useState("New");
  const [risk, setRisk] = useState("");
  const params = new URLSearchParams();
  if (status) params.set("alert_status", status);
  if (risk) params.set("risk", risk);
  const { data, error, loading, reload } = useApi<{ count: number; alerts: Alert[] }>(`/api/alerts?${params}`);

  return (
    <>
      <PageHeader title="Early-warning alerts"
        subtitle="Raised automatically for High and Medium risk students. Record what was done: this is the intervention log." />
      <div className="mb-4 flex flex-wrap gap-3">
        <div className="w-48">
          <Select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status">
            <option value="New">New</option><option value="Acknowledged">Acknowledged</option><option value="Resolved">Resolved</option><option value="">All statuses</option>
          </Select>
        </div>
        <div className="w-48">
          <Select value={risk} onChange={(e) => setRisk(e.target.value)} aria-label="Risk">
            <option value="">All risk levels</option><option value="High">High risk</option><option value="Medium">Medium risk</option>
          </Select>
        </div>
        {data && <span className="self-center text-sm text-ink-2">{data.count} alerts</span>}
      </div>
      {error && <ErrorNote message={error.message} />}
      {loading && !data ? <Loading /> : (
        <div className="grid gap-3">
          {data?.alerts.map((a) => <AlertCard key={a.id} alert={a} onChanged={reload} />)}
          {data?.alerts.length === 0 && <Card><p className="text-sm text-ink-2">No alerts match these filters.</p></Card>}
        </div>
      )}
    </>
  );
}

function AlertCard({ alert, onChanged }: { alert: Alert; onChanged: () => void }) {
  const [open, setOpen] = useState(false);
  const [action, setAction] = useState(alert.action_taken ?? "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function update(status: Alert["status"]) {
    setBusy(true);
    setError(null);
    try {
      await api(`/api/alerts/${alert.id}`, { method: "PATCH", json: { status, action_taken: action } });
      setOpen(false);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update the alert.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="flex flex-wrap items-center gap-3">
        <RiskBadge risk={alert.risk_level} />
        <Link href={`/students/view/?code=${alert.student.code}`} className="font-medium text-brand-dark hover:underline">{alert.student.full_name}</Link>
        <span className="text-sm text-ink-2">{alert.student.code} · {alert.student.level} · probability of Fail {pct(alert.fail_probability)}</span>
        <span className="ml-auto flex items-center gap-3 text-xs text-muted">{date(alert.sent_at)} <StatusBadge status={alert.status} /></span>
      </div>
      <p className="mt-2 text-sm text-ink-2">{alert.message}</p>
      {alert.action_taken && !open && (
        <p className="mt-2 rounded-lg bg-page p-2 text-sm"><strong>Intervention:</strong> {alert.action_taken}
          {alert.acknowledged_by && <span className="text-ink-2"> · {alert.acknowledged_by}, {date(alert.acknowledged_at)}</span>}</p>
      )}
      {alert.status !== "Resolved" && !open && (
        <div className="mt-3 flex gap-2">
          <Button variant="secondary" onClick={() => setOpen(true)}>Record intervention</Button>
          {alert.status === "New" && <Button variant="ghost" busy={busy} onClick={() => update("Acknowledged")}>Acknowledge</Button>}
        </div>
      )}
      {open && (
        <div className="mt-3 space-y-2">
          <textarea value={action} onChange={(e) => setAction(e.target.value)} rows={3} maxLength={2000}
            placeholder="What was done? e.g. Met the student on 23 Oct; agreed a weekly study plan; referred to the CA tutorial."
            className="w-full rounded-lg border border-line p-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" aria-label="Intervention taken" />
          {error && <ErrorNote message={error} />}
          <div className="flex flex-wrap gap-2">
            <Button busy={busy} onClick={() => update("Resolved")} disabled={!action.trim()}>Save and resolve</Button>
            <Button variant="secondary" busy={busy} onClick={() => update("Acknowledged")}>Save, keep open</Button>
            <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
          </div>
        </div>
      )}
    </div>
  );
}
