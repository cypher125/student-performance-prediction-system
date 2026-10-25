export type Role = "admin" | "lecturer" | "adviser" | "student";
export type Risk = "High" | "Medium" | "Low";
export type PerformanceClass = "Distinction" | "Merit" | "Pass" | "Fail";
export const CLASSES: PerformanceClass[] = ["Distinction", "Merit", "Pass", "Fail"];
export const LEVELS = ["ND1", "ND2", "HND1", "HND2"];

export interface User {
  id: number;
  username: string;
  full_name: string;
  email: string | null;
  role: Role;
  is_active: boolean;
  last_login: string | null;
  student_code: string | null;
}

export interface Student {
  code: string;
  matric_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
  department: string;
  programme: string;
  level: string;
  session: string;
  entry_session: string;
}

export interface AcademicRecord {
  id: number;
  level: string;
  session: string;
  semester: string;
  attendance_pct: number | null;
  ca_score: number | null;
  assignment_score: number | null;
  prior_gpa: number | null;
  exam_score: number | null;
  gpa: number | null;
  performance_class: PerformanceClass | null;
  has_results: boolean;
  source: string;
}

export interface ExplanationItem {
  feature: string;
  label: string;
  value: number | string | null;
  contribution: number;
}

export interface Recommendation {
  audience: "student" | "staff";
  factor: string;
  text: string;
}

export interface Prediction {
  id: number;
  record_id: number;
  predicted_class: PerformanceClass;
  confidence_score: number;
  fail_probability: number;
  risk_level: Risk;
  model_version: string;
  created_at: string;
  probabilities?: Record<PerformanceClass, number>;
  explanation?: ExplanationItem[];
  recommendations?: Recommendation[];
  top_factor?: string | null;
}

export interface Alert {
  id: number;
  alert_type: string;
  message: string;
  status: "New" | "Acknowledged" | "Resolved";
  sent_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  action_taken: string | null;
  student: { code: string; full_name: string; level: string };
  risk_level: Risk;
  fail_probability: number;
  session: string;
  semester: string;
}
