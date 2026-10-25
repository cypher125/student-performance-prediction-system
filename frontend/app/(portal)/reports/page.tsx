"use client";

import { Download, Printer } from "lucide-react";
import { Button, Card, ErrorNote, Loading, PageHeader, StatTile, Table, Td } from "@/components/ui";
import { API_BASE, useApi } from "@/lib/api";
import { CLASSES } from "@/lib/types";

interface Summary {
  session: string;
  semester: string;
  students_assessed: number;
  by_level: { level: string; students: number; High: number; Medium: number; Low: number; at_risk_pct: number }[];
  predicted_classes: Record<string, number>;
  alerts: Record<string, number>;
  interventions_recorded: number;
}

export default function ReportsPage() {
  const { data, error, loading } = useApi<Summary>("/api/reports/summary");
  if (loading && !data) return <Loading />;
  if (error) return <ErrorNote message={error.message} />;
  if (!data) return null;
  const total = data.by_level.reduce((acc, r) => ({ High: acc.High + r.High, Medium: acc.Medium + r.Medium, Low: acc.Low + r.Low }), { High: 0, Medium: 0, Low: 0 });

  return (
    <>
      <PageHeader title="Summary report" subtitle={`${data.semester} semester, ${data.session} · generated ${new Date().toLocaleDateString("en-GB")}`}
        actions={<>
          <a href={`${API_BASE}/api/reports/predictions.csv`}
            className="inline-flex items-center gap-2 rounded-lg border border-line bg-surface px-3.5 py-2 text-sm font-medium hover:bg-page">
            <Download size={16} aria-hidden /> Export predictions (CSV)
          </a>
          <Button onClick={() => window.print()}><Printer size={16} aria-hidden /> Print</Button>
        </>} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Students assessed" value={data.students_assessed} />
        <StatTile label="At risk (High + Medium)" value={total.High + total.Medium} tone="High"
          note={`${Math.round((100 * (total.High + total.Medium)) / Math.max(1, data.students_assessed))}% of students`} />
        <StatTile label="Alerts still open" value={(data.alerts.New ?? 0) + (data.alerts.Acknowledged ?? 0)} tone="Medium" />
        <StatTile label="Interventions recorded" value={data.interventions_recorded} tone="Low" />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Card title="Risk by level" className="lg:col-span-2">
          <Table head={["Level", "Students", "High", "Medium", "Low", "At risk"]}>
            {data.by_level.map((r) => (
              <tr key={r.level}><Td className="font-medium">{r.level}</Td><Td>{r.students}</Td><Td>{r.High}</Td><Td>{r.Medium}</Td><Td>{r.Low}</Td><Td>{r.at_risk_pct}%</Td></tr>
            ))}
            <tr className="bg-page font-medium"><Td>Total</Td><Td>{data.students_assessed}</Td><Td>{total.High}</Td><Td>{total.Medium}</Td><Td>{total.Low}</Td>
              <Td>{Math.round((1000 * (total.High + total.Medium)) / Math.max(1, data.students_assessed)) / 10}%</Td></tr>
          </Table>
        </Card>
        <Card title="Predicted classes">
          <Table head={["Class", "Students"]}>
            {CLASSES.map((c) => <tr key={c}><Td>{c}</Td><Td>{data.predicted_classes[c] ?? 0}</Td></tr>)}
          </Table>
        </Card>
        <Card title="Alerts by status" className="lg:col-span-3">
          <Table head={["New", "Acknowledged", "Resolved", "Interventions recorded"]}>
            <tr><Td>{data.alerts.New ?? 0}</Td><Td>{data.alerts.Acknowledged ?? 0}</Td><Td>{data.alerts.Resolved ?? 0}</Td><Td>{data.interventions_recorded}</Td></tr>
          </Table>
        </Card>
      </div>
    </>
  );
}
