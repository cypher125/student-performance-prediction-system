"use client";

import {
  Bar, BarChart, CartesianGrid, Cell, LabelList, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import { value as formatValue } from "@/lib/format";
import type { AcademicRecord, ExplanationItem, PerformanceClass } from "@/lib/types";
import { CLASSES } from "@/lib/types";

// Chart colours: a neutral slate for single series, so the college green is never read as
// "Low risk"; red against slate for the explanation's two directions (checked for colour-blind
// separation); the status colours only where a chart shows risk levels.
export const COLORS = {
  series: "#475569",
  toward: "#e34948",
  away: "#475569",
  muted: "#cfd5dc",
  grid: "#e5e8e2",
  axis: "#6b746e",
  ink2: "#4b544e",
  surface: "#ffffff",
  high: "#d03b3b",
  medium: "#fab219",
  low: "#0ca30c",
};

const axisProps = { stroke: COLORS.grid, tick: { fill: COLORS.ink2, fontSize: 12 }, tickLine: false };
const tooltipStyle = { borderRadius: 4, border: `1px solid ${COLORS.grid}`, fontSize: 12 };
const cursor = { fill: "#f4f5f2" };
/** Legend text in the ordinary text colour; the coloured marker beside it carries the series. */
const legendText = (value: string) => <span style={{ color: COLORS.ink2 }}>{value}</span>;

/** Why the model predicted what it did: bars push the probability of Fail up (red) or down (grey). */
export function ExplanationChart({ items }: { items: ExplanationItem[] }) {
  const data = items.map((i) => ({ ...i, name: `${i.label}: ${formatValue(i.feature, i.value)}` }));
  // A symmetric axis on round numbers (±0.1, ±0.2, ±0.4 ...) with room for the value labels.
  const largest = Math.max(0.05, ...items.map((i) => Math.abs(i.contribution)));
  const step = largest > 0.2 ? 0.1 : 0.05;
  const span = Math.ceil((largest * 1.15) / step) * step;
  const ticks = [-span, -span / 2, 0, span / 2, span];
  return (
    <div>
      <ResponsiveContainer width="100%" height={46 * items.length + 40}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 48, top: 4, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke={COLORS.grid} />
          <XAxis type="number" domain={[-span, span]} ticks={ticks} {...axisProps}
            tickFormatter={(v: number) => String(Math.round(v * 100) / 100)} />
          <YAxis type="category" dataKey="name" width={210} {...axisProps} />
          <ReferenceLine x={0} stroke={COLORS.axis} />
          <Tooltip contentStyle={tooltipStyle} cursor={cursor}
            formatter={(v) => [Number(v).toFixed(3), "Effect on probability of Fail"]} />
          <Bar isAnimationActive={false} dataKey="contribution" maxBarSize={22} radius={1}>
            {data.map((d) => <Cell key={d.feature} fill={d.contribution > 0 ? COLORS.toward : COLORS.away} />)}
            <LabelList dataKey="contribution" position="right" fontSize={11} fill={COLORS.ink2}
              formatter={(v: unknown) => `${Number(v) > 0 ? "+" : ""}${Number(v).toFixed(3)}`} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-1 text-xs text-muted">
        <span className="mr-1 inline-block h-2.5 w-2.5 rounded-[1px] align-middle" style={{ background: COLORS.toward }} /> raises the risk of failing
        <span className="ml-4 mr-1 inline-block h-2.5 w-2.5 rounded-[1px] align-middle" style={{ background: COLORS.away }} /> lowers it
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
        <Tooltip contentStyle={tooltipStyle} cursor={cursor} formatter={(v) => [v, "Students"]} />
        <Bar isAnimationActive={false} dataKey="value" fill={COLORS.series} maxBarSize={24} radius={horizontal ? [0, 2, 2, 0] : [2, 2, 0, 0]}>
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
        <Tooltip contentStyle={tooltipStyle} cursor={cursor} />
        <Legend iconType="square" wrapperStyle={{ fontSize: 12 }} itemSorter={null} formatter={legendText} />
        <Bar isAnimationActive={false} dataKey="High" name="High risk" stackId="r" fill={COLORS.high} stroke={COLORS.surface} strokeWidth={2} maxBarSize={24} />
        <Bar isAnimationActive={false} dataKey="Medium" name="Medium risk" stackId="r" fill={COLORS.medium} stroke={COLORS.surface} strokeWidth={2} maxBarSize={24} />
        <Bar isAnimationActive={false} dataKey="Low" name="Low risk" stackId="r" fill={COLORS.low} stroke={COLORS.surface} strokeWidth={2} maxBarSize={24} radius={[0, 2, 2, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Probability of each class; the predicted class is emphasised, the others recede. */
export function ProbabilityBars({ probabilities, predicted }: {
  probabilities: Record<PerformanceClass, number>; predicted: PerformanceClass;
}) {
  // A hairline minimum keeps a 0% class's bar, and so its label, on the chart.
  const data = CLASSES.map((c) => {
    const p = probabilities[c] ?? 0;
    return { label: c, value: Math.max(p, 0.004), shown: `${Math.round(p * 100)}%` };
  });
  return (
    <ResponsiveContainer width="100%" height={170}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 44, left: 4, bottom: 0 }}>
        <XAxis type="number" domain={[0, 1]} hide />
        <YAxis type="category" dataKey="label" width={84} {...axisProps} axisLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={cursor} formatter={(_v, _n, item) => [item.payload.shown, "Probability"]} />
        <Bar isAnimationActive={false} dataKey="value" maxBarSize={18} radius={[0, 2, 2, 0]}>
          {data.map((d) => <Cell key={d.label} fill={d.label === predicted ? COLORS.series : COLORS.muted} />)}
          <LabelList dataKey="shown" position="right" fontSize={11} fill={COLORS.ink2} />
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
