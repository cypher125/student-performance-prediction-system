"use client";

import { Lightbulb, UserCheck } from "lucide-react";
import { ExplanationChart, ProbabilityBars } from "@/components/charts";
import { Card, ClassBadge, RiskBadge } from "@/components/ui";
import { date, pct } from "@/lib/format";
import type { Prediction } from "@/lib/types";

export function PredictionPanel({ prediction, audience }: { prediction: Prediction; audience: "student" | "staff" }) {
  const explanation = prediction.explanation ?? [];
  const advice = (prediction.recommendations ?? []).filter((r) => audience === "staff" || r.audience === "student");
  const helping = explanation.filter((e) => e.contribution < 0).map((e) => e.label);

  return (
    <div className="grid gap-5 lg:grid-cols-5">
      <Card title="Prediction" subtitle={`Model ${prediction.model_version} · ${date(prediction.created_at)}`} className="lg:col-span-2">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted">Predicted class</p>
            <p className="mt-0.5 text-3xl font-semibold">{prediction.predicted_class}</p>
          </div>
          <div className="ml-auto text-right">
            <RiskBadge risk={prediction.risk_level} />
            <p className="mt-1 text-sm text-ink-2">Probability of Fail: <strong>{pct(prediction.fail_probability)}</strong></p>
          </div>
        </div>
        {prediction.probabilities && (
          <div className="mt-4">
            <p className="mb-1 text-xs uppercase tracking-wide text-muted">Probability of each class</p>
            <ProbabilityBars probabilities={prediction.probabilities} predicted={prediction.predicted_class} />
          </div>
        )}
      </Card>

      <Card title="Why this prediction?" subtitle="SHAP explanation: how each factor moved the probability of Fail" className="lg:col-span-3">
        <ExplanationChart items={explanation} />
        {helping.length > 0 && (
          <p className="mt-3 text-sm text-ink-2">Working in {audience === "student" ? "your" : "the student's"} favour: {helping.join(", ")}.</p>
        )}
      </Card>

      <Card title="Recommendations" className="lg:col-span-5">
        <ul className="grid gap-3 md:grid-cols-2">
          {advice.map((r, i) => (
            <li key={i} className={`flex gap-3 rounded-lg border p-3 text-sm ${r.audience === "staff" ? "border-brand/30 bg-brand-soft" : "border-line bg-page"}`}>
              {r.audience === "staff" ? <UserCheck size={18} className="mt-0.5 shrink-0 text-brand-dark" aria-hidden />
                : <Lightbulb size={18} className="mt-0.5 shrink-0 text-warn-text" aria-hidden />}
              <div>
                <p className="font-medium">{r.audience === "staff" ? "For the adviser" : r.factor}</p>
                <p className="mt-0.5 text-ink-2">{r.text}</p>
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

export function PredictionSummary({ prediction }: { prediction: Prediction }) {
  return (
    <span className="inline-flex items-center gap-2">
      <ClassBadge value={prediction.predicted_class} /> <RiskBadge risk={prediction.risk_level} />
    </span>
  );
}
