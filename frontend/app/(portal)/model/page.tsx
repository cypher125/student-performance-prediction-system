"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { COLORS } from "@/components/charts";
import { useUser } from "@/components/session";
import { Button, Card, ErrorNote, Loading, PageHeader, StatTile, SuccessNote, Table, Td } from "@/components/ui";
import { api, useApi } from "@/lib/api";
import { num, pct } from "@/lib/format";

interface ModelInfo {
  version: string;
  algorithm: string;
  trained_on: string;
  dataset: { file: string; records: number; kind: string };
  features: string[];
  feature_labels: Record<string, string>;
  settings: Record<string, string | number | null>;
  test_metrics: Record<string, number>;
  evaluation_note: string;
  risk_rule: { high_if_fail_probability_at_least: number; medium_if_fail_probability_at_least: number };
  feature_importance: { feature: string; impurity: number; permutation_mean?: number; shap_fail?: number }[];
  records_available_for_retraining: number;
  retrain: RetrainState;
}

interface RetrainState { status: "idle" | "running" | "done" | "failed"; message: string; version: string | null }

const METRIC_LABELS: [string, string][] = [
  ["accuracy", "Accuracy"], ["precision_macro", "Precision (macro)"], ["recall_macro", "Recall (macro)"],
  ["f1_macro", "F1-score (macro)"], ["f1_weighted", "F1-score (weighted)"], ["roc_auc_ovr_macro", "ROC-AUC (one-vs-rest)"],
  ["fail_precision", "Fail: precision"], ["fail_recall", "Fail: recall"], ["fail_roc_auc", "Fail: ROC-AUC"],
];

export default function ModelPage() {
  const user = useUser();
  const { data, error, loading, reload } = useApi<ModelInfo>("/api/model");
  if (loading && !data) return <Loading />;
  if (error) return <ErrorNote message={error.message} />;
  if (!data) return null;

  const m = data.test_metrics;
  const importance = data.feature_importance.map((f) => ({
    label: data.feature_labels[f.feature] ?? f.feature, impurity: f.impurity, shap: f.shap_fail ?? null,
  }));
  const hasShap = importance.every((i) => i.shap != null);

  return (
    <>
      <PageHeader title="Prediction model" subtitle={`${data.algorithm} · version ${data.version} · trained ${data.trained_on} on ${data.dataset.records.toLocaleString()} ${data.dataset.kind} records`}
        actions={user.role === "admin" ? <Retrain initial={data.retrain} available={data.records_available_for_retraining} onDone={reload} /> : undefined} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Accuracy" value={pct(m.accuracy)} note="Share of test students placed in the right class" />
        <StatTile label="Macro F1-score" value={num(m.f1_macro, 2)} note="Balances all four classes" />
        <StatTile label="ROC-AUC" value={num(m.roc_auc_ovr_macro, 2)} note="1.0 = perfect ranking, 0.5 = chance" />
        <StatTile label="Failing students caught" value={pct(m.fail_recall)} note="Recall of the Fail class" />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Card title="Which factors matter most?" subtitle="Random Forest impurity importance and mean |SHAP| for the Fail class">
          <ResponsiveContainer width="100%" height={70 + 52 * importance.length}>
            <BarChart data={importance} layout="vertical" margin={{ top: 4, right: 44, left: 4, bottom: 4 }}>
              <CartesianGrid horizontal={false} stroke={COLORS.grid} />
              <XAxis type="number" stroke={COLORS.grid} tick={{ fill: COLORS.ink2, fontSize: 12 }} tickLine={false} />
              <YAxis type="category" dataKey="label" width={150} stroke={COLORS.grid} tick={{ fill: COLORS.ink2, fontSize: 12 }} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 4, fontSize: 12 }} formatter={(v) => Number(v).toFixed(3)} />
              <Legend iconType="square" wrapperStyle={{ fontSize: 12 }} itemSorter={null}
                formatter={(value: string) => <span style={{ color: COLORS.ink2 }}>{value}</span>} />
              <Bar isAnimationActive={false} dataKey="impurity" name="Impurity importance" fill={COLORS.series} maxBarSize={18} radius={[0, 2, 2, 0]}>
                <LabelList dataKey="impurity" position="right" fontSize={11} fill={COLORS.ink2} formatter={(v: unknown) => Number(v).toFixed(2)} />
              </Bar>
              {hasShap && (
                <Bar isAnimationActive={false} dataKey="shap" name="Mean |SHAP| (Fail)" fill="#9aa5b4" maxBarSize={18} radius={[0, 2, 2, 0]}>
                  <LabelList dataKey="shap" position="right" fontSize={11} fill={COLORS.ink2} formatter={(v: unknown) => Number(v).toFixed(2)} />
                </Bar>
              )}
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="All test-set measures" subtitle={data.evaluation_note}>
          <Table head={["Measure", "Value"]}>
            {METRIC_LABELS.filter(([k]) => k in m).map(([k, label]) => <tr key={k}><Td>{label}</Td><Td className="font-medium">{num(m[k], 3)}</Td></tr>)}
          </Table>
        </Card>

        <Card title="How a prediction becomes an alert">
          <ul className="space-y-2 text-sm text-ink-2">
            <li><strong className="text-critical">High risk</strong>: Fail is the predicted class, or the probability of Fail is at least {pct(data.risk_rule.high_if_fail_probability_at_least)}.</li>
            <li><strong className="text-warn-text">Medium risk</strong>: probability of Fail at least {pct(data.risk_rule.medium_if_fail_probability_at_least)}.</li>
            <li><strong className="text-good-text">Low risk</strong>: otherwise. High and Medium risk students get an alert for their adviser.</li>
            <li>The examination score is never used: predictions are made before examinations, from attendance, CA, assignments, previous GPA and level.</li>
          </ul>
        </Card>

        <Card title="Model settings" subtitle="Chosen by 5-fold cross-validated grid search on the training data">
          <Table head={["Setting", "Value"]}>
            {Object.entries(data.settings).map(([k, v]) => <tr key={k}><Td className="font-mono text-xs">{k}</Td><Td>{v === null ? "None" : String(v)}</Td></tr>)}
            <tr><Td className="font-mono text-xs">features</Td><Td wrap>{data.features.map((f) => data.feature_labels[f] ?? f).join(", ")}</Td></tr>
          </Table>
        </Card>
      </div>
    </>
  );
}

function Retrain({ initial, available, onDone }: { initial: RetrainState; available: number; onDone: () => void }) {
  const [state, setState] = useState<RetrainState>(initial);

  useEffect(() => {
    if (state.status !== "running") return;
    const timer = setInterval(async () => {
      const next = await api<RetrainState>("/api/model/retrain");
      setState(next);
      if (next.status !== "running") onDone();
    }, 3000);
    return () => clearInterval(timer);
  }, [state.status, onDone]);

  return (
    <div className="flex max-w-sm flex-col items-end gap-2">
      <Button onClick={async () => setState(await api<RetrainState>("/api/model/retrain", { method: "POST" }))} busy={state.status === "running"}>
        Retrain on {available.toLocaleString()} records
      </Button>
      {state.status === "done" && <SuccessNote>{state.message}</SuccessNote>}
      {state.status === "failed" && <ErrorNote message={state.message} />}
      {state.status === "running" && <span className="text-xs text-ink-2">{state.message}</span>}
    </div>
  );
}
