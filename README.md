# AI-Powered Student Academic Performance Prediction System

HND Computer Science project, Yaba College of Technology (YABATECH), Lagos.

**Live demo:** https://student-performance-prediction-hazel.vercel.app (simulated data; the demonstration accounts are listed on the sign-in page). It runs on Modal and Vercel, as described in [docs/cloud.md](docs/cloud.md).

The system predicts each student's performance class (Distinction, Merit, Pass or Fail) **before final examinations**, from attendance, continuous assessment (CA), assignments, previous GPA and level. It explains each prediction with SHAP, flags students at risk of failing, recommends what to do, and keeps a log of interventions. Lecturers, advisers, students and administrators each get their own dashboard.

| Layer | Technology |
|---|---|
| Web interface | Next.js 16 (React, TypeScript, Tailwind CSS, Recharts), built as static pages (or on Vercel, a Next.js app that forwards the API to Modal) |
| Backend API and model | FastAPI (Python) with a scikit-learn Random Forest and SHAP |
| Database | SQLite through SQLAlchemy (PostgreSQL-ready) |

## Quick start (Windows)

1. Install **Python 3.12 or later** from python.org (tick "Add Python to PATH").
2. Double-click **`setup.bat`** once. It installs the packages and creates the demo database.
3. Double-click **`start.bat`**. The system opens at **http://localhost:8000**.

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin@2026` |
| Lecturer | `lecturer` | `Lecturer@2026` |
| Academic adviser | `adviser` | `Adviser@2026` |
| Student | student code in lower case, e.g. `s0379` | `Student@2026` |

All the students and records in the demonstration are **simulated**; every matric number starts with `SIM/`.

The trained model (`backend/artifacts/model.joblib`) and the built interface (`frontend/out`) are included, so the system runs without a training run or Node.js. The full guide is in [docs/user-guide.md](docs/user-guide.md).

## Data

The department's records were not available, so the study uses two datasets ([docs/datasets.md](docs/datasets.md)):

| Dataset | Kind | Used for |
|---|---|---|
| [UCI Student Performance](https://archive.ics.uci.edu/dataset/320/student+performance) (Cortez & Silva, 2008) | Real, public (CC BY 4.0), 649 students | Main evidence for the model's accuracy and the hypothesis tests |
| Simulated YABATECH-format dataset | Simulated, 2,208 student-semester records | Running and demonstrating the system with the exact fields in Table 3.1 |

The simulated dataset must always be described as simulated, never as YABATECH's records.

## Results at a glance

| Test set | UCI (real) | Simulated |
|---|---|---|
| Random Forest accuracy (baseline) | 76.2% (54.6%) | 60.4% (45.0%) |
| ROC-AUC | 0.89 | 0.85 |
| Failing students caught by the alert rule | 85% | 90% |
| H01 / H02 | both rejected (p < 0.05) | both rejected (p < 0.05) |

## Project layout

```
backend/
  app/             FastAPI application: API routes, database models, prediction, alerts, advice
  ml/              data pipeline and model experiments (simulation, cleaning, training, SHAP, tests of H01/H02)
  tools/           Chapter 3 diagrams and Chapter 4 screenshots
  artifacts/       the deployed model and its metadata
  data/            raw UCI files, simulated data, processed datasets, and the SQLite database
  tests/           97 automated tests (pytest)
frontend/
  app/             Next.js pages: login, dashboard, students, records, alerts, reports, model, users, account
  components/      shared UI and charts
  lib/             API client, types, formatting
  out/             the built web interface that FastAPI serves
reports/
  figures/         charts and diagrams for Chapters 3 and 4
  tables/          CSV tables for Chapter 4 (every chart has a table twin)
  screenshots/     screenshots of every screen for Chapter 4
deploy/            the cloud deployment (Modal)
docs/              datasets, user guide, tests, cloud notes (see below)
setup.bat, start.bat
```

## Documents

| File | What it is |
|---|---|
| [docs/datasets.md](docs/datasets.md) | Both datasets, the simulation design and the cleaning steps |
| [docs/user-guide.md](docs/user-guide.md) | Installation and user manual |
| [docs/test-cases.md](docs/test-cases.md) | Unit and system test cases with results |
| [docs/uat-questionnaire.md](docs/uat-questionnaire.md) | User acceptance test questionnaire (Technology Acceptance Model) |
| [docs/cloud.md](docs/cloud.md) | The online deployment on Modal and Vercel |

The write-up drafts (`docs/write-up-updates.md`, `docs/chapter4-5-guide.md`), the defence brief and the four presentation PDFs (`docs/presentation/`) are kept out of the public repository until the project report has been submitted.

## Commands (from `backend`, using `.venv\Scripts\python.exe`)

| Task | Command |
|---|---|
| Rebuild datasets, data tables and figures | `-m ml.prepare_data` |
| Train, tune, evaluate and explain all models (about 40 minutes) | `-m ml.train_models` |
| Reset the demo database | `-m app.seed --reset` |
| Run the system | `-m uvicorn app.main:app --port 8000` |
| Run the tests | `-m pytest` |
| Redraw the Chapter 3 diagrams | `-m tools.diagrams` |
| Start afresh for real records (one admin account, no demo data) | `-m app.seed --reset --empty` |

Every result is reproducible: the random seed is fixed (`SEED = 42` in `backend/ml/config.py`). The interactive API documentation is at http://localhost:8000/docs. Settings are listed in `backend/.env.example`.

The screenshots (`reports/screenshots`) are retaken with `python backend/tools/screenshots.py` from the project folder. It needs Playwright and Microsoft Edge, rebuilds the demo database before and after, and starts its own server on port 8010.
