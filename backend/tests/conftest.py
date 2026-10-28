import os
import tempfile
from pathlib import Path

# The API tests use a throwaway database; this must be set before the app is imported.
_TMP = Path(tempfile.mkdtemp(prefix="sapps-test-"))
os.environ["SAPPS_DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["SAPPS_SECRET_KEY"] = "test-secret-key-not-for-production-0123456789"
os.environ["SAPPS_FRONTEND_DIR"] = str(_TMP / "no-frontend")
# Pin the settings the tests depend on, so an edited backend/.env (a new semester, HTTPS cookies)
# cannot make them fail.
os.environ["SAPPS_CURRENT_SESSION"] = "2025/2026"
os.environ["SAPPS_CURRENT_SEMESTER"] = "First"
os.environ["SAPPS_COOKIE_SECURE"] = "false"
