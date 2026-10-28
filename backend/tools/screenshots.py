"""Capture the system's screens for Chapter 4 and for the presentation PDFs.

Run from the backend folder with any Python that has Playwright (Microsoft Edge is used,
so no browser download is needed):
    python tools/screenshots.py              # reseed, capture everything, reseed again
    python tools/screenshots.py --no-reset   # capture the database as it is

It starts the API on port 8010 with the project's own virtual environment, signs in through
the real sign-in form as each role, and saves:
  reports/screenshots/NN_*.png           full pages for Chapter 4 (1440 px wide)
  docs/presentation/src/screens/*.png    pages and single cards for the PDFs (1.5x pixel density)
  docs/presentation/src/screens/index.json  each image's size and the position of every card
                                          on it, in CSS pixels, for cropping in the documents
Uploads, manual entries and interventions change the demo data, so the database is reseeded
before and after the run.
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
PROJECT = BACKEND.parent
VENV_PY = BACKEND / ".venv" / "Scripts" / "python.exe"
CH4 = PROJECT / "reports" / "screenshots"
DOCS = PROJECT / "docs" / "presentation" / "src" / "screens"
PORT = 8010
BASE = f"http://127.0.0.1:{PORT}"
WIDTH = 1440
MAX_PAGE_HEIGHT = 2000  # CSS pixels; longer pages are cut here
PASSWORDS = {"admin": "Admin@2026", "lecturer": "Lecturer@2026", "adviser": "Adviser@2026"}
STUDENT_PASSWORD = "Student@2026"
DEMO_STUDENT = "S0379"  # David Aliyu: high risk, with a year of results for the GPA chart

INDEX = {}


def reseed():
    print("Reseeding the demo database…", flush=True)
    subprocess.run([str(VENV_PY), "-m", "app.seed", "--reset"], cwd=BACKEND, check=True,
                   stdout=subprocess.DEVNULL)


def wait_until_up(timeout=240):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/health", timeout=3) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(2)
    raise RuntimeError("The server did not start in time.")


def regions(page):
    """Every card (section) and the page header, with their boxes in CSS pixels."""
    return page.evaluate("""() => {
        const out = [];
        const add = (el, label) => {
            const r = el.getBoundingClientRect();
            if (r.width < 40 || r.height < 20) return;
            out.push({label, x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY),
                      w: Math.round(r.width), h: Math.round(r.height)});
        };
        document.querySelectorAll('main section, main form, main table, aside, header').forEach(el => {
            const h = el.querySelector('h1, h2, summary, th');
            add(el, (el.tagName.toLowerCase() + ': ' + (h ? h.innerText : el.innerText).trim().split('\\n')[0]).slice(0, 80));
        });
        document.querySelectorAll('main h1').forEach(h => add(h, 'title: ' + h.innerText.trim()));
        return out;
    }""")


def settle(page, text=None):
    page.wait_for_load_state("networkidle")
    if text:
        page.get_by_text(text, exact=False).first.wait_for(timeout=30000)
    page.wait_for_timeout(600)


def page_clip(page):
    """The whole page, cut at MAX_PAGE_HEIGHT: long lists (students, alerts) only need their top."""
    size = page.evaluate("() => ({w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})")
    return {"x": 0, "y": 0, "width": size["w"], "height": min(size["h"], MAX_PAGE_HEIGHT)}


def full(page, name, ch4=None):
    """Full page for the documents (and, with ch4, a 1x copy for Chapter 4)."""
    target = DOCS / f"{name}.png"
    clip = page_clip(page)
    page.screenshot(path=str(target), full_page=True, clip=clip)
    boxes = [r for r in regions(page) if r["y"] < clip["height"]]
    for r in boxes:
        r["h"] = min(r["h"], clip["height"] - r["y"])
    INDEX[name] = {"file": target.name, "css_width": clip["width"], "css_height": clip["height"], "regions": boxes}
    print("  saved", target.relative_to(PROJECT), flush=True)
    if ch4:
        ch4.screenshot(path=str(CH4 / f"{name_ch4(name)}.png"), full_page=True, clip=page_clip(ch4))


def name_ch4(name):
    return CH4_NAMES[name]


CH4_NAMES = {
    "login": "01_login", "staff-dashboard": "02_dashboard_staff", "students": "03_students",
    "student-profile": "04_student_profile", "records": "05_records", "alerts": "06_alerts",
    "reports": "07_reports", "model": "08_model", "users": "09_users",
    "student-dashboard": "10_dashboard_student", "api-docs": "11_api_docs",
}


def card(page, title, name, note=""):
    """One card, found by its heading."""
    locator = page.locator("section").filter(has=page.get_by_role("heading", name=title, exact=True)).first
    locator.scroll_into_view_if_needed()
    target = DOCS / f"{name}.png"
    locator.screenshot(path=str(target))
    box = locator.bounding_box()
    INDEX[name] = {"file": target.name, "css_width": round(box["width"]), "css_height": round(box["height"]),
                   "card": title, "note": note}
    print("  saved", target.relative_to(PROJECT), flush=True)


class Session:
    """A signed-in browser for one role, with a 1x twin for the Chapter 4 copies."""

    def __init__(self, browser, username, password, dsf=1.5, viewport=(WIDTH, 900)):
        self.ctx = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]}, device_scale_factor=dsf)
        self.page = self.ctx.new_page()
        self.username, self.password = username, password

    def login(self, ch4=None):
        page = self.page
        page.goto(f"{BASE}/login/")
        settle(page, "Use the username and password")
        if ch4 is not None:
            full(page, "login", ch4=ch4)
        page.get_by_label("Username").fill(self.username)
        page.get_by_label("Password").fill(self.password)
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url(lambda url: "/dashboard" in url, timeout=60000)
        settle(page)

    def go(self, path, text=None):
        self.page.goto(BASE + path)
        settle(self.page, text)
        return self.page

    def close(self):
        self.ctx.close()


def twin(browser, username, password):
    """A 1x session that follows the main one, for Chapter 4's full-page copies."""
    s = Session(browser, username, password, dsf=1)
    s.login()
    return s


def phones(browser):
    """The student's and the lecturer's dashboards on a phone, before the demo upload changes any numbers."""
    print("Phones:", flush=True)
    for username, password, name in ((DEMO_STUDENT.lower(), STUDENT_PASSWORD, "phone-student"),
                                     ("lecturer", PASSWORDS["lecturer"], "phone-staff")):
        phone = Session(browser, username, password, dsf=2, viewport=(390, 844))
        phone.login()
        phone.go("/dashboard/", "Welcome" if username != "lecturer" else "Early-warning dashboard")
        target = DOCS / f"{name}.png"
        phone.page.screenshot(path=str(target), full_page=False)
        INDEX[name] = {"file": target.name, "css_width": 390, "css_height": 844, "note": "phone viewport, top of page"}
        print("  saved", target.relative_to(PROJECT), flush=True)
        phone.close()


def capture_all(browser, skip_api_docs):
    DOCS.mkdir(parents=True, exist_ok=True)
    CH4.mkdir(parents=True, exist_ok=True)
    phones(browser)

    print("Lecturer:", flush=True)
    lec = Session(browser, "lecturer", PASSWORDS["lecturer"])
    lec1 = Session(browser, "lecturer", PASSWORDS["lecturer"], dsf=1)
    lec1.page.goto(f"{BASE}/login/")
    settle(lec1.page, "Use the username and password")
    lec.login(ch4=lec1.page)
    lec1.login()

    def both(path, name, text=None):
        lec.go(path, text)
        lec1.go(path, text)
        full(lec.page, name, ch4=lec1.page)

    both("/dashboard/", "staff-dashboard", "Early-warning dashboard")
    both("/students/", "students", "students")
    both(f"/students/view/?code={DEMO_STUDENT}", "student-profile", "Why this prediction?")
    card(lec.page, "Prediction", "profile-prediction")
    card(lec.page, "Why this prediction?", "profile-why")
    card(lec.page, "Recommendations", "profile-recommendations")
    card(lec.page, "GPA trend", "profile-gpa")
    both("/reports/", "reports", "Summary report")
    both("/model/", "model", "Prediction model")
    lec.go("/account/", "Change password")
    full(lec.page, "account")
    lec.go("/students/", "students")
    lec.page.get_by_label("Risk").select_option("High")
    settle(lec.page)
    full(lec.page, "students-high")

    # Alerts: the list, then one card with the intervention form open (not saved).
    both("/alerts/", "alerts", "Early-warning alerts")
    lec.page.get_by_role("button", name="Record intervention").first.click()
    lec.page.get_by_label("Intervention taken").fill(
        "Met the student on 27 October; agreed a weekly study plan and a place in the CA tutorial group.")
    lec.page.wait_for_timeout(300)
    form_card = lec.page.locator("[data-alert-card]").filter(has=lec.page.get_by_label("Intervention taken")).first
    form_card.screenshot(path=str(DOCS / "alert-intervention.png"))
    box = form_card.bounding_box()
    INDEX["alert-intervention"] = {"file": "alert-intervention.png", "css_width": round(box["width"]),
                                   "css_height": round(box["height"]), "note": "intervention form open, not saved"}
    print("  saved docs/presentation/src/screens/alert-intervention.png", flush=True)

    # Records: the page, a CSV upload with two bad rows, then a manual entry.
    both("/records/", "records", "Upload a CSV file")
    codes = current_codes(lec.page)
    csv_path = BACKEND / "data" / "demo_upload.csv"
    csv_path.write_text(
        "student_code,level,session,semester,attendance_pct,ca_score,assignment_score,prior_gpa\n"
        f"{codes[0]},ND1,2025/2026,First,88,71,74,\n"
        f"{codes[1].lower()},nd 1,2025/26,1st,62,44,41,\n"
        "S9999,ND2,2025/2026,First,80,60,65,2.8\n"
        f"{codes[2]},ND1,2025/2026,First,150,55,60,\n", encoding="utf-8")
    try:
        lec.page.locator("input[type=file]").set_input_files(str(csv_path))
        lec.page.get_by_role("button", name="Upload and predict").click()
        lec.page.get_by_text("rows saved", exact=False).first.wait_for(timeout=120000)
        lec.page.wait_for_timeout(500)
        card(lec.page, "Upload a CSV file", "records-upload-result", note=f"uploaded {csv_path.name}")
    finally:
        csv_path.unlink(missing_ok=True)

    form = lec.page.locator("section").filter(has=lec.page.get_by_role("heading", name="Enter one record", exact=True)).first
    form.get_by_label("Student code").fill(codes[3])
    form.get_by_label("Level").select_option("ND1")
    form.get_by_label("Attendance (%)").fill("58")
    form.get_by_label("CA score (%)").fill("38")
    form.get_by_label("Assignment score (%)").fill("35")
    form.get_by_role("button", name="Save and predict").click()
    lec.page.get_by_role("heading", name="Why this prediction?").first.wait_for(timeout=120000)
    lec.page.wait_for_timeout(600)
    card(lec.page, "Enter one record", "records-manual-result", note=f"manual entry for {codes[3]}")
    lec1.close()
    lec.close()

    print("Administrator:", flush=True)
    adm = Session(browser, "admin", PASSWORDS["admin"])
    adm.login()
    adm1 = twin(browser, "admin", PASSWORDS["admin"])
    adm.go("/users/", "User accounts")
    adm1.go("/users/", "User accounts")
    full(adm.page, "users", ch4=adm1.page)
    adm.go("/model/", "Prediction model")
    full(adm.page, "model-admin")
    if not skip_api_docs:
        try:
            adm.page.goto(f"{BASE}/docs", timeout=60000)
            adm.page.wait_for_selector(".swagger-ui .opblock", timeout=60000)
            adm.page.wait_for_timeout(800)
            adm1.page.goto(f"{BASE}/docs", timeout=60000)
            adm1.page.wait_for_selector(".swagger-ui .opblock", timeout=60000)
            full(adm.page, "api-docs", ch4=adm1.page)
        except Exception as error:  # Swagger UI loads from the internet
            print(f"  skipped api-docs: {error.__class__.__name__} (no internet?)", flush=True)
    adm1.close()
    adm.close()

    print("Student:", flush=True)
    stu = Session(browser, DEMO_STUDENT.lower(), STUDENT_PASSWORD)
    stu.login()
    stu1 = twin(browser, DEMO_STUDENT.lower(), STUDENT_PASSWORD)
    stu.go("/dashboard/", "Welcome")
    stu1.go("/dashboard/", "Welcome")
    full(stu.page, "student-dashboard", ch4=stu1.page)
    stu1.close()
    stu.close()


def current_codes(page):
    """Four current-semester student codes: low-risk ones, so the demo changes are visible."""
    data = page.evaluate("""async () => {
        const r = await fetch('/api/students?risk=Low', {credentials: 'include'});
        return (await r.json()).students.filter(s => s.level === 'ND1').map(s => s.code);
    }""")
    if len(data) < 4:
        raise RuntimeError("Not enough current ND1 students for the demo upload.")
    return data[:4]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-reset", action="store_true", help="do not reseed before and after")
    parser.add_argument("--skip-api-docs", action="store_true", help="skip /docs (needs the internet)")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    if not args.no_reset:
        reseed()
    server = subprocess.Popen([str(VENV_PY), "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
                              cwd=BACKEND, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    started = time.time()
    try:
        wait_until_up()
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge")
            try:
                capture_all(browser, args.skip_api_docs)
            finally:
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=30)
        (DOCS / "index.json").write_text(json.dumps(INDEX, indent=1), encoding="utf-8")
        if not args.no_reset:
            reseed()
    print(f"Done in {time.time() - started:.0f}s: {len(INDEX)} images")


if __name__ == "__main__":
    sys.exit(main())
