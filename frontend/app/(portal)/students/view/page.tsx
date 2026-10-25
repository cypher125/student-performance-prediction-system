"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { GpaHistoryChart } from "@/components/charts";
import { PredictionPanel } from "@/components/prediction";
import { isStaff, useUser } from "@/components/session";
import { Card, ClassBadge, ErrorNote, Loading, PageHeader, RiskBadge, StatusBadge, Table, Td } from "@/components/ui";
import { useApi } from "@/lib/api";
import { date, gpa, num, pct } from "@/lib/format";
import type { AcademicRecord, Alert, Prediction, Student } from "@/lib/types";

interface Detail {
  student: Student;
  records: AcademicRecord[];
  predictions: Prediction[];
  alerts: Alert[];
}

export default function StudentViewPage() {
  return (
    <Suspense fallback={<Loading />}>
      <StudentView />
    </Suspense>
  );
}

function StudentView() {
  const code = useSearchParams().get("code");
  const user = useUser();
  const { data, error, loading } = useApi<Detail>(code ? `/api/students/${encodeURIComponent(code)}` : null);

  if (!code) return <ErrorNote message="No student selected." />;
  if (loading && !data) return <Loading />;
  if (error) return <ErrorNote message={error.message} />;
  if (!data) return null;
  const { student, records, predictions, alerts } = data;
  const latest = predictions[0];

  return (
    <>
      {isStaff(user) && (
        <Link href="/students/" className="no-print mb-3 inline-flex items-center gap-1 text-sm text-brand-dark hover:underline">
          <ArrowLeft size={15} aria-hidden /> All students
        </Link>
      )}
      <PageHeader title={student.full_name}
        subtitle={`${student.code} · ${student.matric_number} · ${student.level} · ${student.department} · entered ${student.entry_session}`} />

      {latest ? <PredictionPanel prediction={latest} audience="staff" />
        : <Card title="No prediction"><p className="text-sm text-ink-2">This student has no current-semester record yet.</p></Card>}

      <div className="mt-5 grid gap-5 lg:grid-cols-5">
        <Card title="GPA trend" className="lg:col-span-2"><GpaHistoryChart records={records} /></Card>
        <Card title="Semester records" className="lg:col-span-3">
          <Table head={["Session", "Level", "Attendance", "CA", "Assign.", "Exam", "GPA", "Class"]}>
            {[...records].reverse().map((r) => (
              <tr key={r.id}>
                <Td>{r.session} {r.semester === "First" ? "1st" : "2nd"}</Td>
                <Td>{r.level}</Td>
                <Td>{num(r.attendance_pct)}%</Td>
                <Td>{num(r.ca_score)}%</Td>
                <Td>{num(r.assignment_score)}%</Td>
                <Td>{r.exam_score == null ? <span className="text-muted">pending</span> : `${num(r.exam_score)}%`}</Td>
                <Td>{r.gpa == null ? <span className="text-muted">pending</span> : gpa(r.gpa)}</Td>
                <Td><ClassBadge value={r.performance_class} /></Td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>

      {alerts.length > 0 && (
        <Card title="Alerts and interventions" className="mt-5">
          <ul className="divide-y divide-line">
            {alerts.map((a) => (
              <li key={a.id} className="py-3 text-sm">
                <div className="flex flex-wrap items-center gap-3">
                  <RiskBadge risk={a.risk_level} /> <StatusBadge status={a.status} />
                  <span className="text-ink-2">Raised {date(a.sent_at)} · probability of Fail {pct(a.fail_probability)}</span>
                </div>
                {a.action_taken && <p className="mt-2 text-ink-2"><strong>Intervention:</strong> {a.action_taken} {a.acknowledged_by && `(${a.acknowledged_by})`}</p>}
              </li>
            ))}
          </ul>
          {isStaff(user) && <Link href="/alerts/" className="mt-2 inline-block text-sm text-brand-dark underline">Manage alerts</Link>}
        </Card>
      )}

      {predictions.length > 1 && (
        <Card title="Prediction history" className="mt-5">
          <Table head={["Date", "Predicted", "P(Fail)", "Risk", "Model"]}>
            {predictions.map((p) => (
              <tr key={p.id}><Td>{date(p.created_at)}</Td><Td><ClassBadge value={p.predicted_class} /></Td><Td>{pct(p.fail_probability)}</Td><Td><RiskBadge risk={p.risk_level} /></Td><Td>{p.model_version}</Td></tr>
            ))}
          </Table>
        </Card>
      )}
    </>
  );
}
