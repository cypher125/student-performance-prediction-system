"use client";

import { AlertTriangle, CheckCircle2, CircleAlert, Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";
import type { PerformanceClass, Risk } from "@/lib/types";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink-2">{subtitle}</p>}
      </div>
      {actions && <div className="no-print flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Card({ title, subtitle, children, className = "", actions }: {
  title?: string; subtitle?: ReactNode; children: ReactNode; className?: string; actions?: ReactNode;
}) {
  return (
    <section className={`rounded-xl border border-line bg-surface p-5 ${className}`}>
      {(title || actions) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && <h2 className="text-base font-semibold">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-sm text-ink-2">{subtitle}</p>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function StatTile({ label, value, note, tone }: { label: string; value: ReactNode; note?: ReactNode; tone?: Risk }) {
  const bar = tone === "High" ? "bg-critical" : tone === "Medium" ? "bg-warn" : tone === "Low" ? "bg-good" : "bg-brand";
  return (
    <div className="relative overflow-hidden rounded-xl border border-line bg-surface p-4">
      <span className={`absolute inset-y-0 left-0 w-1 ${bar}`} />
      <p className="text-sm text-ink-2">{label}</p>
      <p className="mt-1 text-3xl font-semibold">{value}</p>
      {note && <p className="mt-1 text-xs text-muted">{note}</p>}
    </div>
  );
}

const RISK_STYLE: Record<Risk, { cls: string; Icon: typeof AlertTriangle }> = {
  High: { cls: "bg-critical/10 text-critical ring-critical/30", Icon: AlertTriangle },
  Medium: { cls: "bg-warn/15 text-warn-text ring-warn/40", Icon: CircleAlert },
  Low: { cls: "bg-good/10 text-good-text ring-good/30", Icon: CheckCircle2 },
};

/** Status colour always comes with an icon and a word, never colour alone. */
export function RiskBadge({ risk }: { risk: Risk | null | undefined }) {
  if (!risk) return <span className="text-sm text-muted">–</span>;
  const { cls, Icon } = RISK_STYLE[risk];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${cls}`}>
      <Icon size={13} aria-hidden /> {risk} risk
    </span>
  );
}

export function ClassBadge({ value }: { value: PerformanceClass | null | undefined }) {
  if (!value) return <span className="text-sm text-muted">–</span>;
  return <span className="inline-flex rounded-md bg-page px-2 py-0.5 text-xs font-medium ring-1 ring-line ring-inset">{value}</span>;
}

export function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <span className="text-sm text-muted">–</span>;
  const cls = status === "New" ? "bg-brand-soft text-brand-dark" : status === "Acknowledged" ? "bg-warn/15 text-warn-text" : "bg-good/10 text-good-text";
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{status}</span>;
}

export function Button({ variant = "primary", busy, children, className = "", ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost"; busy?: boolean;
}) {
  const style = {
    primary: "bg-brand text-white hover:bg-brand-dark",
    secondary: "border border-line bg-surface text-ink hover:bg-page",
    ghost: "text-brand-dark hover:bg-brand-soft",
  }[variant];
  return (
    <button
      {...rest}
      disabled={rest.disabled || busy}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${style} ${className}`}
    >
      {busy && <Loader2 size={15} className="animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Field({ label, hint, error, children }: { label: string; hint?: string; error?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-muted">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-critical">{error}</span>}
    </label>
  );
}

const control = "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20";

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
    <div role="alert" className="flex items-start gap-2 rounded-lg border border-critical/30 bg-critical/5 px-3 py-2 text-sm text-critical">
      <AlertTriangle size={16} className="mt-0.5 shrink-0" aria-hidden /> {message}
    </div>
  );
}

export function SuccessNote({ children }: { children: ReactNode }) {
  return (
    <div role="status" className="flex items-start gap-2 rounded-lg border border-good/30 bg-good/5 px-3 py-2 text-sm text-good-text">
      <CheckCircle2 size={16} className="mt-0.5 shrink-0" aria-hidden /> <div>{children}</div>
    </div>
  );
}

export function Table({ head, children }: { head: ReactNode[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="tabular w-full text-left text-sm">
        <thead className="bg-page text-xs uppercase tracking-wide text-ink-2">
          <tr>{head.map((h, i) => <th key={i} className="whitespace-nowrap px-3 py-2.5 font-medium">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-line">{children}</tbody>
      </table>
    </div>
  );
}

export function Td({ children, className = "", wrap = false }: { children: ReactNode; className?: string; wrap?: boolean }) {
  return <td className={`${wrap ? "whitespace-normal" : "whitespace-nowrap"} px-3 py-2.5 ${className}`}>{children}</td>;
}
