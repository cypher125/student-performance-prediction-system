"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";
import { CountBars, GpaHistoryChart, RiskByLevelChart } from "@/components/charts";
import { PredictionPanel } from "@/components/prediction";
import { isStaff, useUser } from "@/components/session";
import { Card, ErrorNote, Loading, PageHeader, RiskBadge, StatTile, StatusBadge } from "@/components/ui";
import { useApi } from "@/lib/api";
import { date, num, pct } from "@/lib/format";
import type { AcademicRecord, Alert, Prediction, Student } from "@/lib/types";

interface StaffDashboard {
  session: string;
  semester: string;
  students_assessed: number;
  risk_counts: { High: number; Medium: number; Low: number };
  predicted_class_counts: Record<string, number>;
  risk_by_level: { level: string; High: number; Medium: number; Low: number }[];
  top_risk_factors: { factor: string; students: number }[];
  alert_counts: Record<string, number>;
  averages: { attendance_pct: number | null; ca_score: number | null; assignment_score: number | null };
  recent_alerts: Alert[];
  model: { version: string; accuracy: number; f1_macro: number; fail_recall: number; trained_on: string };
}

interface StudentDashboard {
  student: Student;
  latest_prediction: Prediction | null;
  current_record: AcademicRecord | null;
  history: AcademicRecord[];
  alerts: Alert[];
}

export default function DashboardPage() {
  const user = useUser();
  return isStaff(user) ? <StaffView /> : <StudentView />;
}

function StaffView() {
  const { data, error, loading } = useApi<StaffDashboard>("/api/dashboard");
  if (loading && !data) return <Loading />;
  if (error) return <ErrorNote message={error.message} />;
  if (!data) return null;
  const atRisk = data.risk_counts.High + data.risk_counts.Medium;

  return (
    <>
      <PageHeader title="Early-warning dashboard"
        subtitle={`${data.semester} semester, ${data.session} · ${data.students_assessed} students assessed before examinations`} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="High risk" value={data.risk_counts.High} tone="High" note="Fail predicted, or probability of Fail ≥ 50%" />
        <StatTile label="Medium risk" value={data.risk_counts.Medium} tone="Medium" note="Probability of Fail 25–49%" />
        <StatTile label="Low risk" value={data.risk_counts.Low} tone="Low" note="Probability of Fail below 25%" />
        <StatTile label="Alerts awaiting action" value={data.alert_counts.New ?? 0}
          note={`${data.alert_counts.Acknowledged ?? 0} acknowledged · ${data.alert_counts.Resolved ?? 0} resolved`} />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Card title="Risk by level" subtitle={`${atRisk} of ${data.students_assessed} students (${pct(atRisk / Math.max(1, data.students_assessed))}) need attention`}>
          <RiskByLevelChart data={data.risk_by_level} />
        </Card>
        <Card title="Predicted performance classes" subtitle="What the model expects at the end of the semester">
          <CountBars data={Object.entries(data.predicted_class_counts).map(([label, value]) => ({ label, value }))} />
        </Card>
        <Card title="Main reason students are at risk" subtitle="The factor that raised each at-risk student's probability of Fail the most">
          {data.top_risk_factors.length ? (
            <CountBars horizontal height={60 + 44 * data.top_risk_factors.length}
              data={data.top_risk_factors.map((f) => ({ label: f.factor, value: f.students }))} />
          ) : <p className="text-sm text-muted">No students at risk.</p>}
        </Card>
        <Card title="This semester so far" subtitle="Averages across the students assessed">
          <dl className="grid grid-cols-3 gap-3 text-center">
            {[["Attendance", data.averages.attendance_pct], ["CA score", data.averages.ca_score], ["Assignments", data.averages.assignment_score]].map(([label, v]) => (
              <div key={label as string} className="rounded-lg bg-page p-3">
                <dt className="text-xs text-ink-2">{label}</dt>
                <dd className="mt-1 text-2xl font-semibold">{num(v as number | null, 1)}%</dd>
              </div>
            ))}
          </dl>
          <div className="mt-4 rounded-lg border border-line p-3 text-sm text-ink-2">
            Model {data.model.version} (trained {data.model.trained_on}): test accuracy <strong>{pct(data.model.accuracy)}</strong>,
            macro F1 <strong>{num(data.model.f1_macro, 2)}</strong>, catches <strong>{pct(data.model.fail_recall)}</strong> of failing students.{" "}
            <Link href="/model/" className="text-brand-dark underline">Details</Link>
          </div>
        </Card>
      </div>

      <Card title="Latest alerts" className="mt-5" actions={<Link href="/alerts/" className="text-sm text-brand-dark underline">All alerts</Link>}>
        <ul className="divide-y divide-line">
          {data.recent_alerts.map((a) => (
            <li key={a.id} className="flex flex-wrap items-center gap-3 py-3 text-sm">
              <RiskBadge risk={a.risk_level} />
              <Link href={`/students/view/?code=${a.student.code}`} className="font-medium hover:underline">{a.student.full_name}</Link>
              <span className="text-ink-2">{a.student.level} · probability of Fail {pct(a.fail_probability)}</span>
              <span className="ml-auto flex items-center gap-3 text-xs text-muted">{date(a.sent_at)} <StatusBadge status={a.status} /></span>
            </li>
          ))}
          {data.recent_alerts.length === 0 && <li className="py-3 text-sm text-muted">No alerts yet.</li>}
        </ul>
      </Card>
    </>
  );
}

function StudentView() {
  const { data, error, loading } = useApi<StudentDashboard>("/api/dashboard");
  if (loading && !data) return <Loading />;
  if (error) return <ErrorNote message={error.message} />;
  if (!data) return null;
  const openAlert = data.alerts.find((a) => a.status !== "Resolved");

  return (
    <>
      <PageHeader title={`Welcome, ${data.student.first_name}`}
        subtitle={`${data.student.code} · ${data.student.matric_number} · ${data.student.level}, ${data.student.session}`} />

      {openAlert && (
        <div className="mb-5 flex gap-3 rounded-xl border border-critical/30 bg-critical/5 p-4 text-sm">
          <AlertTriangle className="shrink-0 text-critical" size={20} aria-hidden />
          <div>
            <p className="font-medium">You have been flagged for early support ({openAlert.risk_level.toLowerCase()} risk).</p>
            <p className="mt-0.5 text-ink-2">Your academic adviser has been notified. Follow the recommendations below and expect a check-in.</p>
          </div>
        </div>
      )}

      {data.latest_prediction ? <PredictionPanel prediction={data.latest_prediction} audience="student" />
        : <Card title="No prediction yet"><p className="text-sm text-ink-2">Your current semester has not been assessed yet.</p></Card>}

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        {data.current_record && (
          <Card title="Your current record" subtitle={`${data.current_record.semester} semester, ${data.current_record.session}`}>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              {[["Attendance", `${num(data.current_record.attendance_pct)}%`], ["CA score", `${num(data.current_record.ca_score)}%`],
                ["Assignments", `${num(data.current_record.assignment_score)}%`], ["Previous GPA", num(data.current_record.prior_gpa, 2)]].map(([k, v]) => (
                <div key={k} className="rounded-lg bg-page p-3"><dt className="text-xs text-ink-2">{k}</dt><dd className="mt-1 text-xl font-semibold">{v}</dd></div>
              ))}
            </dl>
          </Card>
        )}
        <Card title="Your results so far" subtitle="Semester GPA">
          <GpaHistoryChart records={data.history} />
        </Card>
      </div>
    </>
  );
}
