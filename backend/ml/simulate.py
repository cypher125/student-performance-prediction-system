"""Generate the simulated YABATECH-format dataset.

The department's records were not available, so this module builds a clearly
labelled SIMULATED dataset with the fields in Table 3.1. Each row is one student
in one semester. Every value comes from the generative model below; none of it
is real student data. docs/simulated-dataset.md describes the design for the
write-up.

How a row is produced
1. Each student has two hidden traits, ability and engagement (correlation 0.45).
2. Each semester shifts both traits a little (the student's form that term) and
   adds small level and session effects.
3. Each semester also has its own shock for each measure (attendance, CA,
   assignments, exam), shared by all that term's courses: exam-period
   preparation or illness, for example. These do not average away across
   courses, which keeps the measures realistically imperfect proxies.
4. In each of the semester's 8 courses the student gets attendance (lectures
   attended out of 30), a CA test score, an assignment score (0 when not
   submitted) and an exam score. Very low attendance can mean missing the exam.
5. Course total = 30% CA tests + 10% assignments + 60% exam, graded on the NBTE
   scale; the credit-weighted mean of grade points is the semester GPA.
6. The row keeps the course averages, the GPA and the previous semester's GPA.
   The hidden traits are never written out.
Effect sizes were set so the relationships have realistic strength (for example,
attendance correlates with grades at about r = 0.4 in the meta-analysis by
Credé, Roch and Kieszczynka, 2010), not to make any model look accurate.
Students may withdraw after a poor semester, so later levels have fewer rows.
"""
import math

import numpy as np
import pandas as pd

from . import config
from .grading import round_half_up, semester_gpa

# 2019/2020 entrants supply second-year rows in 2020/2021; 2025/2026 entrants are the current first years.
ENTRY_START_YEARS = range(2019, 2026)
FIRST_START_YEAR, LAST_START_YEAR = 2020, 2024  # historical sessions: 2020/2021 to 2024/2025
# The system is demonstrated in 2025/2026 (1.8): first-semester records before exams, no results yet.
CURRENT_START_YEAR, CURRENT_SEMESTER = 2025, "First"
CURRENT_COLUMNS = ["student_code", "level", "session", "semester", "attendance_pct", "ca_score",
                   "assignment_score", "prior_gpa"]
CURRENT_MISSING_RATES = {"attendance_pct": 0.03, "assignment_score": 0.04}

ND_COHORT_SIZE = (60, 80)  # entrants per session, inclusive
HND_COHORT_SIZE = (42, 58)
HND_ABILITY_MEAN, HND_ABILITY_SD = 0.25, 0.9  # HND entrants already passed ND

COURSES_PER_SEMESTER = 8
CREDIT_UNIT_CHOICES, CREDIT_UNIT_PROBS = [1, 2, 3, 4], [0.05, 0.35, 0.45, 0.15]
COURSE_DIFFICULTY_SD = 0.25
LECTURES_PER_COURSE = 30
CA_TEST_WEIGHT, ASSIGNMENT_WEIGHT, EXAM_WEIGHT = 0.30, 0.10, 0.60

ABILITY_ENGAGEMENT_CORR = 0.45
SEMESTER_SHOCK_SD = 0.30
ENGAGEMENT_SHOCK_SD = 0.40
# Per-semester shock for each measure, shared across that term's courses (logit scale).
MEASURE_SHOCK_SD = {"attendance": 0.40, "ca": 0.30, "assignment": 0.40, "exam": 0.30}
LEVEL_EFFECT = {"ND1": -0.10, "ND2": 0.0, "HND1": -0.05, "HND2": 0.05}
SESSION_EFFECT_SD = 0.07

# Below 40% attendance in a course, a student misses its exam with this probability.
LOW_ATTENDANCE_THRESHOLD = 0.40
LOW_ATTENDANCE_EXAM_MISS = 0.15

# Withdrawal probability after a semester, by GPA.
WITHDRAWAL_RULES = [(1.0, 0.30), (1.5, 0.10), (math.inf, 0.015)]

# Record-keeping imperfections added to the raw file, so cleaning has real work (3.16).
NOISE_RATES = {
    "duplicate": 0.010,            # record entered twice
    "label_variant": 0.030,        # e.g. "nd 1", "1st", "2021/22"
    "missing_attendance": 0.040,   # lecturer did not submit attendance
    "missing_assignment": 0.060,
    "missing_ca": 0.010,
    "missing_gpa": 0.005,          # result withheld
    "incomplete": 0.005,           # attendance, CA and assignment all missing
    "attendance_typo": 0.003,      # extra digit, e.g. 83.3 typed as 833
    "gpa_typo": 0.002,             # decimal point dropped, e.g. 2.86 typed as 28.6
}

COLUMNS = ["student_code", "level", "session", "semester", "attendance_pct", "ca_score",
           "assignment_score", "exam_score", "gpa", "prior_gpa"]


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _session_name(start_year):
    return f"{start_year}/{start_year + 1}"


def _course_plans(rng):
    """Credit units and difficulty for the 8 courses of each level and semester."""
    plans = {}
    for level in config.LEVELS:
        for semester in config.SEMESTERS:
            credits = rng.choice(CREDIT_UNIT_CHOICES, size=COURSES_PER_SEMESTER, p=CREDIT_UNIT_PROBS)
            difficulty = rng.normal(0.0, COURSE_DIFFICULTY_SD, size=COURSES_PER_SEMESTER)
            plans[(level, semester)] = (credits, difficulty)
    return plans


def _simulate_semester(ability, engagement, plan, rng):
    credits, difficulty = plan
    k = len(credits)
    shock = {name: rng.normal(0, sd) for name, sd in MEASURE_SHOCK_SD.items()}

    p_attend = _sigmoid(1.45 + 0.45 * engagement + 0.05 * ability + shock["attendance"]
                        + rng.normal(0, 0.4, k))
    attended = rng.binomial(LECTURES_PER_COURSE, p_attend) / LECTURES_PER_COURSE

    ca = 100 * _sigmoid(0.42 + 0.30 * ability + 0.10 * engagement + 0.6 * (attended - 0.8)
                        + shock["ca"] - difficulty + rng.normal(0, 0.40, k))
    submitted = rng.random(k) >= _sigmoid(-3.3 - 0.8 * engagement)
    assignment = np.where(
        submitted,
        100 * _sigmoid(0.60 + 0.12 * ability + 0.35 * engagement + shock["assignment"]
                       + rng.normal(0, 0.45, k)),
        0.0)
    exam = 100 * _sigmoid(0.15 + 0.38 * ability + 0.05 * engagement + 0.6 * (attended - 0.8)
                          + shock["exam"] - difficulty + rng.normal(0, 0.40, k))
    missed_exam = (attended < LOW_ATTENDANCE_THRESHOLD) & (rng.random(k) < LOW_ATTENDANCE_EXAM_MISS)
    exam = np.where(missed_exam, 0.0, exam)

    # Mark sheets hold whole numbers.
    ca, assignment, exam = round_half_up(ca), round_half_up(assignment), round_half_up(exam)
    total = CA_TEST_WEIGHT * ca + ASSIGNMENT_WEIGHT * assignment + EXAM_WEIGHT * exam
    return {
        "attendance_pct": round(100 * float(attended.mean()), 1),
        "ca_score": round(float(ca.mean()), 1),
        "assignment_score": round(float(assignment.mean()), 1),
        "exam_score": round(float(exam.mean()), 1),
        "gpa": semester_gpa(total, credits),
    }


def _withdraws(gpa, rng):
    for ceiling, probability in WITHDRAWAL_RULES:
        if gpa < ceiling:
            return rng.random() < probability
    return False


def _simulate_student(code, levels, entry_year, ability_mean, ability_sd, ctx, rng):
    z = rng.normal()
    ability = ability_mean + ability_sd * z
    engagement = ABILITY_ENGAGEMENT_CORR * z + math.sqrt(1 - ABILITY_ENGAGEMENT_CORR ** 2) * rng.normal()
    if levels[0] == "HND1":
        # Previous GPA for the first HND semester is the final ND CGPA.
        prior = float(np.clip(round(2.85 + 0.45 * z + rng.normal(0, 0.2), 2), 2.0, 3.95))
    else:
        prior = float("nan")  # new ND1 students have no GPA yet

    rows = []
    for year_offset, level in enumerate(levels):
        start_year = entry_year + year_offset
        for semester in config.SEMESTERS:
            a_t = (ability + rng.normal(0, SEMESTER_SHOCK_SD) + LEVEL_EFFECT[level]
                   + ctx["session_effect"][start_year])
            e_t = engagement + rng.normal(0, ENGAGEMENT_SHOCK_SD)
            record = _simulate_semester(a_t, e_t, ctx["plans"][(level, semester)], rng)
            rows.append({"student_code": code, "level": level, "session": _session_name(start_year),
                         "semester": semester, **record, "prior_gpa": prior, "_start_year": start_year})
            prior = record["gpa"]
            if _withdraws(record["gpa"], rng):
                return rows
    return rows


def _chronological(df, columns):
    ordered = df.assign(
        _level_order=lambda d: d["level"].map({lvl: i for i, lvl in enumerate(config.LEVELS)}),
        _semester_order=lambda d: d["semester"].map({s: i for i, s in enumerate(config.SEMESTERS)}),
    ).sort_values(by=["_start_year", "_semester_order", "_level_order", "student_code"])
    return ordered[columns].reset_index(drop=True)


def simulate_cohorts(rng, name_rng=None):
    """One simulated population, returned three ways.

    history   records for 2020/2021 to 2024/2025, as a department export would hold them
    current   first semester of 2025/2026 before exams: no exam score or GPA yet
    directory fictional names and SIM/ matric numbers for the demo app
    """
    ctx = {
        "session_effect": {y: rng.normal(0, SESSION_EFFECT_SD) for y in range(2019, 2028)},
        "plans": _course_plans(rng),
    }
    programmes = [
        ("ND", ("ND1", "ND2"), ND_COHORT_SIZE, 0.0, 1.0),
        ("HND", ("HND1", "HND2"), HND_COHORT_SIZE, HND_ABILITY_MEAN, HND_ABILITY_SD),
    ]
    rows, students, serial = [], [], 0
    for programme, levels, (low, high), mean, sd in programmes:
        for entry_year in ENTRY_START_YEARS:
            for _ in range(int(rng.integers(low, high + 1))):
                serial += 1
                code = f"S{serial:04d}"
                students.append({"student_code": code, "programme": programme, "entry_year": entry_year})
                rows.extend(_simulate_student(code, levels, entry_year, mean, sd, ctx, rng))

    df = pd.DataFrame(rows)
    history = _chronological(df.loc[df["_start_year"].between(FIRST_START_YEAR, LAST_START_YEAR)], COLUMNS)
    current = _chronological(
        df.loc[(df["_start_year"] == CURRENT_START_YEAR) & (df["semester"] == CURRENT_SEMESTER)],
        CURRENT_COLUMNS)
    for column, rate in CURRENT_MISSING_RATES.items():
        current.loc[rng.random(len(current)) < rate, column] = np.nan

    in_use = set(history["student_code"]) | set(current["student_code"])
    directory = _directory([s for s in students if s["student_code"] in in_use],
                           name_rng if name_rng is not None else np.random.default_rng([config.SEED, 1]))
    return history, current, directory


# Fictional demo identities: common Nigerian names, paired at random.
FIRST_NAMES = [
    "Adebayo", "Adewale", "Ayomide", "Babatunde", "Bolanle", "Damilola", "Folake", "Funmilayo", "Kehinde",
    "Mojisola", "Olamide", "Oluwaseun", "Temitope", "Tolulope", "Yetunde", "Abiodun", "Opeyemi",
    "Iyanuoluwa", "Adaeze", "Amarachi", "Chidinma", "Chinedu", "Chiamaka", "Ebuka", "Emeka", "Ifeanyi",
    "Ngozi", "Nnamdi", "Obinna", "Uchenna", "Ugochi", "Kosisochukwu", "Abdullahi", "Aisha", "Amina",
    "Bilkisu", "Fatima", "Habiba", "Ibrahim", "Maryam", "Musa", "Sadiq", "Usman", "Zainab", "Hauwa",
    "Aliyu", "Blessing", "Daniel", "Deborah", "Esther", "Favour", "Godwin", "Joy", "Peace", "Samuel",
    "Victor", "Grace", "Precious", "Emmanuel", "David",
]
SURNAMES = [
    "Adebayo", "Adeyemi", "Afolabi", "Ajayi", "Akinola", "Alabi", "Babalola", "Balogun", "Ogunleye",
    "Olatunji", "Oyelaran", "Salami", "Ogundipe", "Oladipo", "Bakare", "Durojaiye", "Chukwu", "Eze",
    "Nwosu", "Okafor", "Okeke", "Nwachukwu", "Okonkwo", "Uchendu", "Anyanwu", "Nnaji", "Igwe", "Okoro",
    "Bello", "Danjuma", "Garba", "Ibrahim", "Mohammed", "Musa", "Sani", "Suleiman", "Yusuf", "Lawal",
    "Aliyu", "Shehu", "Edet", "Bassey", "Etim", "Osagie", "Omoregie", "Ekanem",
]


def _directory(students, rng):
    rows, serial_by_intake = [], {}
    for s in students:
        intake = (s["programme"], s["entry_year"])
        serial_by_intake[intake] = serial_by_intake.get(intake, 0) + 1
        rows.append({
            "student_code": s["student_code"],
            "first_name": str(rng.choice(FIRST_NAMES)),
            "last_name": str(rng.choice(SURNAMES)),
            "matric_number": f"SIM/{s['programme']}/{s['entry_year'] % 100:02d}/{serial_by_intake[intake]:04d}",
            "programme": s["programme"],
            "entry_session": _session_name(s["entry_year"]),
            "department": "Computer Science",
        })
    return pd.DataFrame(rows)


_LEVEL_VARIANTS = {
    "ND1": ["nd1", "ND 1", "Nd1", "ND-1"], "ND2": ["nd2", "ND 2", "Nd2", "ND-2"],
    "HND1": ["hnd1", "HND 1", "Hnd1", "HND-1"], "HND2": ["hnd2", "HND 2", "Hnd2", "HND-2"],
}
_SEMESTER_VARIANTS = {"First": ["first", "1st", "FIRST"], "Second": ["second", "2nd", "SECOND"]}


def _session_variants(session):
    start, end = session.split("/")
    return [f"{start}/{end[2:]}", f"{start}-{end}", f"{start} / {end}"]


def add_record_keeping_noise(records, rng):
    """Raw-export version of the records: missing values, typos, label variants, duplicates."""
    df = records.copy()
    n = len(df)

    def pick(rate):
        return rng.random(n) < rate

    df.loc[pick(NOISE_RATES["missing_attendance"]), "attendance_pct"] = np.nan
    df.loc[pick(NOISE_RATES["missing_assignment"]), "assignment_score"] = np.nan
    df.loc[pick(NOISE_RATES["missing_ca"]), "ca_score"] = np.nan
    df.loc[pick(NOISE_RATES["missing_gpa"]), "gpa"] = np.nan
    df.loc[pick(NOISE_RATES["incomplete"]), ["attendance_pct", "ca_score", "assignment_score"]] = np.nan

    typo = pick(NOISE_RATES["attendance_typo"]) & df["attendance_pct"].notna().to_numpy()
    df.loc[typo, "attendance_pct"] = (df.loc[typo, "attendance_pct"] * 10).round(1)
    typo = pick(NOISE_RATES["gpa_typo"]) & df["gpa"].notna().to_numpy()
    df.loc[typo, "gpa"] = (df.loc[typo, "gpa"] * 10).round(1)

    for column, variants_for in (
        ("level", lambda v: _LEVEL_VARIANTS[v]),
        ("semester", lambda v: _SEMESTER_VARIANTS[v]),
        ("session", _session_variants),
    ):
        mask = pick(NOISE_RATES["label_variant"])
        df.loc[mask, column] = [str(rng.choice(variants_for(v))) for v in df.loc[mask, column]]

    duplicates = df[pick(NOISE_RATES["duplicate"])]
    df = pd.concat([df, duplicates]).sort_index(kind="stable").reset_index(drop=True)
    return df
