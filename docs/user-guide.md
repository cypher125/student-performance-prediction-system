# User guide

How to install, start and use the Student Performance Prediction System. This guide can serve as the user manual appendix in the project report.

## 1. Requirements

- Windows 10 or 11, a 2 GHz processor and 4 GB RAM or more.
- **Python 3.11 or later** from python.org. During installation, tick "Add Python to PATH".
- A web browser: Chrome, Edge or Firefox.
- An internet connection **only for the first setup**, to download the Python packages. After that the system runs fully offline.
- Node.js is not needed: the web interface comes prebuilt in `frontend/out`.

## 2. Install (once)

1. Copy the project folder to the computer.
2. Double-click **`setup.bat`**. It creates a Python environment, installs the packages, checks the trained model and creates the demo database. On a slow connection this can take a while.

## 3. Start and stop

- Double-click **`start.bat`**. A black window opens; leave it open. After about 15 seconds the browser opens at **http://localhost:8000**.
- To stop the system, close the black window.
- To reset all demo data (users, alerts, interventions), run this from the `backend` folder: `.venv\Scripts\python.exe -m app.seed --reset`.

## 4. Demo accounts

All demo data are **simulated**: the names are fictional and matric numbers start with `SIM/`.

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin@2026` |
| Lecturer | `lecturer` | `Lecturer@2026` |
| Academic adviser | `adviser` | `Adviser@2026` |
| Student | the student code in lower case, e.g. `s0379` | `Student@2026` |

Every student in the current semester (2025/2026, first semester) has an account. Their codes appear on the Students page.

## 5. Using the system: lecturers and advisers

| Page | What it is for |
|---|---|
| **Dashboard** | Numbers of High, Medium and Low risk students; risk by level; predicted classes; the main reasons students are at risk; the latest alerts. |
| **Students** | Every current student, highest risk first, with their attendance, CA, assignments, previous GPA, predicted class, probability of Fail and risk. Use the search box and filters. Click a name to open the profile. **Register student** adds a new student. |
| **Student profile** | The predicted class and the probability of each class; "Why this prediction?" (red bars raise the risk of failing, blue bars lower it); recommendations for the student and the next step for the adviser; GPA trend; every semester record; alerts and interventions. |
| **Records & upload** | **Upload a CSV** of the semester's records (download the template first), or **enter one record** by hand. Records without results are scored straight away, and High or Medium risk raises an alert. **Score current semester** re-scores every current record after the model has been retrained. |
| **Alerts** | Alerts for High and Medium risk students. **Record intervention** describes what was done (for example, "Met the student; agreed a weekly study plan"), then **Save and resolve**. The log appears on the student's profile and in the reports. |
| **Reports** | A summary by level and alert status. **Export predictions (CSV)** opens in Excel; **Print** gives a paper copy. |
| **Model** | The model's test accuracy, the share of failing students it catches, which factors matter most, and how a prediction becomes an alert. |

### CSV upload format

One row per student, with a header row:

| Column | Meaning | Example |
|---|---|---|
| `student_code` (or `matric_number`) | Identifies a registered student | `S0379` |
| `level` | ND1, ND2, HND1 or HND2 | `ND2` |
| `session` | Academic session | `2025/2026` |
| `semester` | First or Second | `First` |
| `attendance_pct` | Average attendance, 0–100 | `82.5` |
| `ca_score` | Average CA score, 0–100 | `61` |
| `assignment_score` | Average assignment score, 0–100 | `70` |
| `prior_gpa` | Previous semester's GPA, 0–4. Optional: it is filled from the last result if blank | `2.75` |
| `exam_score`, `gpa` | Optional. Include only once results are released; the record then becomes history used for retraining | |

Labels such as "nd 1", "1st" or "2025/26" are understood. A row is rejected, with its row number and reason, if the student is not registered, a label is unknown, a value is out of range, or two or more of attendance, CA and assignment score are missing.

## 6. Using the system: students

Sign in with your student code. The **Dashboard** shows your predicted class, your risk level and probability of failing, why (the factors raising or lowering your risk), what to do about it, your current record and your GPA so far. If you have been flagged, a notice says your adviser has been informed. You can only see your own record.

## 7. Using the system: administrators

- **Users:** create accounts (a student account needs the student's code), and disable or enable accounts.
- **Model → Retrain:** retrains the model on every record with released results. It runs in the background for about a minute; when it finishes, the new version and its accuracy are shown. Then use **Score current semester** on the Records page.

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| The browser shows "can't reach this page" | Wait a few more seconds (the model loads at start-up), then refresh. Check that the black window is still open. |
| "Port 8000 is already in use" | Another copy is running. Close it, or restart the computer. |
| "Please sign in" after a while | Sessions last 8 hours; sign in again. |
| The demo data are messy after testing | Reset them (Section 3). |

## 9. For developers

Run these from the `backend` folder with `.venv\Scripts\python.exe`.

| Task | Command |
|---|---|
| Rebuild the datasets, tables and data figures | `-m ml.prepare_data` |
| Retrain and evaluate every model (about 40 minutes) | `-m ml.train_models` |
| Redraw the Chapter 3 diagrams | `-m tools.diagrams` |
| Take the Chapter 4 screenshots (server must be running) | `-m tools.screenshots` |
| Run all automated tests | `-m pytest` |
| Start the API with auto-reload | `-m uvicorn app.main:app --reload` |

The frontend is in `frontend/`. Run `npm install`, then `npm run build`, to rebuild `out/`. For live editing, start the backend, set `NEXT_PUBLIC_API_URL=http://localhost:8000` and run `npm run dev`. The interactive API documentation is at http://localhost:8000/docs.
