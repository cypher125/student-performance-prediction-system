"use client";

import {
  Bar, BarChart, CartesianGrid, Cell, LabelList, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import { value as formatValue } from "@/lib/format";
import type { AcademicRecord, ExplanationItem, PerformanceClass } from "@/lib/types";
import { CLASSES } from "@/lib/types";

// Validated data-viz palette (same as the report figures).
export const COLORS = {
  series: "#2a78d6",
  toward: "#e34948",
  away: "#2a78d6",
  muted: "#c3c2b7",
  grid: "#e1e0d9",
  axis: "#898781",
  ink2: "#52514e",
  surface: "#ffffff",
  high: "#d03b3b",
  medium: "#fab219",
  low: "#0ca30c",
};

const axisProps = { stroke: COLORS.grid, tick: { fill: COLORS.ink2, fontSize: 12 }, tickLine: false };
const tooltipStyle = { borderRadius: 8, border: `1px solid ${COLORS.grid}`, fontSize: 12 };

/** Why the model predicted what it did: bars push the probability of Fail up (red) or down (blue). */
export function ExplanationChart({ items }: { items: ExplanationItem[] }) {
  const data = items.map((i) => ({ ...i, name: `${i.label}: ${formatValue(i.feature, i.value)}` }));
  const span = Math.max(0.05, ...items.map((i) => Math.abs(i.contribution))) * 1.25;
  return (
    <div>
      <ResponsiveContainer width="100%" height={46 * items.length + 40}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 48, top: 4, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke={COLORS.grid} />
          <XAxis type="number" domain={[-span, span]} {...axisProps} tickFormatter={(v: number) => v.toFixed(2)} />
          <YAxis type="category" dataKey="name" width={210} {...axisProps} />
          <ReferenceLine x={0} stroke={COLORS.axis} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f5f5f2" }}
            formatter={(v) => [Number(v).toFixed(3), "Effect on probability of Fail"]} />
          <Bar isAnimationActive={false} dataKey="contribution" maxBarSize={24} radius={3}>
            {data.map((d) => <Cell key={d.feature} fill={d.contribution > 0 ? COLORS.toward : COLORS.away} />)}
            <LabelList dataKey="contribution" position="right" fontSize={11} fill={COLORS.ink2}
              formatter={(v: unknown) => `${Number(v) > 0 ? "+" : ""}${Number(v).toFixed(3)}`} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-1 text-xs text-muted">
        <span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm align-middle" style={{ background: COLORS.toward }} /> raises the risk of failing
        <span className="ml-4 mr-1 inline-block h-2.5 w-2.5 rounded-sm align-middle" style={{ background: COLORS.away }} /> lowers it
      </p>
    </div>
  );
}

/** One series of counts: a single colour, value at the bar tip. */
export function CountBars({ data, horizontal = false, height = 240 }: {
  data: { label: string; value: number }[]; horizontal?: boolean; height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"} margin={{ top: 18, right: 36, left: 4, bottom: 4 }}>
        <CartesianGrid vertical={horizontal} horizontal={!horizontal} stroke={COLORS.grid} />
        {horizontal ? (
          <>
            <XAxis type="number" allowDecimals={false} {...axisProps} />
            <YAxis type="category" dataKey="label" width={150} {...axisProps} />
          </>
        ) : (
          <>
            <XAxis dataKey="label" {...axisProps} />
            <YAxis allowDecimals={false} {...axisProps} width={36} />
          </>
        )}
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f5f5f2" }} formatter={(v) => [v, "Students"]} />
        <Bar isAnimationActive={false} dataKey="value" fill={COLORS.series} maxBarSize={24} radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}>
          <LabelList dataKey="value" position={horizontal ? "right" : "top"} fontSize={11} fill={COLORS.ink2} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Risk levels per class level, stacked, in the reserved status colours (with a legend). */
export function RiskByLevelChart({ data }: { data: { level: string; High: number; Medium: number; Low: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke={COLORS.grid} />
        <XAxis type="number" allowDecimals={false} {...axisProps} />
        <YAxis type="category" dataKey="level" width={48} {...axisProps} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f5f5f2" }} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} itemSorter={null} />
        <Bar isAnimationActive={false} dataKey="High" name="High risk" stackId="r" fill={COLORS.high} stroke={COLORS.surface} strokeWidth={2} maxBarSize={24} />
        <Bar isAnimationActive={false} dataKey="Medium" name="Medium risk" stackId="r" fill={COLORS.medium} stroke={COLORS.surface} strokeWidth={2} maxBarSize={24} />
        <Bar isAnimationActive={false} dataKey="Low" name="Low risk" stackId="r" fill={COLORS.low} stroke={COLORS.surface} strokeWidth={2} maxBarSize={24} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Probability of each class; the predicted class is emphasised, the others recede. */
export function ProbabilityBars({ probabilities, predicted }: {
  probabilities: Record<PerformanceClass, number>; predicted: PerformanceClass;
}) {
  const data = CLASSES.map((c) => ({ label: c, value: probabilities[c] ?? 0 }));
  return (
    <ResponsiveContainer width="100%" height={170}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 44, left: 4, bottom: 0 }}>
        <XAxis type="number" domain={[0, 1]} hide />
        <YAxis type="category" dataKey="label" width={84} {...axisProps} axisLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f5f5f2" }} formatter={(v) => [`${Math.round(Number(v) * 100)}%`, "Probability"]} />
        <Bar isAnimationActive={false} dataKey="value" maxBarSize={18} radius={[0, 4, 4, 0]}>
          {data.map((d) => <Cell key={d.label} fill={d.label === predicted ? COLORS.series : COLORS.muted} />)}
          <LabelList dataKey="value" position="right" fontSize={11} fill={COLORS.ink2}
            formatter={(v: unknown) => `${Math.round(Number(v) * 100)}%`} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Semester GPA over time, with the Fail line at 2.00. */
export function GpaHistoryChart({ records }: { records: AcademicRecord[] }) {
  const data = records.filter((r) => r.gpa != null).map((r) => ({
    term: `${r.session.slice(2, 4)}/${r.session.slice(7)} ${r.semester === "First" ? "S1" : "S2"}`,
    gpa: r.gpa, level: r.level,
  }));
  if (data.length === 0) return <p className="text-sm text-muted">No results yet.</p>;
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 4 }}>
        <CartesianGrid vertical={false} stroke={COLORS.grid} />
        <XAxis dataKey="term" {...axisProps} />
        <YAxis domain={[0, 4]} ticks={[0, 1, 2, 3, 4]} {...axisProps} width={30} />
        <ReferenceLine y={2} stroke={COLORS.high} strokeOpacity={0.6}
          label={{ value: "Fail below 2.00", position: "insideBottomRight", fill: COLORS.ink2, fontSize: 11 }} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v) => [Number(v).toFixed(2), "Semester GPA"]} />
        <Line isAnimationActive={false} type="monotone" dataKey="gpa" stroke={COLORS.series} strokeWidth={2}
          dot={{ r: 4, fill: COLORS.series, stroke: COLORS.surface, strokeWidth: 2 }} activeDot={{ r: 6 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
