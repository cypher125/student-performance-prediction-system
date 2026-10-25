"""Shared settings: paths, the fixed random seed, and the study's categories."""
from pathlib import Path

# One seed for every split, model and simulation, so results reproduce exactly (3.10).
SEED = 42

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
RAW_UCI_DIR = DATA_DIR / "raw" / "uci"
SIMULATED_DIR = DATA_DIR / "simulated"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

SIM_RAW_CSV = SIMULATED_DIR / "yabatech_simulated_raw.csv"
SIM_CURRENT_CSV = SIMULATED_DIR / "current_semester_2025_2026.csv"
SIM_DIRECTORY_CSV = SIMULATED_DIR / "demo_student_directory.csv"
SIM_CLEAN_CSV = PROCESSED_DIR / "yabatech_simulated_clean.csv"
UCI_PREPARED_CSV = {course: PROCESSED_DIR / f"uci_{course}_prepared.csv" for course in ("por", "mat")}

LEVELS = ["ND1", "ND2", "HND1", "HND2"]
SEMESTERS = ["First", "Second"]
# Sessions covered by the study's time scope (1.8).
SESSIONS = ["2020/2021", "2021/2022", "2022/2023", "2023/2024", "2024/2025"]

# Performance categories from Table 3.1, best first.
CLASSES = ["Distinction", "Merit", "Pass", "Fail"]

# Features known before final examinations: the early-warning model may use only these
# (objective 5, H02). exam_score and gpa are outcomes, never inputs.
EARLY_NUMERIC_FEATURES = ["attendance_pct", "ca_score", "assignment_score", "prior_gpa"]
EARLY_CATEGORICAL_FEATURES = ["level"]
TARGET = "performance_class"
