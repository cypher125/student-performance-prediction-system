"""Personalised recommendations (objective 6), driven by each prediction's SHAP explanation.

Only factors that raise the student's risk of failing produce advice, largest first,
so the advice always matches the explanation the student and adviser can see.
"""
ATTENDANCE_MINIMUM = 75  # the usual minimum attendance for sitting examinations
LOW_SCORE = 50
LOW_GPA = 2.0
MAX_STUDENT_ADVICE = 3

STAFF_ACTION = {
    "High": "Book an intervention meeting with the student within a week and agree a study plan with the "
            "course lecturers.",
    "Medium": "Check in with the student after the next CA test and follow up on any missed lectures or "
              "assignments.",
    "Low": "No intervention needed; keep monitoring as new CA scores arrive.",
}


def _advice(feature, value):
    if feature == "attendance_pct":
        if value is None:
            return "Your attendance has not been recorded yet. Confirm it with your course adviser and attend every lecture."
        if value < ATTENDANCE_MINIMUM:
            return (f"Your attendance is {value:.0f}%, below the {ATTENDANCE_MINIMUM}% usually required to sit "
                    "examinations. Attend every remaining lecture and explain any absences to your course adviser.")
        return f"Your attendance ({value:.0f}%) is holding your prediction back. Aim for full attendance this semester."
    if feature == "ca_score":
        if value is None:
            return "Your CA scores are missing. Check with your lecturers that every test has been recorded."
        if value < LOW_SCORE:
            return (f"Your average CA score is {value:.0f}%. Join a tutorial or study group for your weakest courses "
                    "and ask lecturers for feedback on your tests.")
        return f"Raising your CA average ({value:.0f}%) would improve your prediction. Prepare early for the next test."
    if feature == "assignment_score":
        if value is None:
            return "Some assignment scores are missing. Submit every assignment on time; a missed one counts as zero."
        if value < LOW_SCORE:
            return (f"Your assignments average {value:.0f}%. Submit every remaining assignment on time and use the "
                    "feedback to improve.")
        return f"Your assignment average ({value:.0f}%) could be higher. Start each assignment early."
    if feature == "prior_gpa":
        if value is None:
            return "As a new student, make use of the department's orientation and peer-mentoring support."
        if value < LOW_GPA:
            return (f"Your previous GPA was {value:.2f}, below 2.00. Meet your academic adviser to plan this "
                    "semester and clear any carry-over courses.")
        return (f"Your previous GPA ({value:.2f}) shows some courses need more attention. Review last semester's "
                "weakest courses.")
    return None  # level is not something a student can change


def recommend(explanation, risk_level):
    """Advice for the student (from risk-raising factors) and the next step for staff."""
    advice = []
    for item in explanation:
        if item["contribution"] <= 0 or len(advice) >= MAX_STUDENT_ADVICE:
            continue
        text = _advice(item["feature"], item["value"])
        if text:
            advice.append({"audience": "student", "factor": item["label"], "text": text})
    if not advice:
        advice.append({"audience": "student", "factor": "Overall",
                       "text": "Your records point to a good result. Keep up your attendance and study habits."})
    advice.append({"audience": "staff", "factor": "Next step", "text": STAFF_ACTION[risk_level]})
    return advice
