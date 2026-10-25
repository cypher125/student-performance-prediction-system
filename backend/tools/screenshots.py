"""Capture every screen for Chapter 4 with headless Microsoft Edge.

Run from the backend folder (no server needs to be running):  python -m tools.screenshots
For each role it starts the app on port 8010 with SAPPS_DEMO_AUTO_LOGIN set (a local-only
switch that signs every request in as that user), captures the pages, then stops it.
Writes PNGs to reports/screenshots/.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

from sqlalchemy import select

from app import models as m
from app.db import SessionLocal
from app.queries import latest_predictions
from ml import config

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 8010
BASE = f"http://127.0.0.1:{PORT}"
OUT = config.REPORTS_DIR / "screenshots"
WIDTH = 1440


def flagged_student():
    """The highest-risk current student who also has past results, so the profile shows a GPA trend."""
    with SessionLocal() as db:
        with_history = [p for p in latest_predictions(db)
                        if sum(r.gpa is not None for r in p.student.records) >= 2]
        top = max(with_history, key=lambda p: p.fail_probability)
        return top.student.student_code


def wait_until_up(timeout=180):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/health", timeout=3) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(2)
    raise RuntimeError("The server did not start in time.")


def capture(name, path, height, profile):
    target = OUT / f"{name}.png"
    try:
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                        f"--user-data-dir={profile}", f"--window-size={WIDTH},{height}",
                        "--virtual-time-budget=20000", f"--screenshot={target}", BASE + path],
                       check=True, timeout=180, capture_output=True)
    except subprocess.TimeoutExpired:
        # /docs loads Swagger UI from the internet; skip a page rather than abort the whole run.
        print(f"  skipped {name}: timed out (no internet?); the previous screenshot is kept", flush=True)
        return
    print("  saved", target.relative_to(config.PROJECT_DIR), flush=True)


def run_role(username, pages):
    env = {**os.environ, "SAPPS_DEMO_AUTO_LOGIN": username}
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
                              env=env, cwd=config.BACKEND_DIR, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    profile = tempfile.mkdtemp(prefix="edge-shots-")
    try:
        wait_until_up()
        print(f"Signed in as {username}:", flush=True)
        for name, path, height in pages:
            capture(name, path, height, profile)
    finally:
        server.terminate()
        server.wait(timeout=30)
        shutil.rmtree(profile, ignore_errors=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    code = flagged_student()
    with SessionLocal() as db:
        student_user = db.scalar(select(m.User).join(m.Student).where(m.Student.student_code == code))
    run_role("lecturer", [
        ("01_login", "/login/", 900),
        ("02_dashboard_staff", "/dashboard/", 1500),
        ("03_students", "/students/", 1250),
        ("04_student_profile", f"/students/view/?code={code}", 2000),
        ("05_records", "/records/", 1150),
        ("06_alerts", "/alerts/", 1300),
        ("07_reports", "/reports/", 1050),
        ("08_model", "/model/", 1350),
        ("11_api_docs", "/docs", 1500),
    ])
    run_role("admin", [("09_users", "/users/", 1150)])
    run_role(student_user.username, [("10_dashboard_student", "/dashboard/", 1900)])


if __name__ == "__main__":
    main()
