"""The Student Performance Prediction System in the cloud: one Modal container (docs/cloud.md).

    modal deploy deploy/modal_app.py                 start it, or update it after a change (from the project root)
    modal app stop student-performance               switch it off; the data stays in the volume
    modal run deploy/modal_app.py::reset_demo        after stopping: the next start has fresh demonstration data

The container runs the FastAPI application, which also serves the built web pages, so this
address works on its own. The public address is the Vercel project, which forwards /api and /docs
here, so the browser sees one site and the session cookie stays first-party.

The key that signs the session cookies is made on the first start and kept on the volume, never in
this repository. The SQLite database lives on the container's own disk. It is copied to the volume every 10 minutes
and at shutdown, and a new container restores the latest copy; the very first start creates the
simulated demonstration data instead. The model files live on the volume, so a model retrained in
the cloud survives restarts. There is never more than one container (max_containers=1): a second
one would have a second database.
"""
from __future__ import annotations

import os
import secrets
import shutil
import sqlite3
import sys
import threading
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = Path("/app")
BACKEND = APP_DIR / "backend"
STORE = Path("/store")                    # the Modal volume: the database copy and the model files
BACKUP = STORE / "app.db"
MODELS = STORE / "artifacts"
LOCAL_DB = Path("/data/app.db")           # the container's own disk
BACKUP_SECONDS = 600

image = (
    modal.Image.debian_slim(python_version="3.13")
    .pip_install_from_requirements(str(ROOT / "backend" / "requirements.txt"))
    .env({
        "PYTHONUTF8": "1",
        "SAPPS_DATABASE_URL": f"sqlite:///{LOCAL_DB.as_posix()}",
        "SAPPS_MODEL_PATH": (MODELS / "model.joblib").as_posix(),
        "SAPPS_MODEL_META_PATH": (MODELS / "model_meta.json").as_posix(),
        "SAPPS_FRONTEND_DIR": (APP_DIR / "frontend" / "out").as_posix(),
        "SAPPS_COOKIE_SECURE": "true",    # HTTPS only, here and on Vercel
    })
    .add_local_dir(ROOT / "backend", BACKEND.as_posix(),
                   ignore=[".venv", "**/__pycache__", "**/.pytest_cache", ".env", "tests", "tools",
                           "data/app.db*", "data/secret.key", "data/raw"])
    .add_local_dir(ROOT / "frontend" / "out", (APP_DIR / "frontend" / "out").as_posix())
)
volume = modal.Volume.from_name("student-performance-data", create_if_missing=True)
app = modal.App("student-performance", image=image)


def log(message: str) -> None:
    print(f"[student-performance] {message}", flush=True)


def copy_database(source: Path, target: Path) -> None:
    """A consistent copy of a SQLite database, safe while the application is writing to it."""
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial")
    src, dst = sqlite3.connect(source), sqlite3.connect(partial)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    partial.replace(target)


@app.cls(volumes={STORE.as_posix(): volume}, max_containers=1, scaledown_window=1200,
         timeout=600, cpu=1.0, memory=2048)
@modal.concurrent(max_inputs=50)
class Service:
    @modal.enter()
    def boot(self) -> None:
        key = STORE / "secret.key"         # signs the session cookies; set before the app reads its settings
        if not key.exists():
            key.write_text(secrets.token_urlsafe(48))
            volume.commit()
        os.environ["SAPPS_SECRET_KEY"] = key.read_text().strip()
        sys.path.insert(0, BACKEND.as_posix())
        if not (MODELS / "model.joblib").exists():
            shutil.copytree(BACKEND / "artifacts", MODELS, dirs_exist_ok=True)
            volume.commit()
            log("model files copied to the volume")
        LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
        if BACKUP.exists():
            copy_database(BACKUP, LOCAL_DB)
            log("database restored from the volume")
        else:
            from app.db import create_tables
            from app.seed import seed
            create_tables()
            seed()                          # simulated demonstration data, as setup.bat does
            self.backup()
            log("demonstration database created")
        self.stopping = threading.Event()
        threading.Thread(target=self.keep_backing_up, daemon=True).start()

    def backup(self) -> None:
        copy_database(LOCAL_DB, BACKUP)
        volume.commit()

    def keep_backing_up(self) -> None:
        while not self.stopping.wait(BACKUP_SECONDS):
            try:
                self.backup()
            except Exception as error:  # a failed copy is retried at the next interval
                log(f"backup failed: {error}")

    @modal.asgi_app(label="student-performance")
    def web(self):
        from app.main import app as fastapi_app
        return fastapi_app

    @modal.exit()
    def shutdown(self) -> None:
        self.stopping.set()
        self.backup()
        log("database saved to the volume")


@app.function(volumes={STORE.as_posix(): volume})
def reset_demo() -> None:
    """Forget the saved database, so the next start creates fresh demonstration data.

    Stop the app first (modal app stop student-performance): a running container saves its
    database again when it stops. A model retrained in the cloud is kept.
    """
    if BACKUP.exists():
        BACKUP.unlink()
        volume.commit()
        log("saved database removed; the next start creates fresh demonstration data")
    else:
        log("no saved database: the next start creates fresh demonstration data")
