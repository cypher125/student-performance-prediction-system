export const pct = (p: number | null | undefined) => (p == null ? "–" : `${Math.round(p * 100)}%`);

export const num = (v: number | null | undefined, digits = 1) => (v == null ? "–" : v.toFixed(digits));

export const gpa = (v: number | null | undefined) => num(v, 2);

export function value(feature: string, v: number | string | null) {
  if (v == null) return "not recorded";
  if (typeof v === "string") return v;
  if (feature.includes("gpa")) return v.toFixed(2);
  return feature.endsWith("pct") || feature.endsWith("score") ? `${v.toFixed(1)}%` : String(v);
}

export function date(iso: string | null | undefined) {
  if (!iso) return "–";
  return new Date(iso).toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
