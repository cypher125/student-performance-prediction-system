"""Draw the Chapter 3 diagrams: architecture, use cases, flowchart and ERD.

Run from the backend folder:  python -m tools.diagrams
Writes PNGs to reports/figures/diagram_*.png. They describe the system as built.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon  # noqa: E402

from ml import plotstyle as ps  # noqa: E402

INK, INK2, LINE = ps.INK, ps.INK_SECONDARY, "#9a998f"
TINTS = {"blue": ("#eef4fc", "#2a78d6"), "orange": ("#fdf1ea", "#eb6834"), "green": ("#e9f6f0", "#1baf7a"),
         "grey": ("#f3f2ee", "#898781")}


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w * 10)
    ax.set_ylim(0, h * 10)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text="", fill="white", edge=LINE, size=9.0, weight="normal", radius=1.2, color=INK, lw=1.0, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                                facecolor=fill, edgecolor=edge, linewidth=lw, zorder=z))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, fontweight=weight,
                color=color, zorder=3, wrap=True)


def arrow(ax, start, end, text="", both=False, size=8, style="-|>", rad=0.0, color=INK2):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=("<|-|>" if both else style), mutation_scale=11,
                                 color=color, linewidth=1.1, zorder=1, connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=2, shrinkB=2))
    if text:
        ax.text((start[0] + end[0]) / 2 + 1, (start[1] + end[1]) / 2, text, fontsize=size, color=INK2,
                ha="left", va="center", zorder=4, bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})


def save(fig, name):
    return ps.save(fig, name)


def architecture():
    fig, ax = canvas(12, 9.4)
    tiers = [
        (66, "Presentation Layer: Next.js web interface (React, TypeScript, Tailwind CSS, Recharts)", "blue",
         ["Sign-in", "Dashboards", "Students &\nprofiles", "Records &\nCSV upload", "Alerts &\ninterventions",
          "Reports", "Model &\nretraining", "User\naccounts"]),
        (34, "Application Layer: FastAPI REST API (Python)", "orange",
         ["Authentication\n& role checks", "Validation &\nCSV import", "Preprocessing\npipeline",
          "Random Forest\nmodel", "SHAP\nexplainer", "Recommendation\nengine", "Alert\nengine",
          "Reports &\nretraining"]),
        (4, "Database Layer: SQLite through SQLAlchemy (PostgreSQL-ready)", "green",
         ["Student", "Academic\nRecord", "Prediction", "Alert", "User"]),
    ]
    for y, title, tint, parts in tiers:
        fill, edge = TINTS[tint]
        box(ax, 4, y, 112, 24, fill=fill, edge=edge, radius=2, lw=1.4)
        ax.text(7, y + 20.5, title, fontsize=10.5, fontweight="semibold", color=INK, va="center")
        n = len(parts)
        width = (106 - (n - 1) * 2) / n
        for i, part in enumerate(parts):
            box(ax, 7 + i * (width + 2), y + 3, width, 12, part, size=7.0 if n > 6 else 8.6)
    for x, label in ((30, "Administrator"), (60, "Lecturer / Adviser"), (90, "Student")):
        box(ax, x - 10, 95, 20, 5.5, label, fill="white", edge=TINTS["blue"][1], size=9)
        arrow(ax, (x, 95), (x, 90))
    ax.text(60, 103, "Users sign in with a web browser", ha="center", fontsize=9, color=INK2)
    arrow(ax, (60, 66), (60, 58), "HTTPS requests and JSON responses (session cookie)", both=True)
    arrow(ax, (60, 34), (60, 28), "SQL through the ORM", both=True)
    ax.set_xlim(0, 128)
    box(ax, 4, -8, 112, 9.5, "Offline training pipeline (backend/ml): prepare data → tune and compare 6 algorithms → "
        "evaluate → SHAP\nsaves model.joblib and model_meta.json, which the Application Layer loads",
        fill=TINTS["grey"][0], edge=TINTS["grey"][1], size=8.6)
    ax.plot([116, 120, 120], [-3.25, -3.25, 46], color=INK2, lw=1.1, zorder=1)
    arrow(ax, (120, 46), (116, 46))
    ax.text(121, 20, "trained\nmodel", fontsize=8, color=INK2, va="center")
    ax.set_ylim(-9, 106)
    return save(fig, "diagram_system_architecture")


def stick(ax, x, y, label):
    ax.add_patch(Circle((x, y + 9), 2, fill=False, color=INK, lw=1.3))
    ax.plot([x, x], [y + 7, y + 1.5], color=INK, lw=1.3)
    ax.plot([x - 3, x + 3], [y + 5.2, y + 5.2], color=INK, lw=1.3)
    ax.plot([x, x - 2.6], [y + 1.5, y - 2.5], color=INK, lw=1.3)
    ax.plot([x, x + 2.6], [y + 1.5, y - 2.5], color=INK, lw=1.3)
    ax.text(x, y - 5, label, ha="center", va="top", fontsize=9.5, fontweight="semibold")


def use_cases():
    fig, ax = canvas(12, 10)
    box(ax, 28, 3, 64, 94, fill="#fbfbf9", edge=LINE, radius=2, z=0.5)
    ax.text(60, 94, "Student Performance Prediction System", ha="center", fontsize=11, fontweight="semibold")
    cases = {
        "signin": (60, 87, "Sign in / change password"),
        "dash": (60, 79, "View dashboard"),
        "upload": (60, 71, "Upload records (CSV)"),
        "manual": (60, 63, "Enter a record manually"),
        "register": (60, 55, "Register a student"),
        "predict": (60, 47, "View predictions and SHAP explanations"),
        "alerts": (60, 39, "Manage alerts and record interventions"),
        "reports": (60, 31, "Generate and export reports"),
        "own": (60, 23, "View own prediction and recommendations"),
        "retrain": (60, 15, "Retrain the prediction model"),
        "users": (60, 7, "Manage user accounts"),
    }
    for x, y, label in cases.values():
        ax.add_patch(Ellipse((x, y), 50, 6.2, facecolor="white", edgecolor=TINTS["blue"][1], lw=1.2, zorder=2))
        ax.text(x, y, label, ha="center", va="center", fontsize=8.8, zorder=3)
    actors = {"lecturer": (12, 62, "Lecturer /\nAdviser"), "admin": (108, 30, "Administrator"),
              "student": (12, 18, "Student")}
    for x, y, label in actors.values():
        stick(ax, x, y, label)
    links = {
        "lecturer": ["signin", "dash", "upload", "manual", "register", "predict", "alerts", "reports"],
        "student": ["signin", "dash", "own"],
        "admin": ["signin", "dash", "upload", "register", "predict", "reports", "retrain", "users"],
    }
    for actor, names in links.items():
        ax_, ay, _ = actors[actor]
        for name in names:
            cx, cy, _ = cases[name]
            edge_x = cx - 25 if ax_ < cx else cx + 25
            ax.plot([ax_ + (3.5 if ax_ < cx else -3.5), edge_x], [ay + 5, cy], color=LINE, lw=0.9, zorder=1.5)
    ax.text(108, 12, "The administrator can also\ndo everything a lecturer can.", ha="center", fontsize=8, color=INK2)
    return save(fig, "diagram_use_cases")


def flowchart():
    fig, ax = canvas(9, 15.5)
    cx = 45
    steps = [
        ("start", 148, "Start"),
        ("io", 136, "Lecturer uploads a CSV file\nor enters a record by hand"),
        ("proc", 124, "Validate each record\n(labels, ranges, known student)"),
        ("dec", 110, "Valid?"),
        ("proc", 96, "Save the academic record"),
        ("dec", 82, "Results (GPA)\nalready known?"),
        ("proc", 68, "Preprocess: fill gaps,\nencode level"),
        ("proc", 56, "Random Forest estimates the\nprobability of each class"),
        ("proc", 44, "Risk level from probability of Fail\n(High >= 0.50, Medium >= 0.25)"),
        ("proc", 32, "SHAP explanation and\npersonalised recommendations"),
        ("dec", 18, "High or\nMedium risk?"),
        ("proc", 4, "Show prediction, explanation and\nadvice on the dashboards"),
        ("start", -8, "End"),
    ]
    for kind, y, text in steps:
        if kind == "dec":
            ax.add_patch(Polygon([(cx, y + 6.5), (cx + 15, y), (cx, y - 6.5), (cx - 15, y)], closed=True,
                                 facecolor=TINTS["orange"][0], edgecolor=TINTS["orange"][1], lw=1.2, zorder=2))
            ax.text(cx, y, text, ha="center", va="center", fontsize=8.6, zorder=3)
        elif kind == "start":
            box(ax, cx - 10, y - 3.5, 20, 7, text, fill=TINTS["green"][0], edge=TINTS["green"][1], radius=3.4, size=9,
                weight="semibold")
        elif kind == "io":
            ax.add_patch(Polygon([(cx - 19, y - 4.5), (cx + 22, y - 4.5), (cx + 19, y + 4.5), (cx - 22, y + 4.5)],
                                 closed=True, facecolor=TINTS["blue"][0], edgecolor=TINTS["blue"][1], lw=1.2, zorder=2))
            ax.text(cx, y, text, ha="center", va="center", fontsize=8.6, zorder=3)
        else:
            box(ax, cx - 19, y - 4.5, 38, 9, text, fill="white", edge=LINE, size=8.6)
    heights = {"start": 3.5, "io": 4.5, "proc": 4.5, "dec": 6.5}
    for (k1, y1, _), (k2, y2, _) in zip(steps, steps[1:]):
        arrow(ax, (cx, y1 - heights[k1]), (cx, y2 + heights[k2]))
    ax.text(cx + 1.5, 101.5, "Yes", fontsize=8, color=INK2)
    ax.text(cx + 1.5, 73.5, "No", fontsize=8, color=INK2)
    ax.text(cx + 1.5, 9.5, "No", fontsize=8, color=INK2)
    # side branches
    box(ax, 66, 105.5, 22, 9, "Report the row\nand the problem", fill="#fdecec", edge=ps.TOWARD, size=8.4)
    arrow(ax, (cx + 15, 110), (66, 110)); ax.text(cx + 17, 111.2, "No", fontsize=8, color=INK2)
    box(ax, 66, 77.5, 22, 9, "Keep as history\n(used to retrain)", fill="white", edge=LINE, size=8.4)
    arrow(ax, (cx + 15, 82), (66, 82)); ax.text(cx + 17, 83.2, "Yes", fontsize=8, color=INK2)
    box(ax, 66, 13.5, 22, 9, "Raise an alert\nfor the adviser", fill="#fdecec", edge=ps.TOWARD, size=8.4)
    arrow(ax, (cx + 15, 18), (66, 18)); ax.text(cx + 17, 19.2, "Yes", fontsize=8, color=INK2)
    arrow(ax, (77, 13.5), (cx + 19, 4))
    ax.set_ylim(-14, 154)
    return save(fig, "diagram_flowchart")


ROW = 3.8


def entity(ax, x, y, name, rows, width=24):
    h = ROW * (len(rows) + 1)
    box(ax, x, y - h, width, h, fill="white", edge=TINTS["blue"][1], radius=0.8, lw=1.2)
    ax.add_patch(FancyBboxPatch((x, y - ROW), width, ROW, boxstyle="round,pad=0,rounding_size=0.8",
                                facecolor=TINTS["blue"][1], edgecolor=TINTS["blue"][1], zorder=3))
    ax.text(x + width / 2, y - ROW / 2, name, ha="center", va="center", color="white", fontsize=9.5,
            fontweight="semibold", zorder=4)
    for i, (field, key) in enumerate(rows):
        yy = y - ROW * (i + 1.5)
        tag = {"pk": "PK ", "fk": "FK ", "": ""}[key]
        ax.text(x + 1.2, yy, f"{tag}{field}", va="center", fontsize=7.8, zorder=4,
                color=TINTS["blue"][1] if key == "fk" else INK, fontweight="semibold" if key == "pk" else "normal")
    return (x, y, width, h)


def erd():
    fig, ax = canvas(13, 10.2)
    entity(ax, 2, 98, "ACADEMIC_RECORD", [
        ("record_id", "pk"), ("student_id", "fk"), ("level", ""), ("session", ""), ("semester", ""),
        ("attendance_pct", ""), ("ca_score", ""), ("assignment_score", ""), ("prior_gpa", ""),
        ("exam_score (after results)", ""), ("gpa (after results)", ""), ("performance_class", "")], width=27)
    entity(ax, 52, 98, "STUDENT", [
        ("student_id", "pk"), ("student_code", ""), ("matric_number", ""), ("first_name", ""), ("last_name", ""),
        ("department", ""), ("programme", ""), ("level", ""), ("session", "")])
    entity(ax, 101, 98, "PREDICTION", [
        ("prediction_id", "pk"), ("student_id", "fk"), ("record_id", "fk"), ("predicted_class", ""),
        ("confidence_score", ""), ("fail_probability", ""), ("risk_level", ""), ("explanation", ""),
        ("recommendations", ""), ("model_version", ""), ("created_at", "")], width=27)
    entity(ax, 52, 40, "USER", [
        ("user_id", "pk"), ("username", ""), ("email", ""), ("password_hash", ""), ("role", ""),
        ("student_id (students only)", "fk"), ("last_login", ""), ("created_at", "")], width=27)
    entity(ax, 101, 40, "ALERT", [
        ("alert_id", "pk"), ("prediction_id", "fk"), ("alert_type", ""), ("message", ""), ("status", ""),
        ("sent_at", ""), ("acknowledged_at", ""), ("acknowledged_by", "fk"), ("action_taken", "")], width=27)

    def link(p1, p2, l1, l2, label="", label_x=None):
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=INK2, lw=1.1, zorder=1)
        style = {"color": ps.TOWARD, "fontsize": 9, "fontweight": "bold"}
        if p1[0] == p2[0]:  # vertical: cardinalities beside the line, just outside each box
            ax.text(p1[0] + 1.2, p1[1] - 3.2, l1, **style)
            ax.text(p2[0] + 1.2, p2[1] + 1.0, l2, **style)
        else:
            ax.text(p1[0] + (1.5 if p2[0] >= p1[0] else -3), p1[1] + 1.2, l1, **style)
            ax.text(p2[0] + (-3 if p2[0] >= p1[0] else 1.5), p2[1] + 1.2, l2, **style)
        if label:
            x = label_x if label_x is not None else (p1[0] + p2[0]) / 2
            ax.text(x, (p1[1] + p2[1]) / 2 - 2.5, label, ha="center", fontsize=7.6, color=INK2)

    link((52, 90), (29, 90), "1", "N", "has semester records")
    link((76, 90), (101, 90), "1", "N", "receives predictions")
    link((29, 56), (101, 56), "1", "N", "is scored by", label_x=44)
    link((114.5, 52.4), (114.5, 40), "1", "1", "")
    ax.text(116, 46, "raises (only at High\nor Medium risk)", fontsize=7.6, color=INK2)
    link((65.5, 60), (65.5, 40), "1", "0..1", "")
    ax.text(67, 49, "a student's own\naccount", fontsize=7.6, color=INK2)
    link((79, 24), (101, 24), "1", "N", "acknowledges")
    ax.text(2, 44, "PK = primary key\nFK = foreign key\n1 / N = one / many\n0..1 = optional\n\n"
            "exam_score and gpa stay empty\nuntil results are released;\npredictions use only the\nother fields.",
            fontsize=8, color=INK2, va="top")
    ax.set_ylim(0, 102)
    return save(fig, "diagram_erd")


def main():
    ps.apply()
    for draw in (architecture, use_cases, flowchart, erd):
        print("saved", draw())


if __name__ == "__main__":
    main()
