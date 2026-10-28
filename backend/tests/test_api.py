"""API tests (3.18): authentication, access control, prediction, upload validation and alerts."""
import pytest
from fastapi.testclient import TestClient

from app import models as m
from app.db import SessionLocal, create_tables
from app.main import app
from app.security import hash_password
from app.settings import get_settings

PASSWORD = "Password@123"


@pytest.fixture(scope="module")
def client():
    create_tables()
    settings = get_settings()
    with SessionLocal() as db:
        if not db.get(m.User, 1):
            ada = m.Student(student_code="S0001", matric_number="SIM/ND/24/0001", first_name="Ada", last_name="Obi",
                            programme="ND", level="ND2", session=settings.current_session, entry_session="2024/2025")
            tunde = m.Student(student_code="S0002", matric_number="SIM/ND/24/0002", first_name="Tunde",
                              last_name="Bello", programme="ND", level="ND2", session=settings.current_session,
                              entry_session="2024/2025")
            db.add_all([ada, tunde])
            db.flush()
            db.add(m.AcademicRecord(student_id=ada.id, level="ND1", session="2024/2025", semester="Second",
                                    attendance_pct=80, ca_score=60, assignment_score=65, prior_gpa=2.5,
                                    exam_score=55, gpa=2.75, performance_class="Pass", source="seed"))
            db.add_all([
                m.User(username="admin", full_name="Admin", role="admin", password_hash=hash_password(PASSWORD)),
                m.User(username="lecturer", full_name="Lecturer", role="lecturer",
                       password_hash=hash_password(PASSWORD)),
                m.User(username="s0001", full_name="Ada Obi", role="student", student_id=ada.id,
                       password_hash=hash_password(PASSWORD)),
            ])
            db.commit()
    with TestClient(app) as test_client:
        yield test_client


def login(client, username):
    client.cookies.clear()
    response = client.post("/api/auth/login", json={"username": username, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()


def test_health_reports_the_loaded_model(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["model_version"]


def test_wrong_password_is_rejected(client):
    client.cookies.clear()
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_signed_out_requests_are_refused(client):
    client.cookies.clear()
    assert client.get("/api/students").status_code == 401


def test_login_sets_an_httponly_session_cookie(client):
    client.cookies.clear()
    response = client.post("/api/auth/login", json={"username": "lecturer", "password": PASSWORD})
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert client.get("/api/auth/me").json()["role"] == "lecturer"


def test_manual_entry_returns_prediction_explanation_and_advice(client):
    login(client, "lecturer")
    settings = get_settings()
    response = client.post("/api/records", json={
        "student_code": "S0001", "level": "ND2", "session": settings.current_session,
        "semester": settings.current_semester, "attendance_pct": 45, "ca_score": 30, "assignment_score": 25})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["record"]["prior_gpa"] == 2.75  # filled from the previous semester's result
    prediction = body["prediction"]
    assert prediction["predicted_class"] in {"Distinction", "Merit", "Pass", "Fail"}
    assert abs(sum(prediction["probabilities"].values()) - 1) < 0.01
    assert prediction["risk_level"] == "High"  # very low attendance, CA and assignments
    assert {e["feature"] for e in prediction["explanation"]} >= {"attendance_pct", "ca_score"}
    assert any(r["audience"] == "student" for r in prediction["recommendations"])
    alerts = client.get("/api/alerts").json()["alerts"]
    assert any(a["student"]["code"] == "S0001" and a["status"] == "New" for a in alerts)


def test_invalid_manual_entry_names_the_field(client):
    login(client, "lecturer")
    response = client.post("/api/records", json={
        "student_code": "S0002", "level": "ND9", "session": "2025/2026", "semester": "First",
        "attendance_pct": 80, "ca_score": 60, "assignment_score": 60})
    assert response.status_code == 422
    assert response.json()["detail"]["field"] == "level"


def test_csv_upload_reports_each_bad_row(client):
    login(client, "lecturer")
    csv = ("student_code,level,session,semester,attendance_pct,ca_score,assignment_score,prior_gpa\n"
           "S0002,nd 2,2025/26,1st,85,70,72,3.1\n"        # messy labels are understood
           "S9999,ND2,2025/2026,First,85,70,72,3.1\n"     # unknown student
           "S0002,ND2,2025/2026,First,150,70,72,3.1\n")   # attendance out of range
    response = client.post("/api/records/upload", files={"file": ("records.csv", csv, "text/csv")})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rows_accepted"] == 1 and body["rows_rejected"] == 2
    assert {(e["row"], e["field"]) for e in body["errors"]} == {(3, "student_code"), (4, "attendance_pct")}
    assert body["predictions_made"] == 1


def test_students_cannot_see_staff_pages_or_other_students(client):
    login(client, "s0001")
    assert client.get("/api/students").status_code == 403
    assert client.get("/api/students/S0002").status_code == 403
    assert client.get("/api/students/S0001").status_code == 200
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["role"] == "student" and dashboard["student"]["code"] == "S0001"


def test_alert_workflow_records_the_intervention(client):
    login(client, "lecturer")
    alert = client.get("/api/alerts", params={"alert_status": "New"}).json()["alerts"][0]
    resolve_too_early = client.patch(f"/api/alerts/{alert['id']}", json={"status": "Resolved"})
    assert resolve_too_early.status_code == 422
    updated = client.patch(f"/api/alerts/{alert['id']}", json={
        "status": "Resolved", "action_taken": "Met the student; agreed a weekly study plan."}).json()
    assert updated["status"] == "Resolved"
    assert updated["acknowledged_by"] == "Lecturer"
    assert updated["action_taken"].startswith("Met the student")


def test_only_admins_manage_users_and_retraining(client):
    login(client, "lecturer")
    assert client.get("/api/users").status_code == 403
    assert client.post("/api/model/retrain").status_code == 403
    login(client, "admin")
    created = client.post("/api/users", json={"username": "adviser2", "full_name": "New Adviser",
                                              "role": "adviser", "password": "Adviser@2026"})
    assert created.status_code == 201, created.text
    assert client.get("/api/users").json()["count"] >= 4


def test_template_download_and_student_registration(client):
    login(client, "lecturer")
    template = client.get("/api/records/template")
    assert template.status_code == 200
    assert template.text.startswith("student_code,level,session,semester")
    body = {"first_name": "Ngozi", "last_name": "Eze", "matric_number": "SIM/ND/25/0999", "level": "ND1",
            "session": "2025/2026"}
    created = client.post("/api/students", json=body)
    assert created.status_code == 201, created.text
    assert created.json()["code"].startswith("S")
    assert client.post("/api/students", json=body).status_code == 409  # same matric number


def test_rescoring_only_scores_records_not_yet_scored(client):
    login(client, "lecturer")
    result = client.post("/api/predictions/run").json()
    assert result["predictions_made"] == 0  # every current record already has a prediction


def test_password_change_requires_the_current_password(client):
    login(client, "s0001")
    wrong = client.post("/api/auth/password", json={"current_password": "nope", "new_password": "NewPass@2026"})
    assert wrong.status_code == 400
    ok = client.post("/api/auth/password", json={"current_password": PASSWORD, "new_password": "NewPass@2026"})
    assert ok.status_code == 200
    client.cookies.clear()
    assert client.post("/api/auth/login", json={"username": "s0001", "password": "NewPass@2026"}).status_code == 200


def test_retraining_refuses_without_enough_results(client):
    import time

    login(client, "admin")
    client.post("/api/model/retrain")
    state = {}
    for _ in range(60):
        state = client.get("/api/model/retrain").json()
        if state["status"] != "running":
            break
        time.sleep(0.5)
    assert state["status"] == "failed"
    assert "At least 200 records" in state["message"]


def test_staff_dashboard_and_reports(client):
    login(client, "lecturer")
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["role"] == "staff"
    assert dashboard["students_assessed"] >= 2
    assert set(dashboard["risk_counts"]) == {"High", "Medium", "Low"}
    summary = client.get("/api/reports/summary").json()
    assert summary["interventions_recorded"] >= 1
    export = client.get("/api/reports/predictions.csv")
    assert export.status_code == 200
    assert export.text.splitlines()[0].startswith("student_code,matric_number")


def test_times_carry_their_utc_offset(client):
    login(client, "lecturer")
    assert client.get("/api/auth/me").json()["last_login"].endswith("+00:00")


def test_a_repeated_csv_row_is_scored_once(client):
    login(client, "lecturer")
    settings = get_settings()
    row = f"S0002,ND2,{settings.current_session},{settings.current_semester},80,62,66,3.0\n"
    csv = "student_code,level,session,semester,attendance_pct,ca_score,assignment_score,prior_gpa\n" + row + row
    body = client.post("/api/records/upload", files={"file": ("dup.csv", csv, "text/csv")}).json()
    assert body["rows_accepted"] == 2
    assert body["predictions_made"] == 1


def test_old_results_do_not_move_a_student_back_a_level(client):
    login(client, "lecturer")
    csv = ("student_code,level,session,semester,attendance_pct,ca_score,assignment_score,prior_gpa,exam_score,gpa\n"
           "S0002,ND1,2023/2024,First,78,60,64,,55,2.6\n")
    body = client.post("/api/records/upload", files={"file": ("old.csv", csv, "text/csv")}).json()
    assert body["rows_accepted"] == 1 and body["predictions_made"] == 0  # results known: history only
    student = client.get("/api/students/S0002").json()["student"]
    assert student["level"] == "ND2" and student["session"] == get_settings().current_session


def test_a_blank_intervention_cannot_resolve_an_alert(client):
    login(client, "lecturer")
    settings = get_settings()
    client.post("/api/records", json={
        "student_code": "S0002", "level": "ND2", "session": settings.current_session,
        "semester": settings.current_semester, "attendance_pct": 40, "ca_score": 25, "assignment_score": 20})
    alert = client.get("/api/alerts", params={"alert_status": "New"}).json()["alerts"][0]
    response = client.patch(f"/api/alerts/{alert['id']}", json={"status": "Resolved", "action_taken": "   "})
    assert response.status_code == 422


def test_a_duplicate_email_is_a_clear_conflict(client):
    login(client, "admin")
    first = {"username": "adviser3", "full_name": "Adviser Three", "email": "adviser3@yabatech.edu.ng",
             "role": "adviser", "password": "Adviser@2026"}
    assert client.post("/api/users", json=first).status_code == 201
    second = {**first, "username": "adviser4"}
    response = client.post("/api/users", json=second)
    assert response.status_code == 409
    assert "email" in response.json()["detail"]


def test_an_admin_resets_a_forgotten_password_but_cannot_disable_themselves(client):
    admin = login(client, "admin")
    created = client.post("/api/users", json={"username": "adviser5", "full_name": "Adviser Five",
                                              "role": "adviser", "password": "Adviser@2026"}).json()
    assert client.patch(f"/api/users/{created['id']}", json={"password": "short"}).status_code == 422
    assert client.patch(f"/api/users/{created['id']}", json={"password": "Temporary@2026"}).status_code == 200
    response = client.patch(f"/api/users/{admin['id']}", json={"is_active": False})
    assert response.status_code == 400
    assert "your own account" in response.json()["detail"]
    client.cookies.clear()
    assert client.post("/api/auth/login", json={"username": "adviser5", "password": "Adviser@2026"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "adviser5", "password": "Temporary@2026"}).status_code == 200


def _open_alerts_for(client, code):
    return [a for a in client.get("/api/alerts").json()["alerts"]
            if a["student"]["code"] == code and a["status"] != "Resolved"]


def test_rescoring_keeps_one_alert_and_closes_it_when_risk_drops(client):
    login(client, "lecturer")
    settings = get_settings()
    record = {"student_code": "S0002", "level": "ND2", "session": settings.current_session,
              "semester": settings.current_semester}
    client.post("/api/records", json={**record, "attendance_pct": 40, "ca_score": 25, "assignment_score": 20})
    client.post("/api/records", json={**record, "attendance_pct": 42, "ca_score": 24, "assignment_score": 22})
    assert len(_open_alerts_for(client, "S0002")) == 1  # re-scored, not duplicated
    client.post("/api/records", json={**record, "attendance_pct": 97, "ca_score": 88, "assignment_score": 92,
                                      "prior_gpa": 3.9})
    assert _open_alerts_for(client, "S0002") == []
    closed = [a for a in client.get("/api/alerts", params={"alert_status": "Resolved"}).json()["alerts"]
              if a["student"]["code"] == "S0002"]
    assert any("Closed automatically" in (a["action_taken"] or "") for a in closed)


def test_updating_a_finished_semester_keeps_its_results(client):
    login(client, "lecturer")
    body = client.post("/api/records", json={
        "student_code": "S0001", "level": "ND1", "session": "2024/2025", "semester": "Second",
        "attendance_pct": 81, "ca_score": 61, "assignment_score": 66}).json()
    assert body["record"]["gpa"] == 2.75 and body["record"]["has_results"]
    assert body["prediction"] is None  # a finished semester is not scored again


def test_previous_gpa_fills_from_an_earlier_row_in_the_same_file(client):
    login(client, "lecturer")
    code = client.post("/api/students", json={"first_name": "Kemi", "last_name": "Ade", "matric_number": "SIM/ND/24/0777",
                                              "level": "ND2", "session": "2025/2026"}).json()["code"]
    csv = ("student_code,level,session,semester,attendance_pct,ca_score,assignment_score,prior_gpa,exam_score,gpa\n"
           f"{code},ND1,2024/2025,First,85,70,72,,65,3.1\n"
           f"{code},ND1,2024/2025,Second,80,60,64,,52,2.4\n"
           f"{code},ND2,2025/2026,First,78,58,61,,,\n")
    assert client.post("/api/records/upload", files={"file": ("t.csv", csv, "text/csv")}).json()["rows_accepted"] == 3
    records = {(r["session"], r["semester"]): r for r in client.get(f"/api/students/{code}").json()["records"]}
    assert records[("2024/2025", "Second")]["prior_gpa"] == 3.1
    assert records[("2025/2026", "First")]["prior_gpa"] == 2.4


def test_students_never_see_the_staff_notes_or_next_step(client):
    login(client, "admin")
    assert client.post("/api/users", json={"username": "s0002", "full_name": "Tunde Bello", "role": "student",
                                           "password": PASSWORD, "student_code": "S0002"}).status_code == 201
    login(client, "lecturer")
    settings = get_settings()
    client.post("/api/records", json={
        "student_code": "S0002", "level": "ND2", "session": settings.current_session,
        "semester": settings.current_semester, "attendance_pct": 45, "ca_score": 30, "assignment_score": 25})
    alert = next(a for a in client.get("/api/alerts").json()["alerts"]
                 if a["student"]["code"] == "S0002" and a["status"] != "Resolved")
    client.patch(f"/api/alerts/{alert['id']}", json={"status": "Acknowledged", "action_taken": "Private staff note."})
    login(client, "s0002")
    for alerts in (client.get("/api/alerts").json()["alerts"], client.get("/api/dashboard").json()["alerts"],
                   client.get("/api/students/S0002").json()["alerts"]):
        assert alerts
        assert all(a["action_taken"] is None and a["acknowledged_by"] is None for a in alerts)
    predictions = (client.get("/api/dashboard").json()["latest_prediction"],
                   *client.get("/api/students/S0002").json()["predictions"])
    assert all(r["audience"] == "student" for p in predictions for r in p["recommendations"])


def test_the_summary_counts_this_semesters_staff_interventions(client):
    login(client, "lecturer")
    settings = get_settings()
    alerts = client.get("/api/alerts").json()["alerts"]
    written_by_staff = [a for a in alerts if a["session"] == settings.current_session
                        and a["semester"] == settings.current_semester and a["action_taken"]
                        and not a["action_taken"].startswith("Closed automatically")]
    assert client.get("/api/reports/summary").json()["interventions_recorded"] == len(written_by_staff)
