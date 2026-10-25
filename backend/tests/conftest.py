import os
import tempfile
from pathlib import Path

# The API tests use a throwaway database; this must be set before the app is imported.
_TMP = Path(tempfile.mkdtemp(prefix="sapps-test-"))
os.environ["SAPPS_DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["SAPPS_SECRET_KEY"] = "test-secret-key-not-for-production-0123456789"
os.environ["SAPPS_FRONTEND_DIR"] = str(_TMP / "no-frontend")
