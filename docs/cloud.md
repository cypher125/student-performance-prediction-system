# The system in the cloud

The same code that runs on a Windows computer with `start.bat` also runs online, with **simulated** demonstration data.

| Part | Where | Address |
|---|---|---|
| Web interface | [Vercel](https://vercel.com), project `student-performance-prediction` (team `osawaye-cyrus-projects`) | https://student-performance-prediction-hazel.vercel.app |
| Backend and model | [Modal](https://modal.com), app `student-performance` (workspace `osawayecyrus`) | https://osawayecyrus--student-performance.us-east.modal.run |
| Data | Modal volume `student-performance-data` | the database copy, the model files and the session key |

Sign in at the Vercel address. The web interface there forwards `/api`, `/docs` and `/openapi.json` to Modal, so the browser sees one site and the session cookie stays first-party. The Modal address also works on its own: the backend serves the same pages.

The demonstration accounts are the ones printed on the sign-in page (`admin`, `lecturer`, `adviser`, and every current-semester student's code in small letters, with the passwords shown there). Anyone can use them, so treat the online system as a demonstration: never put real student data in it.

## How it runs

- **One container** (`max_containers=1`), so there is only ever one database. It starts when the first request arrives and stops after 20 minutes without requests, so it costs nothing while idle. The first request after a stop waits about 25 seconds while the container starts and loads the model.
- **The database** is SQLite on the container's own disk. It is copied to the volume every 10 minutes and when the container stops, and a new container restores the latest copy. The very first start creates the simulated demonstration data, as `setup.bat` does.
- **The model files** live on the volume, so a model retrained in the cloud survives restarts; the previous version is kept beside it.
- **The session key** is made on the first start and kept on the volume, never in the repository.
- Settings are in `deploy/modal_app.py` (`SAPPS_*` environment variables, the same names as `backend/.env`).

## Updating, switching off and resetting

From the project folder:

| Task | Command |
|---|---|
| Update the backend after a change | `modal deploy deploy/modal_app.py` |
| Update the web interface after a change | `cd frontend`, then `vercel deploy --prod --scope osawaye-cyrus-projects` |
| Switch the backend off (the data stays in the volume) | `modal app stop student-performance` |
| Start again with fresh demonstration data | `modal app stop student-performance`, then `modal run deploy/modal_app.py::reset_demo`, then `modal deploy deploy/modal_app.py` |

The Vercel project has one environment variable, `SAPPS_API_URL`, set to the Modal address above; `frontend/next.config.ts` refuses to build on Vercel without it. `frontend/vercel.json` tells Vercel the project is a Next.js app.

Resetting is worth doing before a demonstration if visitors have changed the data: anyone signed in as `admin` can change accounts and passwords.

## The public repository

The public GitHub repository, https://github.com/cypher125/student-performance-prediction-system, is published from the private working copy by a script that copies `main`, removes the write-up drafts, the defence brief, the presentation documents and the message to the student from the whole history, checks that no student details are left, and pushes. The same input always gives the same filtered commits, so every later publish is a plain fast-forward push.
