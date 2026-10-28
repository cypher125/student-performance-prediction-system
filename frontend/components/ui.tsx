"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";
import type { PerformanceClass, Risk } from "@/lib/types";

export function PageHeader({ title, subtitle, actions, crumbs }: {
  title: string; subtitle?: ReactNode; actions?: ReactNode; crumbs?: { label: string; href?: string }[];
}) {
  return (
    <div className="mb-5 border-b border-line pb-4">
      {crumbs && (
        <nav className="no-print mb-2 text-xs text-muted" aria-label="Breadcrumb">
          {crumbs.map((c, i) => (
            <span key={i}>
              {i > 0 && <span className="mx-1.5">/</span>}
              {c.href ? <Link href={c.href} className="text-brand hover:underline">{c.label}</Link> : <span>{c.label}</span>}
            </span>
          ))}
        </nav>
      )}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-semibold leading-tight text-ink">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-ink-2">{subtitle}</p>}
        </div>
        {actions && <div className="no-print flex flex-wrap items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}

/** A panel: a titled box with a grey header strip, as on most college portals. */
export function Card({ title, subtitle, children, className = "", actions }: {
  title?: string; subtitle?: ReactNode; children: ReactNode; className?: string; actions?: ReactNode;
}) {
  return (
    <section className={`rounded border border-line bg-surface ${className}`}>
      {(title || actions) && (
        <div className="flex items-start justify-between gap-3 border-b border-line bg-panel px-4 py-2.5">
          <div>
            {title && <h2 className="text-[15px] font-semibold text-ink">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-ink-2">{subtitle}</p>}
          </div>
          {actions}
        </div>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

const TONE_EDGE: Record<Risk | "brand", string> = {
  High: "border-l-critical", Medium: "border-l-warn", Low: "border-l-good", brand: "border-l-brand",
};

export function StatTile({ label, value, note, tone }: { label: string; value: ReactNode; note?: ReactNode; tone?: Risk }) {
  return (
    <div className={`rounded border border-line border-l-4 bg-surface px-4 py-3 ${TONE_EDGE[tone ?? "brand"]}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-2">{label}</p>
      <p className="tabular mt-1 text-3xl font-semibold text-ink">{value}</p>
      {note && <p className="mt-0.5 text-xs text-muted">{note}</p>}
    </div>
  );
}

const RISK_STYLE: Record<Risk, string> = {
  High: "border-critical/40 bg-critical/10 text-critical-text",
  Medium: "border-warn/60 bg-warn/15 text-warn-text",
  Low: "border-good/40 bg-good/10 text-good-text",
};

/** Risk is always written out in words, so colour is never the only signal. */
export function RiskBadge({ risk }: { risk: Risk | null | undefined }) {
  if (!risk) return <span className="text-sm text-muted">–</span>;
  return <span className={`inline-block rounded-sm border px-1.5 py-px text-xs font-semibold ${RISK_STYLE[risk]}`}>{risk} risk</span>;
}

export function ClassBadge({ value }: { value: PerformanceClass | null | undefined }) {
  if (!value) return <span className="text-sm text-muted">–</span>;
  return <span className="inline-block rounded-sm border border-line bg-panel px-1.5 py-px text-xs font-medium text-ink">{value}</span>;
}

export function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <span className="text-sm text-muted">–</span>;
  const cls = status === "New" ? "border-brand/30 bg-brand-soft text-brand"
    : status === "Acknowledged" ? "border-gold/60 bg-gold-soft text-gold-text" : "border-chart/30 bg-chart/5 text-chart";
  return <span className={`inline-block rounded-sm border px-1.5 py-px text-xs font-semibold ${cls}`}>{status}</span>;
}

export function Button({ variant = "primary", busy, children, className = "", ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost"; busy?: boolean;
}) {
  const style = {
    primary: "bg-brand text-white hover:bg-brand-dark",
    secondary: "border border-line bg-surface text-ink hover:bg-page",
    ghost: "text-brand hover:underline",
  }[variant];
  return (
    <button
      {...rest}
      disabled={rest.disabled || busy}
      className={`inline-flex items-center justify-center gap-2 rounded px-3.5 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${style} ${className}`}
    >
      {busy && <Loader2 size={15} className="animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Field({ label, hint, error, children }: { label: string; hint?: string; error?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-ink">{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-muted">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-critical-text">{error}</span>}
    </label>
  );
}

const control = "w-full rounded border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20";

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`${control} ${props.className ?? ""}`} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`${control} ${props.className ?? ""}`} />;
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-10 text-sm text-ink-2">
      <Loader2 size={16} className="animate-spin" aria-hidden /> {label}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded border border-critical/30 border-l-4 border-l-critical bg-critical/5 px-3 py-2 text-sm text-critical-text">
      {message}
    </div>
  );
}

export function SuccessNote({ children }: { children: ReactNode }) {
  return (
    <div role="status" className="rounded border border-brand/30 border-l-4 border-l-brand bg-brand-soft px-3 py-2 text-sm text-brand-dark">
      {children}
    </div>
  );
}

export function Table({ head, children }: { head: ReactNode[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded border border-line">
      <table className="tabular w-full text-left text-sm">
        <thead className="border-b border-line bg-panel text-[11px] uppercase tracking-wide text-ink-2">
          <tr>{head.map((h, i) => <th key={i} className="whitespace-nowrap px-3 py-2 font-semibold">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-line-soft [&>tr:nth-child(even)]:bg-[#fafbf9]">{children}</tbody>
      </table>
    </div>
  );
}

export function Td({ children, className = "", wrap = false }: { children: ReactNode; className?: string; wrap?: boolean }) {
  return <td className={`${wrap ? "whitespace-normal" : "whitespace-nowrap"} px-3 py-2 ${className}`}>{children}</td>;
}
